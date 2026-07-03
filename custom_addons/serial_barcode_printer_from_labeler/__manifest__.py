{
    'name': 'Serial Barcode Printer From Labeler',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Print one Lot/Serial barcode label per compact PDF page',
    'description': """
        Prints Lot/Serial barcode labels in a labeler-friendly PDF layout.

        Features:
        - One selected Lot/Serial per PDF page
        - Compact custom paper format (smaller than A4)
        - Dedicated print action for labeler workflows
    """,
    'depends': ['stock', 'product', 'serial_barcode_printer'],
    'data': [
        'views/stock_lot_views.xml',
        'report/lot_barcode_labeler_reports.xml',
        'report/lot_barcode_labeler_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
