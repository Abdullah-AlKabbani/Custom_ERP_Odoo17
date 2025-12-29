from odoo import models, fields

class SupplyDelayLog(models.Model):
    _name = "custom_supply.delay_log"
    _description = "Supply Delay Log"
    _order = "create_date desc"

    request_id = fields.Many2one("custom_supply.request", string="Supply Request", required=True)
    delay_type = fields.Selection([
        ('supply', 'Supply Delay'),
        ('warehouse', 'Warehouse Delay'),
    ], string="Delay Type", required=True)
    notes = fields.Char(string="Notes")
    delay_minutes = fields.Integer(string="Delay Minutes", required=True)
