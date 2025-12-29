# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SupplyDay(models.Model):
    _name = "custom_supply.supply_day"
    _description = "Supply Day"
    _order = "day_of_week"

    name = fields.Char(required=True)
    day_of_week = fields.Integer(required=True)
    code = fields.Selection([
        ('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'),
        ('thu', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday'), ('sun', 'Sunday'),
    ], required=True)

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Each weekday must be unique.')
    ]

    @api.onchange('code')
    def _onchange_code(self):
        mapping = {'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4,
                   'fri': 5, 'sat': 6, 'sun': 0}
        if self.code:
            self.day_of_week = mapping[self.code]
            self.name = dict(self._fields['code'].selection).get(self.code)