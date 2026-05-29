{
    'name': 'Spares Product Type',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Adds Spares product type and part number',
    'description': """
        Adds a new Product Type "Spares" and a Part Number field for products.
    """,
    'depends': ['product', 'stock', 'repair'],
    'data': [
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
