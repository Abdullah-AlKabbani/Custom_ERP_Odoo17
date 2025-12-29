# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from datetime import timedelta

#charts

class HighManagerAvgDuration(models.Model):
    _name = "custom_supply.high_manager_report_avg_duration"
    _description = "High Manager - Average Durations (Supply / InWarehouse)"
    _auto = False
    _order = "id"

    id = fields.Integer("ID", readonly=True)

    state = fields.Selection(
        [
            ('Supply', 'Supply'),
            ('InWarehouse', 'InWarehouse')
        ],
        string="State",
        readonly=True
    )

    avg_duration_seconds = fields.Float("Average Duration (seconds)", readonly=True)
    # ===== حقل محسوب لعرضها بشكل مقروء =====
    avg_duration_readable = fields.Char(string="Average Duration (Readable)", compute="_compute_avg_readable", store=False)

    # ===== دالة حساب شكل الوقت المقروء =====
    def _compute_avg_readable(self):
        for rec in self:
            secs = rec.avg_duration_seconds or 0
            secs = int(secs)
            rec.avg_duration_readable = str(timedelta(seconds=secs))

    # ===== إنشاء الـ SQL View =====
    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'custom_supply_high_manager_report_avg_duration')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW custom_supply_high_manager_report_avg_duration AS
            SELECT
                1 AS id,
                'Supply'::text AS state,
                COALESCE(
                    AVG(EXTRACT(EPOCH FROM (supply_confirm_date - request_date))),
                    0
                )::double precision AS avg_duration_seconds
            FROM custom_supply_supply_request
            WHERE supply_confirm_date IS NOT NULL
              AND request_date IS NOT NULL

            UNION ALL

            SELECT
                2 AS id,
                'InWarehouse'::text AS state,
                COALESCE(
                    AVG(EXTRACT(EPOCH FROM (warehouse_export_date - supply_confirm_date))),
                    0
                )::double precision AS avg_duration_seconds
            FROM custom_supply_supply_request
            WHERE warehouse_export_date IS NOT NULL
              AND supply_confirm_date IS NOT NULL;
        """)

class BranchProductSupplyReport(models.Model):
    _name = "custom_supply.branch_product_supply_report"
    _description = "Branch Product Supply Report"
    _auto = False
    _rec_name = "branch_name"

    branch_id = fields.Many2one("custom_supply.branch", string="Branch", readonly=True)
    branch_name = fields.Char(string="Branch Name", readonly=True)

    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_name = fields.Char(string="Product Name", readonly=True)
    product_name_str = fields.Char(string="Product Name (Display)", readonly=True)
    full_label = fields.Char(string="Full Label", readonly=True)

    total_qty = fields.Float(string="Total Quantity", readonly=True)

    request_date = fields.Datetime(string="Request Date", readonly=True)
    supply_confirm_date = fields.Datetime(string="Supply Confirm Date", readonly=True)
    warehouse_export_date = fields.Datetime(string="Warehouse Export Date", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    b.id AS branch_id,
                    b.name AS branch_name,
                    p.id AS product_id,
                    pt.name AS product_name,
                    pt.name->>'en_US' AS product_name_str,
                    (pt.name->>'en_US') AS full_label,
                    COALESCE(SUM(l.supply_qty), 0) AS total_qty,
                    r.request_date AS request_date,
                    r.supply_confirm_date AS supply_confirm_date,
                    r.warehouse_export_date AS warehouse_export_date
                FROM custom_supply_supply_request_line l
                LEFT JOIN custom_supply_supply_request r ON l.request_id = r.id
                LEFT JOIN custom_supply_branch b ON r.branch_id = b.id
                LEFT JOIN product_product p ON l.product_id = p.id
                LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
                GROUP BY b.id, b.name, p.id, pt.name, r.request_date, r.supply_confirm_date, r.warehouse_export_date
            )
        """)

