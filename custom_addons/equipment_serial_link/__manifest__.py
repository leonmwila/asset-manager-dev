{
    'name': 'Equipment Auto Create from Serial',
    'version': '1.1',
    'category': 'Inventory/Maintenance',
    'summary': 'Automatically create Maintenance Equipment when Serial Numbers are created',
    'depends': ['stock', 'maintenance', 'account', 'company_extension'],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_request_views.xml',
        'views/product_template_views.xml',
        'views/stock_lot_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
