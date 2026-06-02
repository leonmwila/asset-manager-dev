from odoo import fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    labelled = fields.Boolean(
        string='Labelled',
        default=False,
        help='Ticked when the physical item label has been applied.',
    )
