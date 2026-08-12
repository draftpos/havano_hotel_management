from odoo import models, fields, api

class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = 'Hotel Booking'

    name = fields.Char(string='Booking Reference', required=True, copy=False, default='New')
    reservation_id = fields.Many2one('hotel.reservation', string='Reservation')
    guest_id = fields.Many2one('res.partner', string='Customer Name', required=True)
    check_in_by = fields.Many2one('res.users', string='Check In By')
    invoice_id = fields.Many2one('account.move', string='Sales Invoice Number')
    amended_from_id = fields.Many2one('hotel.booking', string='Amended From')
    payment_entry_id = fields.Many2one('account.payment', string='Payment Entry')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    rate_type_id = fields.Many2one('product.pricelist', string='Rate Type')
    venue_id = fields.Many2one('hotel.venue', string='Venue')
    project_id = fields.Many2one('project.project', string='Project')

class HotelCheckOut(models.Model):
    _name = 'hotel.checkout'
    _description = 'Hotel Check Out'

    name = fields.Char(string='Check Out Reference', required=True, copy=False, default='New')
    checkin_id = fields.Many2one('hotel.checkin', string='Check In', required=True)
    guest_id = fields.Many2one('res.partner', string='Guest')
    room_id = fields.Many2one('hotel.room', string='Room')
    room_folio_id = fields.Many2one('hotel.room.folio', string='Room Folio')
    payment_method_id = fields.Many2one('account.journal', string='Payment Method')
    checkout_by = fields.Many2one('res.users', string='Check Out By')
    amended_from_id = fields.Many2one('hotel.checkout', string='Amended From')
    payment_entry_id = fields.Many2one('account.payment', string='Payment Entry')
    invoice_id = fields.Many2one('account.move', string='Sales Invoice Number')

    actual_checkout_time = fields.Datetime(string='Actual Check Out Time', required=True, default=fields.Datetime.now)
    housekeeping_status = fields.Selection([
        ('dirty', 'Dirty'),
        ('clean', 'Clean')
    ], string='House Keeping Status', required=True, default='dirty')

    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            # Find active check-in for this room
            active_checkin = self.env['hotel.checkin'].search([
                ('room_id', '=', self.room_id.id),
                ('state', '=', 'checked_in')
            ], limit=1)
            if active_checkin:
                self.checkin_id = active_checkin.id
                self.guest_id = active_checkin.guest_id.id
                self.invoice_id = active_checkin.invoice_id.id
            else:
                self.checkin_id = False
                self.guest_id = False
                self.invoice_id = False
                return {'warning': {'title': "Invalid Room", 'message': "This room does not have an active check-in!"}}

    def action_checkout(self):
        for rec in self:
            if rec.checkin_id:
                rec.checkin_id.state = 'checked_out'
                rec.checkin_id.checkout_status = 'out'
            if rec.room_id:
                rec.room_id.housekeeping_status = rec.housekeeping_status
                rec.room_id.status = 'available'
                rec.room_id.current_guest_id = False
                rec.room_id.current_checkin_id = False
        return {'type': 'ir.actions.act_window_close'}

class HotelPaymentWizard(models.TransientModel):
    _name = 'hotel.payment.wizard'
    _description = 'Make Payment'

    room_id = fields.Many2one('hotel.room', string='Room')
    checkin_id = fields.Many2one('hotel.checkin', string='Check In')
    guest_id = fields.Many2one('res.partner', string='Customer')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    
    total_amount = fields.Float(string='Total Amount', readonly=True)
    amount = fields.Float(string='Payment Amount', required=True)
    payment_method_id = fields.Many2one('account.journal', string='Mode of Payment', required=True, domain=[('type', 'in', ('bank', 'cash'))], default=lambda self: self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1))
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.context_today)
    reference_no = fields.Char(string='Reference No')
    reference_date = fields.Date(string='Reference Date')
    remarks = fields.Text(string='Remarks')

    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            active_checkin = self.env['hotel.checkin'].search([
                ('room_id', '=', self.room_id.id),
                ('state', '=', 'checked_in')
            ], limit=1)
            if active_checkin:
                self.checkin_id = active_checkin.id
                self.guest_id = active_checkin.guest_id.id
                self.total_amount = active_checkin.total_charge
                self.amount = active_checkin.balance_due
                if active_checkin.invoice_id:
                    self.invoice_id = active_checkin.invoice_id.id
            else:
                self.checkin_id = False
                self.guest_id = False
                self.invoice_id = False
                self.total_amount = 0.0
                self.amount = 0.0

    def action_make_payment(self):
        if self.invoice_id and self.amount > 0:
            payment = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=self.invoice_id.ids).create({
                'amount': self.amount,
                'journal_id': self.payment_method_id.id,
                'payment_date': self.payment_date,
            })
            payment.action_create_payments()
            if self.remarks:
                self.invoice_id.message_post(body=self.remarks)
        return {'type': 'ir.actions.act_window_close'}
