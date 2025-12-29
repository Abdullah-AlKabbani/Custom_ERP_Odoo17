{
    "name": "Help Desk Visits Report",
    "summary": "Website form + back-office for Help Desk Visit Reports",
    "version": "17.0.1.0.1",
    "license": "LGPL-3",
    "depends": ["base", "website", "mail"],
    "data": [
        "security/security.xml",              # ← groups & category
        "security/ir.model.access.csv",       # ← ACL bound to Manager group
        "data/ir_sequence.xml",
        "data/website_menu.xml",              # ← stays public
        "views/menu_action_views.xml",        # ← menus restricted to Manager
        "views/helpdesk_config_views.xml",
        "views/helpdesk_report_views.xml",
        "views/helpdesk_report_kanban.xml",
        "views/website_templates.xml",
    ],
    "application": True,
}
