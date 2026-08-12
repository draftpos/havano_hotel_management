from odoo import models, fields

class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'Hotel Room Type'

    name = fields.Char('Room Type Name', required=True)
    description = fields.Text('Description')

class HotelFloor(models.Model):
    _name = 'hotel.floor'
    _description = 'Hotel Floor'

    name = fields.Char('Floor Name', required=True)

class HotelRoomAmenity(models.Model):
    _name = 'hotel.room.amenity'
    _description = 'Hotel Room Amenity'

    name = fields.Char('Amenity Name', required=True)
    description = fields.Text('Description')

class SeasonType(models.Model):
    _name = 'hotel.season.type'
    _description = 'Season Type'

    name = fields.Char(string='Season Name', required=True)

class BusinessSource(models.Model):
    _name = 'hotel.business.source'
    _description = 'Business Source'

    name = fields.Char(string='Source Name', required=True)

class TransportMode(models.Model):
    _name = 'hotel.transport.mode'
    _description = 'Transport Mode'

    name = fields.Char(string='Mode Name', required=True)

class HotelSettings(models.TransientModel):
    _name = 'hotel.settings'
    _inherit = 'res.config.settings'
    _description = 'Hotel Settings'

    hotel_customer_group_id = fields.Many2one('res.partner.category', string='Hotel Customer Group')
    hotel_item_group_id = fields.Many2one('product.category', string='Hotel Item Group')
