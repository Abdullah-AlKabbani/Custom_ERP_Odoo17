# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BranchProduct(models.Model):
    _name = "custom_supply.branch_product"
    _description = "Product Stock in Branch"

    branch_id = fields.Many2one('custom_supply.branch',string="Branch",required=True,ondelete='cascade')
    product_id = fields.Many2one('product.product',string="Product",required=True,ondelete='cascade')
    supply_unit_id = fields.Many2one('custom_supply.unit',related='product_id.product_tmpl_id.supply_unit_id',string="Unit",readonly=True,store=True)
    category_id = fields.Many2one(related='product_id.categ_id',string="Category",store=True,readonly=True)
    min_quantity = fields.Float(string="Minimum Quantity", default=0.0)
    max_quantity = fields.Float(string="Maximum Quantity", default=0.0)
    current_quantity = fields.Float(string="Current Quantity", default=0.0, readonly=True)
    requested_quantity = fields.Float(string="Requested Quantity",compute="_compute_requested_quantity",store=True)
    activate = fields.Boolean(string="Activate in Branch",default=True,help="If unchecked, the product is not active for this branch")
    _sql_constraints = [
        ('unique_branch_product', 'unique(branch_id, product_id)', 'This product is already defined for this branch.')
    ]

    # ==============================
    # COMPUTE FIELDS
    # ==============================
    @api.depends('current_quantity', 'max_quantity')
    def _compute_requested_quantity(self):
        for record in self:
            record.requested_quantity = max(0, (record.max_quantity or 0.0) - (record.current_quantity or 0.0))

    # ==============================
    # Sync Branch Products
    # ==============================
    def manual_sync(self):
        """Multi-safe sync action"""
        result = self.env['custom_supply.branch'].sync_branch_products()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Branch Product Sync',
                'message': result,
                'type': 'success',
                'sticky': False,
            }
        }

    # ==============================
    # CREATE / WRITE
    # ==============================
    @api.model
    def create(self, vals):
        record = super().create(vals)
        return record

    def write(self, vals):
        res = super().write(vals)
        return res
