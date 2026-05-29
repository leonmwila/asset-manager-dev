{
    'name': 'Product to Asset Terminology',
    'version': '1.0',
    'category': 'Base',
    'summary': 'Changes UI terminology from Products/Product to Assets/Asset',
    'description': """
        This module changes the user interface terminology from "Products" to "Assets" 
        and "Product" to "Asset" throughout the Odoo interface. This is a UI-only change 
        and does not affect underlying variables or code.
        
        Features:
        - Replaces "Products" with "Assets" in menus, labels, and views
        - Replaces "Product" with "Asset" in menus, labels, and views
        - Works across all Odoo modules that use product terminology
        - Frontend JavaScript replacement for dynamic content
        - Translation overrides for model names and field labels
    """,
    'depends': ['base', 'product'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'product_to_asset/static/src/js/terminology_override.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

