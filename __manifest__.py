# -*- coding: utf-8 -*-
{
    'name': "Havano Hotel Management",

    'summary': "Comprehensive Hotel Management System",

    'description': """
        Manage Rooms, Reservations, Check-ins, Check-outs, and more.
    """,

    'author': "Havano",
    'website': "https://www.havano.com",

    'category': 'Operations/Hotel',
    'version': '1.0',

    'depends': ['base', 'web', 'mail', 'account', 'project', 'hr', 'sale_management'],

    'data': [
        'security/ir.model.access.csv',
        'views/hotel_dashboard_views.xml',
        'views/hotel_room_views.xml',
        'views/hotel_checkin_views.xml',
        'views/hotel_shift_views.xml',
        'views/hotel_venue_views.xml',
        'views/hotel_housekeeping_views.xml',
        'views/hotel_booking_views.xml',
        'views/hotel_folio_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'havano_hotel_management/static/src/css/hotel_dashboard.css',
            'havano_hotel_management/static/src/js/hotel_dashboard.js',
            'havano_hotel_management/static/src/xml/hotel_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
}
