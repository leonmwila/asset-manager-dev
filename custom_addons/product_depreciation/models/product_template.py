from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    depreciation_method = fields.Selection(
        [
            ('straight_line', 'Straight Line'),
            ('declining_balance', 'Declining Balance'),
            ('units_of_production', 'Units of Production'),
            ('sum_of_years', 'Sum of Years Digits'),
        ],
        string='Depreciation Method',
        help='Method used to calculate depreciation for assets of this product type'
    )
    
    useful_life = fields.Float(
        string='Useful Life (Years)',
        help='Expected useful life of the asset in years. Used for depreciation calculations.'
    )

