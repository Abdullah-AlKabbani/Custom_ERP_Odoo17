from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'  # The name of the model to inherit

    property_id = fields.Many2one('property', string='Property')

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        # Additional logic can be added here if needed
        print("inside action confirm")
        return res
