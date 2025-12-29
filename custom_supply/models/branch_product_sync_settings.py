# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BranchProductSyncSettings(models.TransientModel):
    _name = "custom_supply.branch_product_sync_settings"
    _description = "Branch Product Sync Settings"

    auto_sync = fields.Boolean(
        string="Enable Automatic Sync",
        default=True
    )

    branch_ids = fields.Many2many(
        'custom_supply.branch',
        'branch_sync_settings_rel',  # اسم جدول قصير
        'settings_id',
        'branch_id',
        string="Branches",
        help="Select branches to sync (leave empty for all)"
    )

    product_ids = fields.Many2many(
        'product.product',
        'product_sync_settings_rel',
        'settings_id',
        'product_id',
        string="Products",
        help="Select products to sync (leave empty for all)"
    )

    @api.model
    def get_auto_sync(self):
        setting = self.search([], limit=1)
        return setting.auto_sync if setting else True

    def manual_sync(self):
        """Manual sync for selected branches and/or products"""
        branches = self.branch_ids if self.branch_ids else None
        products = self.product_ids if self.product_ids else None

        # نمرر فقط الفروع، المنتجات يتم فلترتها داخل التابع
        created_count = 0
        if branches:
            for branch in branches:
                created_count += self.env['custom_supply.branch'].sync_branch_products(branches=branch)
        else:
            created_count = self.env['custom_supply.branch'].sync_branch_products()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Branch Product Sync',
                'message': f"{created_count} branch-product records created/updated.",
                'type': 'success',
            }
        }
