from odoo import models, fields

class IsoSection(models.Model):
    _name = "iso.section"
    _description = "ISO Section (fixed)"

    name = fields.Char(required=True)
    code = fields.Selection([
        ("supply","Supply"),
        ("quality","Quality"),
        ("maintenance","Maintenance"),
        ("sales","Sales"),
        ("tech","Tech"),
        ("hr","HR"),
        ("finance","Finance"),
    ], required=True)

    _sql_constraints = [
        ("iso_section_code_uniq", "unique(code)", "Section code must be unique."),
    ]
