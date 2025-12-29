{
    'name': 'Overtime Request',
    'version': '1.0',
    'summary': 'Manage employee overtime requests',
    'category': 'Human Resources',
    'author': 'Your Name',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/overtime_request_view.xml',
        'report/overtime_report.xml',
    ],
    'installable': True,
    'application': True,
}
