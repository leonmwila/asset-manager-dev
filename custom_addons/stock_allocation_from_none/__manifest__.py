{
    'name': 'Stock Allocation from None',
    'version': '19.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Allocate serials that currently have no stock location to an internal stock location',
    'description': """
        Adds a wizard on Lot/Serial records to place imported orphan serials
        (records with no internal stock quant) into a selected internal stock
        location that the user is allowed to access.
    """,
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_allocation_cron.xml',
        'views/stock_allocation_from_none_views.xml',
        'views/stock_allocation_job_views.xml',
        'views/stock_lot_actions.xml',
    ],
    'installable': True,
    'application': False,
}
