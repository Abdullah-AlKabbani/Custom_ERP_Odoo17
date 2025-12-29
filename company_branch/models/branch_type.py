from odoo import models, fields

class BranchType(models.Model):
    _name = 'custom_supply.branch.type'
    _description = 'Branch Type'
    _order = 'sequence, name'

    name = fields.Char(string="Branch Type", required=True, translate=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description")

    is_operational = fields.Boolean(string="Operational Branch", default=True)
    has_sales = fields.Boolean(string="Has Sales", default=False)
    has_stock = fields.Boolean(string="Has Stock", default=False)

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