class SupplyVsExportReport(models.Model):
    _name = "custom_supply.supply_vs_export_report"
    _description = "Supply vs Export Quantity Report"
    _auto = False
    _order = "id"

    id = fields.Integer("ID", readonly=True)

    category = fields.Selection([
        ('match', 'Matches'),
        ('discrepancy', 'Discrepancies')
    ], string="Category", readonly=True)

    total_count = fields.Integer("Total Count", readonly=True)

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'custom_supply_supply_vs_export_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW custom_supply_supply_vs_export_report AS (

                -- Count of Matches
                SELECT
                    1 AS id,
                    'match' AS category,
                    COUNT(*) AS total_count
                FROM custom_supply_supply_request_line
                WHERE export_qty IS NOT NULL
                  AND supply_qty IS NOT NULL
                  AND export_qty = supply_qty

                UNION ALL

                -- Count of Discrepancies
                SELECT
                    2 AS id,
                    'discrepancy' AS category,
                    COUNT(*) AS total_count
                FROM custom_supply_supply_request_line
                WHERE export_qty IS NOT NULL
                  AND supply_qty IS NOT NULL
                  AND export_qty != supply_qty
            );
        """)

class SupplyVsSuggestionReport(models.Model):
    _name = "custom_supply.supply_vs_suggestion_report"
    _description = "Suggestion vs Supply Quantity Report"
    _auto = False     # لأنه SQL View
    _order = "id"

    id = fields.Integer("ID", readonly=True)

    category = fields.Selection([
        ('match', 'Matches'),
        ('discrepancy', 'Discrepancies')
    ], string="Category", readonly=True)

    total_count = fields.Integer("Total Count", readonly=True)

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'custom_supply_supply_vs_suggestion_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW custom_supply_supply_vs_suggestion_report AS (

                -- Matches (excluding zero-zero pairs)
                SELECT
                    1 AS id,
                    'match' AS category,
                    COUNT(*) AS total_count
                FROM custom_supply_supply_request_line
                WHERE suggested_qty IS NOT NULL
                  AND supply_qty IS NOT NULL
                  AND suggested_qty = supply_qty
                  AND NOT (
                        COALESCE(suggested_qty, 0) = 0
                    AND COALESCE(supply_qty, 0) = 0
                  )

                UNION ALL

                -- Discrepancies (excluding zero-zero pairs)
                SELECT
                    2 AS id,
                    'discrepancy' AS category,
                    COUNT(*) AS total_count
                FROM custom_supply_supply_request_line
                WHERE suggested_qty IS NOT NULL
                  AND supply_qty IS NOT NULL
                  AND suggested_qty != supply_qty
                  AND NOT (
                        COALESCE(suggested_qty, 0) = 0
                    AND COALESCE(supply_qty, 0) = 0
                  )
            );
        """)

