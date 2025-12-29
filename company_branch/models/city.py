# -*- coding: utf-8 -*-
from odoo import models, fields

class BranchCity(models.Model):
    _name = "custom_supply.city"
    _description = "Branch City"

    name = fields.Char(string="City Name", required=True)
    country_id = fields.Many2one('custom_supply.country', string="Country", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This city already exists!')
    ]
