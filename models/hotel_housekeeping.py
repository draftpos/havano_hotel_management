from odoo import models, fields

class HotelHousekeeping(models.Model):
    _name = 'hotel.housekeeping'
    _description = 'Hotel Housekeeping'

    name = fields.Char(string='Task Name', required=True, copy=False, default='New')
    room_id = fields.Many2one('hotel.room', string='Room')
    assigned_staff_id = fields.Many2one('hr.employee', string='Assigned Staff')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Status', default='pending')
    date = fields.Date(string='Date', default=fields.Date.context_today)
