{
    'name': 'GPS Management',
    'version': '1.0',
    'summary': 'Manage The GPS Tickets',
    "description": """
            GPS Ticket Management Module
        """,
    "author": "AbdAlrahman",
    "category": "Operations",
    "depends": ["base", "fleet", "hr"],
    "data": ['security/ir.model.access.csv',
             "views/base_menu.xml",
             "views/gps_view.xml",
             "views/violations_view.xml",
             ],
    "installable": True,
    "application": True,
}
