{
    'name': 'Add New Bulk Lots/Serials',
    'version': '1.0.0',
    'category': 'Inventory',
    'summary': 'Create multiple Lots/Serials with shared data in one flow',
    'depends': ['stock', 'company_extension', 'product_depreciation', 'dept_link'],
    'data': [
        'security/ir.model.access.csv',
        'views/bulk_lot_wizard_views.xml',
        'views/stock_lot_tree_button_views.xml',
    ],
    'installable': True,
    'application': False,
}
