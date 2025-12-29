
from odoo import models, fields

class TsDeviceScrapReason(models.Model):
    _name = 'ts.device.scrap.reason'
    _description = 'Device Scrap Reasons'
    _order = 'name'

    name = fields.Char(string='Reason', required=True)
