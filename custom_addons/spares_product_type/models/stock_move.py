from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_id = fields.Many2one(
        'product.product',
        'Product',
        check_company=True,
        domain="[('type', 'in', ['consu', 'spares'])]",
        index=True,
        required=True,
    )
