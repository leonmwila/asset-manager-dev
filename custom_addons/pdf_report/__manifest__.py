{
    'name': 'PDF Report',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Print asset PDF report from Lots/Serials',
    'description': """
        Adds a printable PDF report for selected Lot/Serial Numbers
        from the Lots/Serials list view.
    """,
    'depends': ['stock'],
    'data': [
        'report/lot_asset_report.xml',
    ],
    'installable': True,
    'application': False,
}
