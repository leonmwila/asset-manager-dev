from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class StockLot(models.Model):
    _inherit = 'stock.lot'

    def create(self, vals_list):
        import re
        from odoo.exceptions import ValidationError
        
        # Validate GRZ Number range for each record
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        for vals in vals_list:
            grz_number = vals.get('grz_number')
            company_id = vals.get('company_id')
            # Validate GRZ Number range if provided
            if grz_number and company_id:
                # Extract last numeric part from GRZ Number
                match = re.search(r'(\d+)$', grz_number)
                if match:
                    grz_num_value = int(match.group(1))
                    # Get all serial ranges for the company
                    ranges = self.env['res.serial.range'].search([('company_id', '=', company_id)])
                    in_range = False
                    for r in ranges:
                        try:
                            start = int(r.start_serial)
                            end = int(r.end_serial)
                            if start <= grz_num_value <= end:
                                in_range = True
                                break
                        except Exception:
                            continue
                    if not in_range:
                        raise ValidationError(f"GRZ Number {grz_number}: last part {grz_num_value} is outside the allowed serial ranges for this company.")
                else:
                    raise ValidationError(f"GRZ Number {grz_number} must end with a number.")
        
        return super().create(vals_list)
    
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', readonly=True)