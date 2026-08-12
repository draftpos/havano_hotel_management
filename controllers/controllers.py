# from odoo import http


# class HavanoHotelManagement(http.Controller):
#     @http.route('/havano_hotel_management/havano_hotel_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/havano_hotel_management/havano_hotel_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('havano_hotel_management.listing', {
#             'root': '/havano_hotel_management/havano_hotel_management',
#             'objects': http.request.env['havano_hotel_management.havano_hotel_management'].search([]),
#         })

#     @http.route('/havano_hotel_management/havano_hotel_management/objects/<model("havano_hotel_management.havano_hotel_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('havano_hotel_management.object', {
#             'object': obj
#         })

