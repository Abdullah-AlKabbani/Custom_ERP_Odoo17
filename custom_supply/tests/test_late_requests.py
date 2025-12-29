# -*- coding: utf-8 -*-
import unittest
from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo import fields

class TestSupplyRequestLateNotifications(TransactionCase):

    def setUp(self):
        super().setUp()

        # ======================
        # Users
        # ======================
        self.branch_manager = self.env['res.users'].search([('login', '=', 'artouz_branch@odoo.com')], limit=1)
        self.supply_manager = self.env['res.users'].search([('login', '=', 'supply_mgr1@example.com')], limit=1)
        self.warehouse_user = self.env['res.users'].search([('login', '=', 'warehousemanager1@gmail.com')], limit=1)

        # ======================
        # Branch
        # ======================
        self.branch = self.branch_manager.branch_id or self.env['custom_supply.branch'].search([], limit=1)

        # ======================
        # Prepare timestamps for late testing
        # ======================
        self.past_time = fields.Datetime.to_string(fields.Datetime.from_string(fields.Datetime.now()) - timedelta(hours=25))

    def test_supply_late_notification(self):
        """Supply late notification every 24h"""
        # إنشاء طلب توريد جديد
        request = self.env['custom_supply.supply_request'].create({
            'branch_id': self.branch.id,
            'status': 'Supply',
            'request_date': self.past_time,
            'supply_manager_id': self.supply_manager.id,
        })

        # كرون التحقق من التأخير
        request.cron_check_late_requests()

        # تحقق من إضافة رسالة Chatter
        self.assertTrue(any("Supply Request" in m.body for m in request.message_ids),
                        "Chatter should have a supply late message")

        # تحقق من أن آخر إشعار تم تحديثه
        self.assertIsNotNone(request.last_supply_late_notify, "last_supply_late_notify should be set")

    def test_warehouse_late_notification(self):
        """Warehouse late notification every 24h"""
        # إنشاء طلب توريد جديد
        request = self.env['custom_supply.supply_request'].create({
            'branch_id': self.branch.id,
            'status': 'InWarehouse',
            'request_date': self.past_time,
            'supply_confirm_date': self.past_time,
            'warehouse_user_id': self.warehouse_user.id,
        })

        # كرون التحقق من التأخير
        request.cron_check_late_requests()

        # تحقق من إضافة رسالة Chatter
        self.assertTrue(any("Warehouse" in m.body for m in request.message_ids),
                        "Chatter should have a warehouse late message")

        # تحقق من أن آخر إشعار تم تحديثه
        self.assertIsNotNone(request.last_warehouse_late_notify, "last_warehouse_late_notify should be set")

    def test_delivery_late_notification(self):
        """Delivery late notification sent only once"""
        # إنشاء طلب توريد جديد
        request = self.env['custom_supply.supply_request'].create({
            'branch_id': self.branch.id,
            'status': 'OnRoad',
            'request_date': self.past_time,
            'supply_confirm_date': self.past_time,
            'warehouse_export_date': self.past_time,
            'received_date': fields.Datetime.to_string(fields.Datetime.from_string(fields.Datetime.now()) - timedelta(hours=1)),
        })

        # إضافة الحقل delivery_late_notified
        request.delivery_late_notified = False

        # كرون التحقق من التأخير
        request.cron_check_late_requests()

        # تحقق من إرسال الإشعار مرة واحدة
        self.assertTrue(request.delivery_late_notified, "Delivery late should be notified once")
        self.assertTrue(any("Delivery Delay" in m.body for m in request.message_ids),
                        "Chatter should have a delivery late message")

        # كرون مرة ثانية لا يجب إرسال إشعار جديد
        old_count = len(request.message_ids)
        request.cron_check_late_requests()
        self.assertEqual(old_count, len(request.message_ids), "No new delivery late message should be added")

if __name__ == '__main__':
    unittest.main()
