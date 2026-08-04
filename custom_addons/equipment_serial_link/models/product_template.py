import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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

    @api.depends('categ_id', 'categ_id.name', 'categ_id.complete_name')
    def _compute_is_vehicle_category(self):
        for product in self:
            category_name = ((product.categ_id.complete_name or product.categ_id.name) if product.categ_id else '') or ''
            product.is_vehicle_category = 'vehicle' in category_name.lower()

    @api.constrains('vehicle_vin', 'categ_id')
    def _check_vehicle_vin(self):
        for product in self:
            if not product.is_vehicle_category or not product.vehicle_vin:
                continue
            vin = (product.vehicle_vin or '').strip().upper()
            if len(vin) != 17:
                raise ValidationError('VIN must be exactly 17 characters for vehicle products.')
            if re.search(r'[^A-Z0-9]', vin):
                raise ValidationError('VIN may only contain letters and numbers.')

    @api.constrains('vehicle_license_plate', 'categ_id')
    def _check_vehicle_license_plate(self):
        for product in self:
            if not product.is_vehicle_category or not product.vehicle_license_plate:
                continue
            plate = (product.vehicle_license_plate or '').strip()
            if re.search(r'[^A-Za-z0-9/\-\s]', plate):
                raise ValidationError('License Plate Number may only contain letters, numbers, spaces, "/" or "-".')

    @api.constrains('vehicle_model_year', 'categ_id')
    def _check_vehicle_model_year(self):
        current_year = fields.Date.today().year
        for product in self:
            if not product.is_vehicle_category or not product.vehicle_model_year:
                continue
            if product.vehicle_model_year < 1886 or product.vehicle_model_year > current_year + 1:
                raise ValidationError('Model Year must be within a valid vehicle year range.')

    @api.constrains('vehicle_insurance_start_date', 'vehicle_insurance_end_date', 'categ_id')
    def _check_vehicle_insurance_dates(self):
        for product in self:
            if not product.is_vehicle_category:
                continue
            if product.vehicle_insurance_start_date and product.vehicle_insurance_end_date and product.vehicle_insurance_end_date < product.vehicle_insurance_start_date:
                raise ValidationError('Insurance End Date cannot be before Insurance Start Date.')
