{
    'name': 'SQL Server Customer Sync',
    'version': '1.0',
    'category': 'Contacts',
    'summary': 'Automated sync of customers from SQL Server to Odoo Contacts.',
    'author': 'Your Name',
    'depends': ['base', 'contacts'],
    'data': [
        'data/cron_job.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
