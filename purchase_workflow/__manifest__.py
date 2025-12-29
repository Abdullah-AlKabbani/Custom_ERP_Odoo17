{
    'name': 'Purchase Workflow',
    'version': '1.0',
    'summary': 'Multi-level approval purchase request workflow with vendor offers',
    'category': 'Purchases',
    'author': 'Your Company',
    'depends': ['purchase', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_request_sequence.xml',
        'views/menu.xml',
        'views/purchase_request_views.xml',
        'views/purchase_offer_views.xml',
    ],
    'installable': True,
    'application': True,
}
