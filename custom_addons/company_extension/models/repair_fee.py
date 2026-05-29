from odoo import models, fields, api

class RepairFee(models.Model):
    _name = 'repair.fee'
    _description = 'Repair Operations/Services'
    
    repair_id = fields.Many2one('repair.order', string='Repair Order', required=True, ondelete='cascade')
    name = fields.Text(string='Description', required=True)
    product_id = fields.Many2one('product.product', string='Service', domain="[('type', '=', 'service')]")
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', default=1.0)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_price_subtotal', store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    currency_id = fields.Many2one('res.currency', related='repair_id.currency_id', store=True)
    company_id = fields.Many2one('res.company', related='repair_id.company_id', store=True)
    invoiced = fields.Boolean(string='Invoiced', copy=False, readonly=True)
    
    @api.depends('product_uom_qty', 'price_unit')
    def _compute_price_subtotal(self):
        for fee in self:
            fee.price_subtotal = fee.product_uom_qty * fee.price_unit
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Auto-fill description and price when service is selected"""
        if self.product_id:
            if not self.name:
                self.name = self.product_id.name
            self.price_unit = self.product_id.lst_price
