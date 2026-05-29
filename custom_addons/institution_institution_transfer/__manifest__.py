{
    'name': 'Institution Institution Transfer',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Request and approve inter-institution asset transfers',
    'description': """
        Adds transfer requests for Lot/Serial Numbers so assets can be moved
        between institutions (companies) with an approval workflow.
    """,
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/institution_transfer_views.xml',
        'views/stock_lot_actions.xml',
        'wizard/transfer_request_views.xml',
    ],
    'installable': True,
    'application': False,
}
