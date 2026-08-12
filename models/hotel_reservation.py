from odoo import models, fields, api

class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'

    name = fields.Char(string='Reservation Reference', required=True, copy=False, readonly=True, default='New')
    guest_id = fields.Many2one('res.partner', string='Guest', required=True)
    room_id = fields.Many2one('hotel.room', string='Room')
    arrival_date = fields.Datetime(string='Check In Date', required=True, default=fields.Datetime.now)
    departure_date = fields.Datetime(string='Check Out Date', compute='_compute_departure', store=True)
    nights = fields.Integer(string='Nights', required=True, default=1)

    @api.depends('arrival_date', 'nights')
    def _compute_departure(self):
        from datetime import timedelta
        for rec in self:
            if rec.arrival_date and rec.nights:
                rec.departure_date = rec.arrival_date + timedelta(days=rec.nights)
            else:
                rec.departure_date = False
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    balance = fields.Float(string='Balance', default=0.0)
    invoice_id = fields.Many2one('account.move', string='Advance Payment Invoice')
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.reservation') or 'New'
        return super().create(vals_list)

    def action_create_reservation(self):
        for rec in self:
            rec.status = 'confirmed'
        return {'type': 'ir.actions.act_window_close'}
    business_source_id = fields.Many2one('hotel.business.source', string='Business Source')
    transport_mode_id = fields.Many2one('hotel.transport.mode', string='Transport Mode')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    project_id = fields.Many2one('project.project', string='Project')
    cost_center_id = fields.Many2one('account.analytic.account', string='Cost Center')
    venue_id = fields.Many2one('hotel.venue', string='Venue')
    guest_ids = fields.One2many('hotel.reservation.guest', 'reservation_id', string='Reservation Guests')

class HotelReservationGuest(models.Model):
    _name = 'hotel.reservation.guest'
    _description = 'Reservation Guest Child Table'

    reservation_id = fields.Many2one('hotel.reservation', string='Reservation')
    checkin_id = fields.Many2one('hotel.checkin', string='Check In')
    guest_id = fields.Many2one('res.partner', string='Guest')
    room_id = fields.Many2one('hotel.room', string='Room')
    check_in_datetime = fields.Datetime(string='Check In Date/Time')
    check_out_datetime = fields.Datetime(string='Check Out Date/Time')
    nights = fields.Integer(string='Nights')
    guest_note = fields.Text(string='Guest Note')
    to_be_billed = fields.Boolean(string='To be billed', default=True)
