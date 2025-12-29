{
    'name': 'Mission Management',
    'version': '1.0',
    'category': 'HR',
    'summary': 'Manage missions for employees',
    'description': 'Module for managing employee missions including mission type, objectives, budget, and status.',
    'author': 'Your Name',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/mission_view.xml',
        'report/mission_report.xml',
    ],
    'installable': True,
    'application': True,
}
