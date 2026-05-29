from odoo import models, fields


class ProductSerialStatus(models.Model):
    _name = 'product.serial.status'
    _description = 'Serial Status for Products'
    _order = 'name'
    
    name = fields.Char(
        string='Status Name',
        required=True,
        help='Name of the status (e.g., Active, Inactive, New, Used, etc.)'
    )
    
    product_ids = fields.Many2many(
        'product.template',
        'product_serial_status_rel',
        'status_id',
        'product_id',
        string='Products',
        help='Products that can use this status'
    )

