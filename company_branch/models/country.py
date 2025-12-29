# -*- coding: utf-8 -*-
from odoo import models, fields

class BranchCountry(models.Model):
    _name = "custom_supply.country"
    _description = "Branch Country"

    name = fields.Char(string="Country Name", required=True, unique=True)
    city_ids = fields.One2many('custom_supply.city', 'country_id', string="Cities")
