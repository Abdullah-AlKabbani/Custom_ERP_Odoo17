# company_branch/__manifest__.py
{
    "name": "Company Branches",
    "version": "1.0.0",
    "summary": "Core Branch module shared across all company departments",
    "author": "Abdullah Al-Kabbani",
    "category": "Administration",
    "depends": [
        "base",
        "mail"
    ],
    "data": [
        'data/country_city_data.xml',
        'data/branch_type_data.xml',
        "security/branch_groups.xml",
        "security/ir.model.access.csv",
        "views/branch_views.xml",
        'views/branch_type_views.xml',
        'views/country_city.xml',
        "views/branch_actions.xml",
        "views/menu.xml",
        'reports/branch_report_location_views.xml',
        'reports/branch_report_state_views.xml',
        'reports/branch_report_type_views.xml',
        'reports/action_reports.xml',
        'reports/menu_reports.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'company_branch/static/src/css/kanban_colors.css',
        ],
    },
    'license': 'LGPL-3',
    "installable": True,
    "application": True
}
