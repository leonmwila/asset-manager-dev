from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    category_2_id = fields.Many2one('product.category.2', string='Product Category 2', ondelete='restrict')
    model = fields.Char(string='Model', help='Product model number or name')
    make = fields.Char(string='Make', help='Product manufacturer or make')
