{
    'name': 'Device Contract',
    'version': '1.0',
    'category': 'Maintenance',
    'summary': 'Adds a contract image field to Maintenance Equipment',
    'depends': ['maintenance'],
    'data': [
        'views/maintenance_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
