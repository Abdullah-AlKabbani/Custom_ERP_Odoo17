from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    iso_enable_public = fields.Boolean(
        string="Enable ISO Public Form",
        config_parameter="iso_tickets.enable_public",
    )
    iso_default_shift_id = fields.Many2one(
        "iso.shift",
        string="Default Shift",
        config_parameter="iso_tickets.default_shift_id",
    )