class SupplyLateReport(models.Model):
    _name = "custom_supply.late_report"
    _description = "Late Requests Summary (rows for pie charts)"
    _auto = False

    id = fields.Integer(readonly=True)
    kind = fields.Selection([('supply','Supply'), ('warehouse','Warehouse'), ('delivery','Delivery')], string="Kind", readonly=True)
    label = fields.Char(string="Label", readonly=True)   # 'Late' | 'On Time'
    value = fields.Integer(string="Value", readonly=True)

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'custom_supply_late_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW custom_supply_late_report AS
            -- Supply Late
            SELECT
                ROW_NUMBER() OVER () AS id,
                'supply'::text AS kind,
                (CASE WHEN late_supply THEN 'Late' ELSE 'On Time' END) AS label,
                COUNT(*) AS value
            FROM custom_supply_supply_request
            GROUP BY (CASE WHEN late_supply THEN 'Late' ELSE 'On Time' END)

            UNION ALL

            -- Warehouse Late
            SELECT
                ROW_NUMBER() OVER () + 1000 AS id,
                'warehouse'::text AS kind,
                (CASE WHEN late_warehouse THEN 'Late' ELSE 'On Time' END) AS label,
                COUNT(*) AS value
            FROM custom_supply_supply_request
            GROUP BY (CASE WHEN late_warehouse THEN 'Late' ELSE 'On Time' END)

            UNION ALL

            -- Delivery Late (فقط الطلبات المكتملة)
            SELECT
                ROW_NUMBER() OVER () + 2000 AS id,
                'delivery'::text AS kind,
                (CASE WHEN late_delivery THEN 'Late' ELSE 'On Time' END) AS label,
                COUNT(*) AS value
            FROM custom_supply_supply_request
            WHERE status = 'Done'
            GROUP BY (CASE WHEN late_delivery THEN 'Late' ELSE 'On Time' END)
        """)

# Pivot table

class BranchProductMonthlyReport(models.Model):
    _name = "custom_supply.branch_product_monthly_report"
    _description = "Branch Product Monthly Detailed Report"
    _auto = False

    # ============================
    #        FIELDS
    # ============================

    branch_id = fields.Many2one("custom_supply.branch", string="Branch", readonly=True)
    branch_name = fields.Char(string="Branch Name", readonly=True)

    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_name = fields.Char(string="Product Name", readonly=True)

    month = fields.Date(string="Month", readonly=True)
    full_label = fields.Char(string="Full Label", readonly=True)

    # Original measures
    total_qty = fields.Float(string="Supply Quantity", readonly=True)
    export_qty = fields.Float(string="Exported Quantity", readonly=True)

    # New computed measures (calculated inside SQL view)
    net_qty = fields.Float(string="Net Quantity", readonly=True)
    export_ratio = fields.Float(string="Export Ratio %", readonly=True)

    # ============================
    #        SQL VIEW
    # ============================

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

        self._cr.execute(f"""
            CREATE OR REPLACE VIEW custom_supply_branch_product_monthly_report AS (
            SELECT
                ROW_NUMBER() OVER () AS id,
        
                b.id AS branch_id,
                b.name AS branch_name,
        
                p.id AS product_id,
                pt.name AS product_name,
                (pt.name->>'en_US') AS full_label,
        
                date_trunc('month', r.request_date)::date AS month,
        
                -- Measures
                COALESCE(SUM(l.supply_qty), 0) AS total_qty,
                COALESCE(SUM(l.export_qty), 0) AS export_qty,
        
                -- net quantity
                COALESCE(SUM(l.supply_qty), 0) - COALESCE(SUM(l.export_qty), 0) AS net_qty,
        
                -- export ratio %
                CASE 
                    WHEN COALESCE(SUM(l.supply_qty), 0) = 0 THEN 0
                    ELSE ROUND(
                            (
                                (COALESCE(SUM(l.export_qty), 0) 
                                / NULLIF(COALESCE(SUM(l.supply_qty), 0), 0)
                                ) * 100
                            )::numeric,
                        2
                    )
                END AS export_ratio
        
            FROM custom_supply_supply_request_line l
            LEFT JOIN custom_supply_supply_request r ON l.request_id = r.id
            LEFT JOIN custom_supply_branch b ON r.branch_id = b.id
            LEFT JOIN product_product p ON l.product_id = p.id
            LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
        
            GROUP BY
                b.id,
                b.name,
                p.id,
                pt.name,
                date_trunc('month', r.request_date)
        
            ORDER BY
                date_trunc('month', r.request_date) DESC,
                p.id
        );
        """)

class BranchMonthlyRequestCount(models.Model):
    _name = "custom_supply.branch_monthly_request_count"
    _description = "Branch Monthly Supply Request Count Report"
    _auto = False

    branch_id = fields.Many2one("custom_supply.branch", string="Branch", readonly=True)
    branch_name = fields.Char(string="Branch Name", readonly=True)
    month = fields.Char(string="Month", readonly=True)  # صيغة YYYY-MM
    request_count = fields.Integer(string="Number of Requests", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    b.id AS branch_id,
                    b.name AS branch_name,
                    TO_CHAR(r.request_date, 'YYYY-MM') AS month,
                    COUNT(r.id) AS request_count
                FROM custom_supply_supply_request r
                LEFT JOIN custom_supply_branch b ON r.branch_id = b.id
                GROUP BY b.id, b.name, TO_CHAR(r.request_date, 'YYYY-MM')
                ORDER BY b.id, month
            )
        """)
