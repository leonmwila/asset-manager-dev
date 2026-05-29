{
    'name': 'Department Link',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Link assets/serial numbers to HR departments',
    'description': """
        Adds a Department field to Lot/Serial Numbers (Assets) so each asset
        can be linked to an HR department.
    """,
    'depends': ['stock', 'hr'],
    'data': [
        'views/stock_lot_views.xml',
    ],
    'installable': True,
    'application': False,
}
