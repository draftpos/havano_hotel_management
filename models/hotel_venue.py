from odoo import models, fields

class HotelVenue(models.Model):
    _name = 'hotel.venue'
    _description = 'Hotel Venue'

    name = fields.Char(string='Venue Name', required=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('maintenance', 'Under Maintenance')
    ], string='Status', default='available')
    price = fields.Float(string='Price')
    housekeeping_status = fields.Selection([
        ('clean', 'Clean'),
        ('dirty', 'Dirty')
    ], string='Housekeeping Status', default='clean')
    venue_item_id = fields.Many2one('product.product', string='Venue Item')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    cost_center_id = fields.Many2one('account.analytic.account', string='Cost Center')
    rate_type_id = fields.Many2one('product.pricelist', string='Rate Type')
    
    current_guest_id = fields.Many2one('res.partner', string='Current Guest')
    # current_booking_id is added in hotel_booking.py via inheritance or relation
