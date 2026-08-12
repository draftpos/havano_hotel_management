from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelShift(models.Model):
    _name = 'hotel.shift'
    _description = 'Hotel POS Shift'
    _order = 'start_time desc'

    name = fields.Char(string='Shift Reference', required=True, copy=False, readonly=True, default='New')
    user_id = fields.Many2one('res.users', string='Cashier', default=lambda self: self.env.user, required=True)
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now, required=True)
    end_time = fields.Datetime(string='End Time')
    opening_cash = fields.Float(string='Opening Cash', required=True)
    closing_cash = fields.Float(string='Closing Cash')
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed')
    ], string='Status', default='open', required=True)
    shift_user_ids = fields.One2many('hotel.shift.user', 'shift_id', string='Shift Users')
    revenue_ids = fields.One2many('hotel.shift.revenue', 'shift_id', string='Revenue by Center')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.shift') or 'New'
        return super().create(vals_list)

    def action_close_shift(self):
        for record in self:
            if record.state == 'closed':
                raise ValidationError("Shift is already closed.")
            record.write({
                'state': 'closed',
                'end_time': fields.Datetime.now()
            })

class HotelShiftWizard(models.TransientModel):
    _name = 'hotel.shift.wizard'
    _description = 'Start Shift Wizard'

    opening_cash = fields.Float(string='Opening Cash', required=True, default=0.0)
    has_open_shift = fields.Boolean(string='Has Open Shift')
    open_shift_id = fields.Many2one('hotel.shift', string='Open Shift')
    open_shift_name = fields.Char(string='Open Shift Name')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        existing_shift = self.env['hotel.shift'].search([
            ('user_id', '=', self.env.user.id),
            ('state', '=', 'open')
        ], limit=1)
        if existing_shift:
            res['has_open_shift'] = True
            res['open_shift_id'] = existing_shift.id
            res['open_shift_name'] = existing_shift.name
        else:
            res['has_open_shift'] = False
        return res

    def action_start_shift(self):
        if self.has_open_shift:
            raise ValidationError("You already have an open shift!")
            
        shift = self.env['hotel.shift'].create({
            'opening_cash': self.opening_cash
        })
        
        # Return action to open POS or reload dashboard
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_go_to_close_shift(self):
        if not self.open_shift_id:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Close Shift',
            'res_model': 'hotel.shift.close.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.open_shift_id.id},
        }

class HotelShiftCloseWizard(models.TransientModel):
    _name = 'hotel.shift.close.wizard'
    _description = 'Close Shift Wizard'

    shift_id = fields.Many2one('hotel.shift', string='Shift', required=True)
    expected_cash = fields.Float(string='Expected Cash', readonly=True)
    closing_cash = fields.Float(string='Actual Closing Cash', required=True, default=0.0)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        shift_id = self.env.context.get('active_id')
        if shift_id:
            shift = self.env['hotel.shift'].browse(shift_id)
            res['shift_id'] = shift.id
            res['expected_cash'] = shift.opening_cash # Logic to add sales can be done here later
        return res

    def action_close_shift(self):
        self.shift_id.write({
            'closing_cash': self.closing_cash,
            'state': 'closed',
            'end_time': fields.Datetime.now()
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}

class HotelShiftUser(models.Model):
    _name = 'hotel.shift.user'
    _description = 'Hotel Shift User'

    shift_id = fields.Many2one('hotel.shift', string='Shift')
    user_id = fields.Many2one('res.users', string='User')
    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    total_revenue = fields.Float(string='Total Revenue')

class HotelShiftRevenue(models.Model):
    _name = 'hotel.shift.revenue'
    _description = 'Hotel Shift Revenue by Center'

    shift_id = fields.Many2one('hotel.shift', string='Shift')
    cost_center_id = fields.Many2one('account.analytic.account', string='Cost Center')
    item_group_id = fields.Many2one('product.category', string='Item Group')
    revenue_amount = fields.Float(string='Revenue Amount')

