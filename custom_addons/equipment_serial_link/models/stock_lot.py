import logging
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StockLot(models.Model):
    _inherit = 'stock.lot'

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', readonly=True)
    is_vehicle_category = fields.Boolean(
        string='Is Vehicle Category',
        compute='_compute_is_vehicle_category',
    )

    vehicle_license_plate = fields.Char(
        string='License Plate Number',
        help='State/Country + alphanumeric plate number.',
    )
    vehicle_vin = fields.Char(
        string='VIN',
        help='Vehicle Identification Number (17 characters).',
    )
    vehicle_chassis_number = fields.Char(string='Chassis Number')
    vehicle_engine_number = fields.Char(string='Engine Number')
    vehicle_make = fields.Char(string='Make')
    vehicle_model = fields.Char(string='Model')
    vehicle_model_year = fields.Integer(string='Model Year')
    vehicle_body_type = fields.Selection([
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('coupe', 'Coupe'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('bus', 'Bus'),
    ], string='Body Type')
    vehicle_fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('ev', 'EV'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
        ('lpg', 'LPG'),
    ], string='Fuel Type')
    vehicle_transmission_type = fields.Selection([
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('cvt', 'CVT'),
        ('dct', 'DCT'),
    ], string='Transmission Type')
    vehicle_exterior_color = fields.Char(string='Exterior Color')
    vehicle_interior_color = fields.Char(string='Interior Color')
    vehicle_odometer_value = fields.Float(string='Mileage / Odometer Reading')
    vehicle_odometer_unit = fields.Selection([
        ('km', 'Kilometers (km)'),
        ('miles', 'Miles (mi)'),
    ], string='Odometer Unit', default='km')
    vehicle_insurance_policy_number = fields.Char(string='Insurance Policy Number')
    vehicle_insurance_provider = fields.Char(string='Insurance Provider')
    vehicle_insurance_start_date = fields.Date(string='Insurance Start Date')
    vehicle_insurance_end_date = fields.Date(string='Insurance End Date')
    vehicle_insurance_type = fields.Selection([
        ('comprehensive', 'Comprehensive'),
        ('third_party', 'Third-party'),
        ('theft', 'Theft'),
    ], string='Insurance Type')

    @api.depends('product_id', 'product_id.categ_id', 'product_id.categ_id.name', 'product_id.categ_id.complete_name')
    def _compute_is_vehicle_category(self):
        for lot in self:
            category = lot.product_id.categ_id
            category_name = ((category.complete_name or category.name) if category else '') or ''
            lot.is_vehicle_category = 'vehicle' in category_name.lower()

    @api.constrains('vehicle_vin', 'product_id')
    def _check_vehicle_vin(self):
        for lot in self:
            if not lot.is_vehicle_category or not lot.vehicle_vin:
                continue
            vin = (lot.vehicle_vin or '').strip().upper()
            if len(vin) != 17:
                raise ValidationError('VIN must be exactly 17 characters for vehicle assets.')
            if re.search(r'[^A-Z0-9]', vin):
                raise ValidationError('VIN may only contain letters and numbers.')

    @api.constrains('vehicle_license_plate', 'product_id')
    def _check_vehicle_license_plate(self):
        for lot in self:
            if not lot.is_vehicle_category or not lot.vehicle_license_plate:
                continue
            plate = (lot.vehicle_license_plate or '').strip()
            if re.search(r'[^A-Za-z0-9/\-\s]', plate):
                raise ValidationError('License Plate Number may only contain letters, numbers, spaces, "/" or "-".')

    @api.constrains('vehicle_model_year', 'product_id')
    def _check_vehicle_model_year(self):
        current_year = fields.Date.today().year
        for lot in self:
            if not lot.is_vehicle_category or not lot.vehicle_model_year:
                continue
            if lot.vehicle_model_year < 1886 or lot.vehicle_model_year > current_year + 1:
                raise ValidationError('Model Year must be within a valid vehicle year range.')

    @api.constrains('vehicle_insurance_start_date', 'vehicle_insurance_end_date', 'product_id')
    def _check_vehicle_insurance_dates(self):
        for lot in self:
            if not lot.is_vehicle_category:
                continue
            if lot.vehicle_insurance_start_date and lot.vehicle_insurance_end_date and lot.vehicle_insurance_end_date < lot.vehicle_insurance_start_date:
                raise ValidationError('Insurance End Date cannot be before Insurance Start Date.')

    def _get_allowed_serial_ranges(self, company_id):
        """Return own serial ranges, plus parent ranges for child institutions."""
        company = self.env['res.company'].browse(company_id)
        ranges = company.serial_range_ids
        if company.parent_id:
            ranges |= company.parent_id.serial_range_ids
        return ranges

    def _sync_maintenance_equipment(self):
        """Ensure each asset serial has a linked maintenance equipment record."""
        Equipment = self.env['maintenance.equipment'].sudo()
        for lot in self:
            if not lot.name:
                continue

            equipment = lot.equipment_id.sudo() if lot.equipment_id else Equipment.search([
                ('serial_no', '=', lot.name),
                ('company_id', 'in', [lot.company_id.id, False]),
            ], limit=1)

            vals = {
                'name': lot.product_id.display_name or lot.name,
                'serial_no': lot.name,
                'company_id': lot.company_id.id or False,
            }
            if 'product_id' in Equipment._fields and lot.product_id:
                vals['product_id'] = lot.product_id.id

            if equipment:
                equipment.write(vals)
            else:
                equipment = Equipment.create(vals)

            if lot.equipment_id != equipment:
                lot.sudo().write({'equipment_id': equipment.id})

    def create(self, vals_list):
        if self.env.context.get('allow_external_grz_number'):
            return super().create(vals_list)
        
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
                    # Include both own and inherited (parent) ranges.
                    ranges = self._get_allowed_serial_ranges(company_id)
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

        lots = super().create(vals_list)
        lots._sync_maintenance_equipment()
        return lots

    def write(self, vals):
        res = super().write(vals)
        if {'name', 'product_id', 'company_id'} & set(vals.keys()):
            self._sync_maintenance_equipment()
        return res