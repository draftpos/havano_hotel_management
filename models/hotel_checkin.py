from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelCheckin(models.Model):
    _name = 'hotel.checkin'
    _description = 'Hotel Check-In'

    name = fields.Char('Reference', default='New', readonly=True)
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    room_housekeeping_status = fields.Selection(related='room_id.housekeeping_status')
    guest_id = fields.Many2one('res.partner', string='Guest', required=True)
    check_in_date = fields.Datetime('Check-In Date', required=True, default=fields.Datetime.now)
    check_out_date = fields.Datetime('Expected Check-Out Date', required=True)
    nights = fields.Integer('Nights', default=1, required=True)
    
    total_charge = fields.Float('Total Charge', compute='_compute_charges', store=True)
    amount_paid = fields.Float('Amount Paid', compute='_compute_charges', store=True)
    balance_due = fields.Float('Balance Due', compute='_compute_charges', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    payment_status = fields.Selection([('unpaid', 'Unpaid'), ('paid', 'Paid Now')], string='Payment Status', default='unpaid')
    payment_amount = fields.Float(string='Amount to Pay')
    payment_journal_id = fields.Many2one('account.journal', string='Payment Method', domain="[('type', 'in', ('bank', 'cash'))]")
    payment_reference = fields.Char(string='Payment Reference')
    
    reservation_id = fields.Many2one('hotel.reservation', string='Reservation')
    invoice_id = fields.Many2one('account.move', string='Sales Invoice', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)

    rate_type_id = fields.Many2one('product.pricelist', string='Rate Type')
    rate = fields.Float(string='Rate', required=True, default=0.0)
    allow_overbooking = fields.Boolean(string='Allow Overbooking')
    has_multiple_guests = fields.Boolean(string='Multiple Guests')
    other_guest_ids = fields.One2many('hotel.reservation.guest', 'checkin_id', string='Other Guests')
    
    num_adults = fields.Integer(string='Number of Adults', default=1)
    num_children = fields.Integer(string='Number of Children', default=0)
    guest_vehicle = fields.Char(string='Guest Vehicle')
    transport_mode_id = fields.Many2one('hotel.transport.mode', string='Transport Mode')
    business_source_id = fields.Many2one('hotel.business.source', string='Business Source')
    notes = fields.Text(string='Notes')

    checkout_status = fields.Selection([
        ('in', 'In'),
        ('out', 'Out'),
        ('overdue', 'Overdue')
    ], string='Checkout Status', compute='_compute_checkout_status', store=True)

    @api.onchange('reservation_id')
    def _onchange_reservation_id(self):
        if self.reservation_id:
            self.guest_id = self.reservation_id.guest_id
            self.room_id = self.reservation_id.room_id
            if self.reservation_id.business_source_id:
                self.business_source_id = self.reservation_id.business_source_id
            if self.reservation_id.transport_mode_id:
                self.transport_mode_id = self.reservation_id.transport_mode_id

    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id:
            if self.room_id.price:
                self.rate = self.room_id.price
            
    @api.onchange('check_in_date', 'check_out_date')
    def _onchange_dates(self):
        if self.check_in_date and self.check_out_date:
            delta = self.check_out_date - self.check_in_date
            nights = delta.days
            if nights < 1:
                nights = 1
            self.nights = nights

    @api.onchange('nights')
    def _onchange_nights(self):
        from datetime import timedelta
        if self.check_in_date and self.nights:
            self.check_out_date = self.check_in_date + timedelta(days=self.nights)

    @api.depends('check_out_date', 'state')
    def _compute_checkout_status(self):
        for record in self:
            if record.state == 'checked_out':
                record.checkout_status = 'out'
            elif record.state == 'checked_in':
                if record.check_out_date and record.check_out_date < fields.Datetime.now():
                    record.checkout_status = 'overdue'
                else:
                    record.checkout_status = 'in'
            else:
                record.checkout_status = False

    @api.depends('rate', 'nights', 'num_adults', 'num_children', 'invoice_id.amount_total', 'invoice_id.amount_residual')
    def _compute_charges(self):
        for record in self:
            total_guests = max(1, record.num_adults + record.num_children)
            # Some hotels charge per person, but usually Rate * Nights. Based on blueprint: "Rate x Nights x Total Guests"
            # We will use Rate * Nights, but if they strictly want Total Guests multiplier:
            record.total_charge = record.rate * record.nights * total_guests
            
            if record.invoice_id:
                record.total_charge = record.invoice_id.amount_total
                record.balance_due = record.invoice_id.amount_residual
                record.amount_paid = record.total_charge - record.balance_due
            else:
                record.amount_paid = 0.0
                record.balance_due = record.total_charge

    @api.onchange('payment_status', 'total_charge')
    def _onchange_payment_status(self):
        if self.payment_status == 'paid':
            self.payment_amount = self.total_charge

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.checkin') or 'New'
        return super().create(vals_list)

    def action_checkin(self):
        for record in self:
            if not record.allow_overbooking:
                if record.room_id.status in ['occupied', 'maintenance']:
                    raise ValidationError(f"Room {record.room_id.name} is not available.")
                if record.room_id.housekeeping_status in ['dirty', 'out_of_order']:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': f"Room {record.room_id.name} is Dirty - Clean it first?",
                        'res_model': 'hotel.housekeeping.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_room_id': record.room_id.id,
                            'default_housekeeping_status': 'clean',
                        }
                    }
            
            # Create invoice
            if not record.invoice_id:
                product_id = record.room_id.product_id.id if record.room_id.product_id else False
                if not product_id:
                    # fallback to searching a generic room product
                    product = self.env['product.product'].search([('name', '=', 'Room Stay')], limit=1)
                    if product:
                        product_id = product.id
                
                if product_id:
                    total_guests = max(1, record.num_adults + record.num_children)
                    
                    # 1. Auto Create Sales Order
                    sale_order = self.env['sale.order'].create({
                        'partner_id': record.guest_id.id,
                        'order_line': [(0, 0, {
                            'product_id': product_id,
                            'name': f"Room {record.room_id.name} Stay ({record.nights} nights)",
                            'product_uom_qty': record.nights * total_guests,
                            'price_unit': record.rate,
                        })]
                    })
                    # 2. Confirm Sales Order
                    sale_order.action_confirm()
                    
                    # 3. Create Invoice from Sales Order
                    invoice = sale_order._create_invoices()
                    
                    if hasattr(invoice, 'action_post'):
                        invoice.action_post()
                        record.invoice_id = invoice.id
                    elif sale_order.invoice_ids:
                        sale_order.invoice_ids[0].action_post()
                        record.invoice_id = sale_order.invoice_ids[0].id
                        invoice = sale_order.invoice_ids[0]

                    record.sale_order_id = sale_order.id
                    
                    if record.payment_status == 'paid' and record.payment_journal_id and invoice:
                        payment = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids).create({
                            'amount': record.payment_amount or invoice.amount_total,
                            'journal_id': record.payment_journal_id.id,
                            'payment_date': fields.Date.context_today(self),
                            'communication': record.payment_reference,
                        })
                        payment.action_create_payments()

            # Update Room
            record.room_id.write({
                'status': 'occupied',
                'current_guest_id': record.guest_id.id,
                'current_checkin_id': record.id,
                'checkout_date': record.check_out_date.date() if record.check_out_date else False,
                'checkout_status': 'in'
            })
            record.state = 'checked_in'

    def action_make_payment(self):
        if not self.invoice_id:
            raise ValidationError("No invoice found for this check-in.")
        return {
            'name': 'Register Payment',
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.invoice_id.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_extra_charges(self):
        return {
            'name': 'Extra Charges',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'context': {
                'default_move_type': 'out_invoice',
                'default_partner_id': self.guest_id.id,
                'default_hotel_checkin_id': self.id,
            }
        }

    def action_move_room(self):
        # Placeholder for room move logic
        pass

    def action_extend_stay(self):
        # Open wizard or unlock nights field
        pass

    def action_clean_room(self):
        self.ensure_one()
        if not self.room_id:
            raise ValidationError("Please select a room first.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Housekeeping Status',
            'res_model': 'hotel.housekeeping.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_room_id': self.room_id.id,
                'default_housekeeping_status': self.room_id.housekeeping_status,
            }
        }

    def action_checkout_modal(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Check Out',
            'res_model': 'hotel.checkout',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_checkin_id': self.id,
                'default_guest_id': self.guest_id.id,
                'default_room_id': self.room_id.id,
            }
        }

    def action_checkout(self):
        for record in self:
            if record.balance_due > 0:
                raise ValidationError("Guest has an outstanding balance. Please settle the invoice first.")
            
            # Update Room
            record.room_id.write({
                'status': 'available',
                'housekeeping_status': 'dirty',
                'current_guest_id': False,
                'current_checkin_id': False,
                'checkout_date': False,
                'checkout_status': False
            })
            record.state = 'checked_out'
