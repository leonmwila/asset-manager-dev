from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    category_code = fields.Char(string='Category Code', required=True, size=2)
