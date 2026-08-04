{
    'name': 'Maintenance Parts Workflow',
    'version': '1.0',
    'category': 'Inventory/Maintenance',
    'summary': 'Approval and signed collection workflow for maintenance part requests',
    'depends': ['maintenance', 'stock', 'equipment_serial_link'],
    'data': [
        'security/maintenance_parts_security.xml',
        'security/ir.model.access.csv',
        'data/maintenance_part_request_sequence.xml',
        'views/maintenance_part_request_views.xml',
    ],
    'installable': True,
    'application': False,
}
