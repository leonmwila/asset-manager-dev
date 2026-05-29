{
    'name': 'Asset Disposal',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Asset disposal workflow for lots/serials',
    'depends': ['stock', 'sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/asset_donation_rules.xml',
        'data/asset_disposal_sequence.xml',
        'data/asset_donation_sequence.xml',
        'views/asset_disposal_views.xml',
        'views/asset_donation_views.xml',
        'views/stock_lot_views.xml',
    ],
    'installable': True,
    'application': False,
}
