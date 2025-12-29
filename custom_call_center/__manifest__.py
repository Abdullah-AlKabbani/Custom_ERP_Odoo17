{
    'name': 'Custom Call Center',
    'version': '1.0',
    'summary': 'Manage Call Center Operations',
    'author': 'Your Name',
    'depends': ['base', 'contacts', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/call_center_views.xml',
    ],
    'installable': True,
    'application': True,
}
