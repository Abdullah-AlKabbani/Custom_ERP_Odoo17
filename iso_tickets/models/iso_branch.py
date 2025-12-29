from odoo import models, fields

class IsoBranch(models.Model):
    _name = "iso.branch"
    _description = "ISO Branch"

    name = fields.Char(required=True)
    location = fields.Char()
    manager_name = fields.Char(help="Default manager name shown on the public form (optional).")
    