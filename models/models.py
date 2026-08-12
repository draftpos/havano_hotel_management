# from odoo import models, fields, api


# class havano_hotel_management(models.Model):
#     _name = 'havano_hotel_management.havano_hotel_management'
#     _description = 'havano_hotel_management.havano_hotel_management'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

