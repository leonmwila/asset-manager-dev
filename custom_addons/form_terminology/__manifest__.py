{
    'name': 'Form Terminology',
    'version': '1.0',
    'category': 'Repair',
    'summary': 'Terminology overrides for repair forms',
    'description': """
        Updates repair order form field labels to match asset terminology.
    """,
    'depends': ['repair'],
    'data': [
        'views/repair_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
