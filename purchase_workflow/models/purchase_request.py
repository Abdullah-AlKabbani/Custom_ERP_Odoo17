from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError

class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='PR Number', required=True, readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string='Requested By', required=True, default=lambda self: self.env.user.employee_id)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    note = fields.Text(string='Notes')
    document = fields.Binary(string="Attachment")
    offer_ids = fields.One2many('purchase.offer', 'request_id', string='Offers')
    selected_offer_id = fields.Many2one('purchase.offer', string='Selected Offer')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages', domain=[('model', '=', 'purchase.request')])
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', domain=[('res_model', '=', 'purchase.request')])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager_approval', 'Manager Approval'),
        ('category_approval', 'Department Approval'),
        ('purchase_approval', 'Purchase Approval'),
        ('finance_approval', 'Finance Approval'),
        ('gm_approval', 'GM Approval'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or 'New'
        return super().create(vals)

    def action_submit(self):
        self.state = 'manager_approval'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_manager_approve(self):
        if not self.env.user.has_group('base.group_user'):
            raise AccessError("Only a manager can approve.")
        self.state = 'category_approval'

    def action_category_approve(self):
        self.state = 'purchase_approval'

    def action_purchase_approve(self):
        if not self.selected_offer_id:
            raise UserError("Please select an offer before proceeding.")
        self.state = 'finance_approval'

    def action_finance_approve(self):
        self.state = 'gm_approval'

    def action_gm_approve(self):
        self.state = 'done'
        self.env['purchase.order'].create({
            'partner_id': self.selected_offer_id.vendor_id.id,
            'order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'name': self.product_id.name,
                'product_qty': self.quantity,
                'price_unit': self.selected_offer_id.price,
                'date_planned': fields.Date.today(),
            })],
            'notes': self.note,
        })
