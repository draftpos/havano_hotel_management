from odoo import models, fields

class HotelRoomFolio(models.Model):
    _name = 'hotel.room.folio'
    _description = 'Room Folio'

    name = fields.Char(string='Folio Reference', required=True, copy=False, default='New')
    guest_id = fields.Many2one('res.partner', string='Guest')
    room_id = fields.Many2one('hotel.room', string='Room')
    desk_folio_id = fields.Many2one('hotel.desk.folio', string='Desk Folio')
    transaction_ids = fields.One2many('hotel.folio.transaction', 'room_folio_id', string='Transactions')
    
class HotelDeskFolio(models.Model):
    _name = 'hotel.desk.folio'
    _description = 'Desk Folio'

    name = fields.Char(string='Desk Folio Reference', required=True, copy=False, default='New')
    reservation_id = fields.Many2one('hotel.reservation', string='Reservation')
    guest_id = fields.Many2one('res.partner', string='Guest')
    payment_entry_ids = fields.One2many('hotel.payment.entry', 'desk_folio_id', string='Payment Transactions')

class HotelFolioTransaction(models.Model):
    _name = 'hotel.folio.transaction'
    _description = 'Folio Transaction'

    room_folio_id = fields.Many2one('hotel.room.folio', string='Room Folio')
    name = fields.Char(string='Description', required=True)
    amount = fields.Float(string='Amount')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    income_account_id = fields.Many2one('account.account', string='Income Account')
    cost_center_id = fields.Many2one('account.analytic.account', string='Cost Center')

class HotelPaymentEntry(models.Model):
    _name = 'hotel.payment.entry'
    _description = 'Hotel Payment Entry Child'

    desk_folio_id = fields.Many2one('hotel.desk.folio', string='Desk Folio')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    account_paid_from = fields.Many2one('account.account', string='Account Paid From')
    currency_from = fields.Many2one('res.currency', string='Account Currency (From)')
    account_paid_to = fields.Many2one('account.account', string='Account Paid To')
    currency_to = fields.Many2one('res.currency', string='Account Currency (To)')
    amount = fields.Float(string='Amount')

class HotelPayments(models.Model):
    _name = 'hotel.payments'
    _description = 'Hotel Payments'

    invoice_id = fields.Many2one('account.move', string='Sales Invoice')
    payment_entry_id = fields.Many2one('account.payment', string='Payment Entry')
    amount = fields.Float(string='Amount')
    payment_date = fields.Date(string='Payment Date')

class HotelSalesInvoices(models.Model):
    _name = 'hotel.sales.invoices'
    _description = 'Hotel Sales Invoices'

    room_id = fields.Many2one('hotel.room', string='Room')
    invoice_id = fields.Many2one('account.move', string='Sales Invoice')
    amount = fields.Float(string='Amount')
    date = fields.Date(string='Date')
    status = fields.Selection(related='invoice_id.state', string='Status', readonly=True)
