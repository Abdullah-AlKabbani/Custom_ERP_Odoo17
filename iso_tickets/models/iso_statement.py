from odoo import models, fields

class IsoStatement(models.Model):
    _name = "iso.statement"
    _description = "ISO Statement (per section)"

    name = fields.Char(required=True)
    section_id = fields.Many2one("iso.section", required=True, ondelete="cascade")
    needs_quantity = fields.Boolean(default=False, help="If true, public form asks for a numeric quantity.")
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    notes_hint = fields.Char(help="Optional hint shown under notes on the form.")
