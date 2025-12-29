from odoo import models, fields

class TsDeviceBrand(models.Model):
    _name = 'ts.device.brand'
    _description = 'Device Brand'
    _order = 'name'

    name = fields.Char(required=True)
    category_id = fields.Many2one(
        'ts.device.category',
        string='Category',
        required=True,
        ondelete='cascade'
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('brand_unique_per_category',
         'unique(name, category_id)',
         'Brand must be unique per category.')
    ]
