# -*- coding: utf-8 -*-
import logging
import random

from odoo import models, fields, api
from datetime import timedelta
_logger = logging.getLogger(__name__)

class BranchNotificationSettings(models.Model):
    _name = "custom_supply.branch_notification_settings"
    _description = "Branch Notification Settings"

    active = fields.Boolean(string="Enable Weekly Branch Notifications", default=True)

    @api.model
    def get_active(self):
        setting = self.search([], limit=1)
        return setting.active if setting else False

class BranchNotification(models.Model):
    _name = "custom_supply.branch_notification"
    _description = "Branch Weekly Notification"

    @api.model
    def send_weekly_notifications(self, force_send=False):
        settings_active = self.env['custom_supply.branch_notification_settings'].get_active()
        if not settings_active and not force_send:
            return

        today = fields.Date.context_today(self)
        tomorrow = today + timedelta(days=1)
        tomorrow_weekday = tomorrow.weekday()

        # الفروع التي يجب توريدها غداً
        branches_tomorrow = self.env['custom_supply.branch'].search([]).filtered(
            lambda b: tomorrow_weekday in b.windows_ids.mapped('supply_day_id.day_of_week')
        )

        for branch in branches_tomorrow:
            # شركاء المستلمين
            partners = self.env.ref('custom_supply.group_supply_manager').users.mapped('partner_id')
            if branch.user_id and branch.user_id.partner_id:
                partners |= branch.user_id.partner_id

            if not partners:
                continue

            self.env['mail.message'].create({
                'subject': f'تذكير توريد الفرع غداً: {branch.name}',
                'body': (
                    f'⚠️ تذكير !!\n'
                    f'يجب أن يتم توريد الفرع "{branch.name}" غداً بين '
                    f'{int(branch.supply_time_from):02d}:{int((branch.supply_time_from%1*60)):02d} و '
                    f'{int(branch.supply_time_to):02d}:{int((branch.supply_time_to%1*60)):02d}.'
                ),
                'message_type': 'notification',
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'partner_ids': [(6, 0, partners.ids)]
            })

class SupplyBranch(models.Model):
    _inherit = "custom_supply.branch"

    product_ids = fields.One2many('custom_supply.branch_product','branch_id',string="Products in Branch")
    search_product = fields.Char(string="Search Product",help="Filter products by name or category",store=False,)

    # ==============================
    # Sync Branch Products
    # ==============================
    @api.model
    def sync_branch_products(self, branches=None):
        Settings = self.env['custom_supply.branch_product_sync_settings']
        if not Settings.get_auto_sync():
            return 0

        BranchProduct = self.env['custom_supply.branch_product']
        Product = self.env['product.product']

        branches = branches or self.search([])

        # ✅ المنتجات المسموح بها للتوريد
        supply_products = Product.search([
            ('product_tmpl_id.product_for_supply', '=', True)
        ])

        supply_product_ids = set(supply_products.ids)

        created_count = 0
        deactivated_count = 0

        for branch in branches:
            branch_products = BranchProduct.search([
                ('branch_id', '=', branch.id)
            ])

            existing_product_ids = set(branch_products.mapped('product_id').ids)

            # ======================
            # ➕ إضافة المنتجات الناقصة
            # ======================
            for product in supply_products:
                if product.id not in existing_product_ids:
                    BranchProduct.create({
                        'branch_id': branch.id,
                        'product_id': product.id,
                        'min_quantity': 0.0,
                        'max_quantity': 0.0,
                        'current_quantity': 0.0,
                        'activate': True,
                    })
                    created_count += 1

            # ======================
            # ➖ تعطيل المنتجات غير المسموح بها
            # ======================
            to_deactivate = branch_products.filtered(
                lambda bp: bp.product_id.id not in supply_product_ids
            )

            if to_deactivate:
                to_deactivate.write({'activate': False})
                deactivated_count += len(to_deactivate)

        _logger.info(
            "Branch product sync done: %s created, %s deactivated",
            created_count,
            deactivated_count
        )

        return created_count

    # ==============================
    # Search Filed
    # ==============================
    def clear_search(self):
        """
        مسح حقل البحث ثم إعادة تحميل واجهة المستخدم لكي يُعاد تطبيق domain على one2many.
        يتم استدعاء هذا الميثود من زر type="object" في الـ XML.
        """
        for rec in self:
            rec.search_product = False
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    # ==============================
    # COMPUTE FIELDS
    # ==============================
    @api.depends('product_ids.write_date')
    def _compute_last_updated(self):
        for branch in self:
            dates = branch.product_ids.mapped('write_date')
            branch.last_updated = max(dates) if dates else False