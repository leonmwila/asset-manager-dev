from odoo import models, fields

class ProductCategory2(models.Model):
    _name = 'product.category.2'
    _description = 'Product Category 2'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)
    parent_id = fields.Many2one('product.category.2', string='Parent Category', index=True)
    child_ids = fields.One2many('product.category.2', 'parent_id', string='Child Categories')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Category name must be unique!')
    ]
