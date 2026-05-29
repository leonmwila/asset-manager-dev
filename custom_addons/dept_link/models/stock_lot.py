from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Department responsible for this asset/serial number'
    )
