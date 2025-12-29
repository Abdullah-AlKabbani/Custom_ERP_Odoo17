from odoo import models, fields

class TsDeviceModel(models.Model):
    _name = 'ts.device.model'
    _description = 'Device Model'
    _order = 'name'

    name = fields.Char(required=True)
    brand_id = fields.Many2one(
        'ts.device.brand',
        string='Brand',
        required=True,
        ondelete='cascade'
    )
    category_id = fields.Many2one(
        related='brand_id.category_id',
        store=True,
        readonly=True
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('model_unique_per_brand',
         'unique(name, brand_id)',
         'Model must be unique per brand.')
    ]
