{
    'name': 'Product Depreciation',
    'version': '1.0',
    'category': 'Inventory/Accounting',
    'summary': 'Adds depreciation functionality to Products and Lot/Serial Numbers',
    'description': """
        This module adds depreciation fields and calculations to Products and Lot/Serial Numbers.
        
        Features:
        - Depreciation method and useful life on Products
        - Fair value, disposal date, disposal price on Lot/Serial Numbers
        - Automatic calculation of depreciation amount and Net Book Value (NBV)
        - Auto-population of disposal date when disposal price is entered
    """,
    'depends': ['product', 'stock'],
    'data': [
        'data/ir_model_data.xml',
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/product_serial_status_views.xml',
        'views/stock_lot_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

