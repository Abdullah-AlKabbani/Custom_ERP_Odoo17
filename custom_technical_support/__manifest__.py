{
    "name": "Custom Technical Support",
    "version": "1.0.0",
    "summary": "Technical Support & Device Management System",
    "author": "ِAbdullah Al-Kabbani",
    "category": "Services",
    "depends": [
        "base",
        "company_branch",  # لأنك تستخدم الفروع
    ],
    "data": [
        "security/security_group.xml",
        "security/ir.model.access.csv",

        "data/device_categories_data.xml",

        "views/device/ts_device_category_views.xml",
        "views/device/ts_device_views.xml",
        "views/device/ts_device_branch_views.xml",
        "views/device/ts_device_brand_views.xml",
        "views/device/ts_device_model_views.xml",
        "views/device/ts_device_scrap_reason_tree.xml",
        "views/device/ts_device_branch_sync_settings_views.xml",
        "views/operations/ts_device_move_views.xml",
        "views/operations/ts_device_inventory_views.xml",

        "views/reports/views_chart_device_category.xml",
        "views/reports/views_chart_device_history.xml",
        "views/reports/views_chart_device_per_branch.xml",
        "views/reports/views_report_device_inventory.xml",
        "views/reports/views_report_device_move.xml",

        "views/actions.xml",
        "views/menus.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'custom_technical_support/static/src/js/show_password.js',
        ],
    },
    'license': 'LGPL-3',
    "installable": True,
    "application": True,
}
