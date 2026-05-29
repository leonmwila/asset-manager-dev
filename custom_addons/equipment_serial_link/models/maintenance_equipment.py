from odoo import models, fields


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    product_id = fields.Many2one('product.product', string='Product')
    # Note: cost field already exists in standard maintenance.equipment model
    # Make serial_number a related field to the standard serial_no field
    # This maintains backward compatibility while using Odoo's standard field
    serial_number = fields.Char(string='Serial Number', related='serial_no', store=True, readonly=False)