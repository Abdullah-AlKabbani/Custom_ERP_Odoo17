# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BranchReportByLocation(models.Model):
    _name = "custom_supply.branch.report.location"
    _description = "Branch Report by Country and City"
    _auto = False

    country_id = fields.Many2one('custom_supply.country', string="Country", tracking=True)
    city_id = fields.Many2one('custom_supply.city', string="City", tracking=True, domain="[('country_id','=',country_id)]")
    branch_count = fields.Integer(string="Number of Active Branches")

    @api.model
    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS custom_supply_branch_report_location CASCADE;
            CREATE OR REPLACE VIEW custom_supply_branch_report_location AS (
                SELECT
                    MIN(id) AS id,
                    country_id,
                    city_id,
                    COUNT(*) AS branch_count
                FROM custom_supply_branch
                WHERE state = 'active'
                GROUP BY country_id, city_id
            );
        """)


class BranchReportByState(models.Model):
    _name = "custom_supply.branch.report.state"
    _description = "Branch Report by State"
    _auto = False

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('closed', 'Closed')
    ], string="State")

    branch_count = fields.Integer(string="Number of Branches")

    @api.model
    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS custom_supply_branch_report_state CASCADE;
            CREATE OR REPLACE VIEW custom_supply_branch_report_state AS (
                SELECT
                    MIN(id) AS id,
                    state,
                    COUNT(*) AS branch_count
                FROM custom_supply_branch
                GROUP BY state
            );
        """)

class BranchReportByType(models.Model):
    _name = "custom_supply.branch.report.type"
    _description = "Branch Report by Type"
    _auto = False

    branch_type_id = fields.Many2one(
        'custom_supply.branch.type',
        string="Branch Type",
        readonly=True
    )

    branch_count = fields.Integer(
        string="Number of Branches",
        readonly=True
    )

    @api.model
    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS custom_supply_branch_report_type CASCADE;
            CREATE OR REPLACE VIEW custom_supply_branch_report_type AS (
                SELECT
                    MIN(b.id) AS id,
                    b.branch_type_id AS branch_type_id,
                    COUNT(*) AS branch_count
                FROM custom_supply_branch b
                WHERE b.branch_type_id IS NOT NULL
                GROUP BY b.branch_type_id
            );
        """)

