from odoo import models, fields

class IsoShift(models.Model):
    _name = "iso.shift"
    _description = "ISO Shift"

    name = fields.Char(required=True)
    start_hour = fields.Char()
    end_hour = fields.Char()
    active = fields.Boolean(default=True)
