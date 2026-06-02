{
    'name': 'Asset Labelling',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Bulk label or unlabel Lot/Serial items from a wizard',
    'description': """
        Adds a Labelled checkbox to Lot/Serial Numbers and provides a bulk
        wizard to label or remove labels from multiple assets.
    """,
    'depends': ['stock', 'add_new_bulk_lots_serials'],
    'data': [
        'security/ir.model.access.csv',
        'views/lot_label_wizard_views.xml',
        'views/stock_lot_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
