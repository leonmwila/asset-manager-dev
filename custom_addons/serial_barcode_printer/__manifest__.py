{
    'name': 'Serial Number Barcode Printer',
    'version': '1.3',
    'category': 'Inventory',
    'summary': 'Print barcode labels for Lot/Serial Numbers',
    'description': """
        This module adds barcode printing functionality to Lot/Serial Numbers,
        similar to the product barcode printing feature.
        
        Features:
        - Generate barcodes for serial numbers
        - Print multiple barcode labels on sheets
        - ZPL format support for label printers
    """,
    'depends': ['stock', 'product'],
    'data': [
        'views/stock_lot_views.xml',
        'report/lot_barcode_reports.xml',
        'report/lot_barcode_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
