{
    'name': 'Asset Labelling',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Mark Lot/Serial items as labelled and support barcode labelling scans',
    'description': """
        Adds a Labelled checkbox to Lot/Serial Numbers and lets barcode scans
        automatically find and mark matching items as labelled.
    """,
    'depends': ['stock', 'web'],
    'data': [
        'views/stock_lot_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'asset_labelling/static/src/js/lot_label_scanner.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
