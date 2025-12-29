from odoo import models, fields

class TsDeviceCategory(models.Model):
    _name = 'ts.device.category'
    _description = 'Technical Device Category'
    _order = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
        index=True
    )

    description = fields.Text(string='Description')

    active = fields.Boolean(default=True)
