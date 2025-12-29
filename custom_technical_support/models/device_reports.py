# -*- coding: utf-8 -*-
from odoo import models, fields

# ===============================
# Device Inventory Report (Tree)
# ===============================
class ReportDeviceInventory(models.Model):
    _name = 'report.ts.device.inventory'
    _description = 'Device Inventory Report'
    _auto = False  # هذا لا ينشئ جدول، نستخدمه لعرض تقرير
    _order = 'branch_id, device_id'

    branch_id = fields.Many2one('custom_supply.branch', string='Branch')
    device_id = fields.Many2one('ts.device', string='Device')
    current_qty = fields.Integer(string='Current Quantity')
    last_move_date = fields.Datetime(string='Last Operation Date')
    branch_user_id = fields.Many2one('res.users', string='Branch Manager')

# ===============================
# Device Movement Log (Tree)
# ===============================
class ReportDeviceMove(models.Model):
    _name = 'report.ts.device.move'
    _description = 'Device Movement Log'
    _auto = False
    _order = 'date desc'

    device_id = fields.Many2one('ts.device', string='Device')
    branch_id = fields.Many2one('custom_supply.branch', string='Branch')
    move_type = fields.Selection([
        ('in','Input'), ('out','Output'),
        ('scrap','Scrap'), ('inventory','Inventory Adjustment')
    ], string='Move Type')
    qty = fields.Integer(string='Quantity')
    qty_before = fields.Integer(string='Quantity Before')
    qty_after = fields.Integer(string='Quantity After')
    date = fields.Datetime(string='Date')
    user_id = fields.Many2one('res.users', string='Performed By')
    note = fields.Text(string='Notes')

# ===============================
# Pivot Table: Branch × Device
# ===============================
class PivotDeviceBranch(models.Model):
    _name = 'pivot.ts.device.branch'
    _description = 'Pivot Device × Branch'
    _auto = False

    branch_id = fields.Many2one('custom_supply.branch', string='Branch')
    device_id = fields.Many2one('ts.device', string='Device')
    current_qty = fields.Integer(string='Current Quantity')

# ===============================
# Pivot Table: Device Movement Summary
# ===============================
class PivotDeviceMove(models.Model):
    _name = 'pivot.ts.device.move'
    _description = 'Pivot Device Movement Summary'
    _auto = False

    device_id = fields.Many2one('ts.device', string='Device')
    move_type = fields.Selection([
        ('in','Input'), ('out','Output'),
        ('scrap','Scrap'), ('inventory','Inventory Adjustment')
    ], string='Move Type')
    total_qty = fields.Integer(string='Total Quantity')

# ===============================
# Chart: Devices per Branch
# ===============================
class ChartDevicePerBranch(models.Model):
    _name = 'chart.ts.device.branch'
    _description = 'Chart Devices per Branch'
    _auto = False

    branch_id = fields.Many2one('custom_supply.branch', string='Branch')
    device_id = fields.Many2one('ts.device', string='Device')
    current_qty = fields.Integer(string='Current Quantity')

# ===============================
# Chart: Device Quantity Over Time
# ===============================
class ChartDeviceHistory(models.Model):
    _name = 'chart.ts.device.history'
    _description = 'Chart Device Quantity Over Time'
    _auto = False

    device_id = fields.Many2one('ts.device', string='Device')
    branch_id = fields.Many2one('custom_supply.branch', string='Branch')
    qty = fields.Integer(string='Quantity')
    date = fields.Datetime(string='Date')

# ===============================
# Chart: Device Distribution by Category
# ===============================
class ChartDeviceCategory(models.Model):
    _name = 'chart.ts.device.category'
    _description = 'Device Distribution by Category'
    _auto = False

    category_id = fields.Many2one('ts.device.category', string='Category')
    total_qty = fields.Integer(string='Total Quantity')
