# -*- coding: utf-8 -*-
from odoo import models, fields

class IsoConfig(models.TransientModel):
    _name = "iso.config"
    _inherit = "res.config.settings"
    _description = "ISO Tickets Configuration (module-local)"

    # Only setting we keep: default shift for the *public* form
    iso_default_shift_id = fields.Many2one(
        "iso.shift",
        string="Default Shift",
        config_parameter="iso_tickets.default_shift_id",
    )
