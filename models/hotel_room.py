from odoo import models, fields, api

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'

    name = fields.Char(string='Room Number', required=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved')
    ], string='Status', default='available')
    
    housekeeping_status = fields.Selection([
        ('clean', 'Clean'),
        ('dirty', 'Dirty'),
        ('out_of_order', 'Out of Order')
    ], string='Housekeeping Status', default='clean')
    
    price = fields.Float(related='product_id.list_price', string='Rate', store=True, readonly=False)
    checkout_date = fields.Date(string='Checkout Date')
    checkout_status = fields.Selection([
        ('in', 'In'),
        ('overdue', 'Overdue')
    ], string='Checkout Status')

    # Relationships
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type')
    floor_id = fields.Many2one('hotel.floor', string='Floor')
    current_guest_id = fields.Many2one('res.partner', string='Current Guest')
    current_checkin_id = fields.Many2one('hotel.checkin', string='Current Check-In')
    product_id = fields.Many2one('product.product', string='Linked Item (Billing)')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    amenity_ids = fields.Many2many('hotel.room.amenity', string='Room Amenities')

    # Backward compatibility / existing logic support
    current_reservation_id = fields.Many2one('hotel.reservation', string='Current Reservation', compute='_compute_current_reservation', store=False)
    guest_name = fields.Char(related='current_guest_id.name', string='Guest Name', readonly=True)
    
    def _compute_current_reservation(self):
        for room in self:
            reservation = self.env['hotel.reservation'].search([
                ('room_id', '=', room.id),
                ('status', 'in', ['confirmed', 'checked_in'])
            ], limit=1)
            room.current_reservation_id = reservation.id if reservation else False

    @api.model
    def get_dashboard_data(self):
        rooms = self.search_read([], ['id', 'name', 'room_type_id', 'status', 'housekeeping_status', 'guest_name', 'checkout_date', 'current_guest_id', 'current_checkin_id'])
        
        for room in rooms:
            room['balance'] = 0.00
            room['arrival_date'] = '-'
            if room.get('current_checkin_id'):
                checkin = self.env['hotel.checkin'].browse(room['current_checkin_id'][0])
                if checkin.exists():
                    room['balance'] = "{:.2f}".format(checkin.balance_due)
                    if checkin.check_in_date:
                        room['arrival_date'] = checkin.check_in_date.strftime('%Y-%m-%d')
        
        stats = {
            'vacant': self.search_count([('status', '=', 'available')]),
            'occupied': self.search_count([('status', '=', 'occupied')]),
            'reserved': self.search_count([('status', '=', 'reserved')]),
            'dirty': self.search_count([('housekeeping_status', '=', 'dirty')]),
            'out_of_order': self.search_count([('housekeeping_status', '=', 'out_of_order')]),
            'all_rooms': len(rooms),
        }
        
        room_types = self.env['hotel.room.type'].search_read([], ['id', 'name'])
        floors = self.env['hotel.floor'].search_read([], ['id', 'name'])
        has_active_shift = self.env['hotel.shift'].search_count([('state', '=', 'open')]) > 0

        return {
            'stats': stats,
            'rooms': rooms,
            'room_types': room_types,
            'floors': floors,
            'has_active_shift': has_active_shift,
        }

    def action_print_receipt(self):
        self.ensure_one()
        active_checkin = self.env['hotel.checkin'].search([
            ('room_id', '=', self.id),
            ('state', 'in', ['checked_in', 'checked_out'])
        ], order='id desc', limit=1)
        
        if active_checkin and active_checkin.invoice_id:
            return self.env.ref('account.account_invoices').report_action(active_checkin.invoice_id)
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Receipt Found',
                    'message': 'There is no active invoice for this room to print.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

class HotelHousekeepingWizard(models.TransientModel):
    _name = 'hotel.housekeeping.wizard'
    _description = 'Update Housekeeping Status'

    room_id = fields.Many2one('hotel.room', string='Room', required=True, readonly=True)
    housekeeping_status = fields.Selection([
        ('clean', 'Clean'),
        ('dirty', 'Dirty'),
        ('out_of_order', 'Out of Order')
    ], string='House Keeping Status', required=True)

    def action_update(self):
        self.ensure_one()
        if self.room_id:
            self.room_id.housekeeping_status = self.housekeeping_status
        return {'type': 'ir.actions.act_window_close'}
