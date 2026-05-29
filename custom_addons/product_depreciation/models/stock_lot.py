from odoo import models, fields, api
from datetime import date, datetime


class StockLot(models.Model):
    _inherit = 'stock.lot'
    
    acquisition_date = fields.Date(
        string='Acquisition Date',
        help='Date when the asset was acquired',
        default=lambda self: fields.Date.today()
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        domain="[('supplier_rank', '>', 0)]",
        help='Supplier/vendor who provided this asset'
    )
    
    # Temporarily commented - will uncomment after module upgrade
    # serial_status_id = fields.Many2one(
    #     'product.serial.status',
    #     string='Serial Status',
    #     domain="[('product_ids', '=', product_id.product_tmpl_id)]",
    #     help='Current status of this serial/lot. Only statuses assigned to the selected product are shown.'
    # )
    # 
    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     """Clear serial_status when product changes"""
    #     if self.product_id and self.serial_status_id:
    #         # Clear status if it's not valid for the new product
    #         if self.product_id.product_tmpl_id not in self.serial_status_id.product_ids:
    #             self.serial_status_id = False
    #     else:
    #         self.serial_status_id = False
    
    fair_value = fields.Float(
        string='Fair Value',
        help='Initial fair value or acquisition cost of the asset'
    )

    lot_acquisition_price = fields.Float(
        string='Acquisition Price',
        help='Acquisition price for this specific lot/serial. If empty, product acquisition price is used for depreciation.'
    )
    
    disposal_date = fields.Date(
        string='Disposal Date',
        help='Date when the asset was disposed of'
    )
    
    disposal_price = fields.Float(
        string='Disposal Price',
        help='Price received when the asset was disposed of'
    )
    
    depreciation_amount = fields.Float(
        string='Depreciation Amount',
        compute='_compute_depreciation',
        store=True,
        help='Total accumulated depreciation amount'
    )
    
    nbv = fields.Float(
        string='Net Book Value (NBV)',
        compute='_compute_depreciation',
        store=True,
        help='Net Book Value = Depreciation Base - Depreciation Amount'
    )
    
    @api.depends('lot_acquisition_price', 'product_id.standard_price', 'disposal_price', 'disposal_date', 'product_id.product_tmpl_id.depreciation_method', 
                 'product_id.product_tmpl_id.useful_life', 'acquisition_date')
    def _compute_depreciation(self):
        """Calculate depreciation amount and NBV based on product's depreciation method and useful life"""
        for lot in self:
            depreciation_amount = 0.0
            nbv = 0.0

            depreciation_base = lot.lot_acquisition_price if lot.lot_acquisition_price not in (False, None) else (lot.product_id.standard_price or 0.0)
            
            # Only calculate if we have the required values
            # Access product template through product_id.product_tmpl_id
            product_template = lot.product_id.product_tmpl_id if lot.product_id else False
            if depreciation_base > 0 and product_template and product_template.depreciation_method and product_template.useful_life:
                method = product_template.depreciation_method
                useful_life = product_template.useful_life
                
                # Get acquisition date (use acquisition_date field or create_date as fallback)
                if lot.acquisition_date:
                    acquisition_date = lot.acquisition_date
                elif lot.create_date:
                    acquisition_date = lot.create_date.date()
                else:
                    acquisition_date = date.today()
                
                # Get disposal date or use today's date for calculation
                end_date = lot.disposal_date if lot.disposal_date else date.today()
                
                # Calculate years elapsed
                if acquisition_date and end_date:
                    delta_days = (end_date - acquisition_date).days
                    years_elapsed = delta_days / 365.25  # Account for leap years
                    
                    # Ensure we don't depreciate beyond useful life
                    years_elapsed = min(years_elapsed, useful_life) if useful_life > 0 else 0
                    
                    # Calculate depreciation based on method
                    if method == 'straight_line':
                        # Straight-line: (Depreciation Base - Disposal Price) / Useful Life * Years Elapsed
                        depreciable_amount = depreciation_base - (lot.disposal_price or 0.0)
                        if useful_life > 0:
                            annual_depreciation = depreciable_amount / useful_life
                            depreciation_amount = annual_depreciation * years_elapsed
                    
                    elif method == 'declining_balance':
                        # Declining balance: More complex, using double declining balance
                        # Rate = 2 / Useful Life
                        if useful_life > 0:
                            rate = 2.0 / useful_life
                            book_value = depreciation_base
                            for year in range(int(years_elapsed)):
                                year_depreciation = book_value * rate
                                book_value -= year_depreciation
                                depreciation_amount += year_depreciation
                            # Add partial year depreciation
                            if years_elapsed > int(years_elapsed):
                                partial_depreciation = book_value * rate * (years_elapsed - int(years_elapsed))
                                depreciation_amount += partial_depreciation
                    
                    elif method == 'sum_of_years':
                        # Sum of Years Digits
                        if useful_life > 0:
                            depreciable_amount = depreciation_base - (lot.disposal_price or 0.0)
                            sum_of_years = useful_life * (useful_life + 1) / 2
                            for year in range(int(years_elapsed)):
                                remaining_life = useful_life - year
                                year_depreciation = (remaining_life / sum_of_years) * depreciable_amount
                                depreciation_amount += year_depreciation
                            # Add partial year depreciation
                            if years_elapsed > int(years_elapsed):
                                remaining_life = useful_life - int(years_elapsed)
                                partial_depreciation = (remaining_life / sum_of_years) * depreciable_amount * (years_elapsed - int(years_elapsed))
                                depreciation_amount += partial_depreciation
                    
                    elif method == 'units_of_production':
                        # Units of Production - simplified version
                        # This would typically require production units, but we'll use a simplified calculation
                        depreciable_amount = depreciation_base - (lot.disposal_price or 0.0)
                        if useful_life > 0:
                            # Assume years_elapsed represents "units" in this simplified version
                            depreciation_amount = (depreciable_amount / useful_life) * years_elapsed
            
            # Calculate NBV
            if depreciation_base > 0:
                nbv = depreciation_base - depreciation_amount
                # NBV should not be negative
                nbv = max(0.0, nbv)
            
            lot.depreciation_amount = depreciation_amount
            lot.nbv = nbv
    
    @api.onchange('disposal_price')
    def _onchange_disposal_price(self):
        """Auto-populate disposal_date with current date when disposal_price is entered"""
        if self.disposal_price and not self.disposal_date:
            self.disposal_date = date.today()
