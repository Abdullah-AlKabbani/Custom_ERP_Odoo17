from odoo import models, fields, api

class CallCenter(models.Model):
    _name = 'call.center'
    _description = 'Call Center Management'

    name = fields.Char(string='Call Reference', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    salesperson_id = fields.Many2one('hr.employee', string='Salesperson', required=True)
    supervisor_id = fields.Many2one('hr.employee', string='Supervisor', required=True)
    product_ids = fields.Many2many(
        'product.product',
        'call_center_product_rel',
        'call_center_id',
        'product_id',
        string='Products'
    )
    offers = fields.Many2many(
        'product.product',
        'call_center_offer_rel',
        'call_center_id',
        'offer_id',
        string='Offers'
    )
    date = fields.Date(string='Date', default=fields.Date.context_today)
    status = fields.Selection([
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ], string='Status', default='open')
    problem_type = fields.Selection([
        ('wrong_number', 'Wrong Number'),
        ('incomplete_number', 'Incomplete Number'),
        ('closed_workshop', 'Closed Workshop'),
        ('out_of_service', 'Out of Service'),
        ('no_selling', 'No Selling'),
    ], string='Problem Type')
    notes = fields.Text(string='Notes')

    def set_status_open(self):
        self.ensure_one()  # Ensure the method is called on a single record
        self.status = 'open'

    def set_status_pending(self):
        self.ensure_one()  # Ensure the method is called on a single record
        self.status = 'pending'

    def set_status_closed(self):
        self.ensure_one()  # Ensure the method is called on a single record
        self.status = 'closed'
