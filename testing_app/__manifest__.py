{
    'name': 'Testing app',
    'version': '1.0',
    'author': 'Abdalrahman',
    'category': 'Human Resources',
    'summary': 'A testing app',
    'depends': ['base', 'sale_management', 'account', 'mail'],
    'data': [
        'views/base_menu.xml',
        'views/property_view.xml',
        'security/ir.model.access.csv',
        'views/tag_view.xml',
        'views/owner_view.xml',
        'views/sale_order_view.xml',
        'views/building_view.xml',
    ],
    'assets': {
        'web.assets_backend': ['/testing_app/static/src/css/property.css']
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
