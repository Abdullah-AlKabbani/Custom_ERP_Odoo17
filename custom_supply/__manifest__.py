# -*- coding: utf-8 -*-
{
    'name': 'Custom Supply Management',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': """It is a system that manages branch supply requests from the warehouse smoothly in Odoo 17. 
    The system manages supply requests in (branches, supply department, warehouse, administration).""",
    'description': """The system begins by creating a purchase order from the branch, which includes the current inventory of the materials to be supplied. 
    The system then suggests an intelligent value for the supply based on the procurement manager's decisions in previous orders. 
    Branch employees can suggest modifications to the system's value and add comments. 
    The order is then sent to the procurement manager, who reviews employee comments and values and confirms the quantities to be supplied. 
    Next, the order is sent to the warehouse manager, who exports the quantities specified by the procurement manager. 
    If there is a discrepancy, it is recorded along with any relevant notes. 
    The order is then sent to the driver, and upon arrival at the branch, a branch employee receives it and confirms the values that were issued from the warehouse. 
    The module includes a notification system that alerts you if the order processing in the procurement or warehouse department is delayed by more than 24 hours, or if the order is delivered outside of the designated days or times for each branch. 
    The module also provides advanced reports such as: average order processing time for each department, number of delays in each department, total quantities of each material requested in each branch per month, and the total number of monthly orders for each branch.
    Other filters and useful features are also included in the procurement system.""",
    'author': 'Abdullah Al-Kabbani',
    'website': '',
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'depends': [
        'company_branch',
        'base',
        'product',
        'mail',
        'web',
    ],
    'data': [
        'data/ir_cron_data.xml',
        'data/activity_cron.xml',
        'data/supply_day.xml',
        'data/sequence_data.xml',
        'data/supply_days_data.xml',
        'data/branch_products_cron.xml',
        'security/custom_supply_groups.xml',
        'security/ir.model.access.csv',
        'views/supply_branch_view.xml',
        'views/branch_supply_schedule_view.xml',
        'views/branch_product_views.xml',
        'views/supply_request_views.xml',
        'views/received_requests.xml',
        'views/supply_request_tracking_views.xml',
        'views/product_template_views.xml',
        'views/supply_unit_views.xml',
        'views/product_supply_view.xml',
        'views/branch_product_sync_settings_views.xml',
        'views/supply_branch_actions.xml',
        'views/menus.xml',
        'report/supply_vs_suggestion_report_views.xml',
        'report/high_manager_report_views.xml',
        'report/supply_vs_export_report_views.xml',
        'report/branch_product_supply_report_views.xml',
        'report/branch_supply_pivot_report_views.xml',
        'report/late_requests.xml',
        'report/supply_pivot_views.xml',
        'report/menu_reports.xml',
        'report/supply_request_report.xml',
        'report/supply_request_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_supply/static/src/css/kanban_colors.css',
            'custom_supply/static/src/js/branch_product_filter.js',
            'custom_supply/static/src/js/pivot_default_collapse.js',
        ],
    },
    'images': ['static/description/supply_management.png'],
}
