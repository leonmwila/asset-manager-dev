from odoo import models, fields, api


class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Override field labels for UI display (must include comodel_name for Many2one fields)
    name = fields.Char(string='Serial Number')
    product_id = fields.Many2one('product.product', string='Asset')
    company_id = fields.Many2one('res.company', string='Institution')
    
    grz_number = fields.Char(string='GRZ Number', required=False)
    grz_number_b = fields.Many2one(
        'grz.available.number',
        string='GRZ Number B',
        help='Select an available GRZ number suffix from the institution\'s allocated range',
        domain="[('company_id', '=', company_id), '|', ('is_used', '=', False), ('id', '=', grz_number_b)]"
    )
    program_id = fields.Many2one('oe.program', string='Program', domain="[('company_id', '=', company_id)]")
    project_id = fields.Many2one('oe.project', string='Project', domain="[('company_id', '=', company_id)]")
    assigned_to = fields.Many2one(
        'hr.employee',
        string='Assigned To',
        domain="[('company_id', '=', company_id)]",
        help="Employee to whom this serial number/equipment is assigned"
    )
    # Related fields from company for export purposes
    province_id = fields.Many2one('res.province', string='Province', related='company_id.province', readonly=True, store=True, help='Province of the company/institution')
    district_id = fields.Many2one('res.district', string='Station', related='company_id.district', readonly=True, store=True, help='District of the company/institution')
    product_model = fields.Char(string='Model', related='product_id.model', readonly=True, store=True, help='Model of the product/asset')
    standard_price = fields.Float(string='Acquisition Price', related='product_id.standard_price', readonly=True, store=True, help='Cost/Acquisition price of the product')
    categ_id = fields.Many2one('product.category', string='Category', related='product_id.categ_id', readonly=True, store=True, help='Product category')
    category_2_id = fields.Many2one('product.category.2', string='Description Category 2', related='product_id.product_tmpl_id.category_2_id', readonly=True, store=True, help='Product Category 2')
    
    # Vehicle-specific fields (only visible when product category is 'Vehicle')
    vehicle_make = fields.Char(string='Make', help='Vehicle manufacturer/make (e.g., Toyota, Ford)')
    engine_no = fields.Char(string='Engine No', help='Vehicle engine number')
    plate_no = fields.Char(string='Plate No', help='Vehicle license plate number')
    is_vehicle = fields.Boolean(string='Is Vehicle', compute='_compute_is_vehicle', store=False, help='True if the product category is Vehicle')

    @api.depends('product_id', 'product_id.categ_id', 'product_id.categ_id.name')
    def _compute_is_vehicle(self):
        """Compute if the product category is Vehicle"""
        for record in self:
            record.is_vehicle = record.product_id and record.product_id.categ_id and record.product_id.categ_id.name.lower() == 'vehicle'
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Clear vehicle fields when product changes and is not a vehicle"""
        # Trigger computation of is_vehicle
        self._compute_is_vehicle()
        if not self.is_vehicle:
            self.vehicle_make = False
            self.engine_no = False
            self.plate_no = False

    @api.onchange('company_id')
    def _onchange_company_id_grz_numbers(self):
        """Reset GRZ Number B when company changes and ensure numbers exist"""
        self.grz_number_b = False
        # Ensure available numbers exist for this company
        if self.company_id:
            self.env['grz.available.number'].ensure_numbers_for_company(self.company_id)

    @api.onchange('company_id', 'program_id', 'project_id', 'product_id', 'grz_number_b')
    def _onchange_build_grz_number(self):
        for record in self:
            if not record.company_id:
                record.grz_number = ''
                continue

            company = record.company_id
            prefix = ''

            # Step 1: Determine prefix based on company_type
            if company.company_type == 'grz':
                prefix = f"GRZ/{company.company_code}/"
            else:
                prefix = f"{company.company_code}/"

            # Step 2: Append program/project/product codes
            middle = ''
            if record.program_id:
                middle += f"{record.program_id.prog_code}/"
                if record.project_id:
                    middle += f"{record.project_id.proj_code}/"
            else:
                # If no program, append product code directly
                if record.product_id:
                    middle += f"{record.product_id.categ_id.category_code or 'NO-CODE'}/"

            # If program but no project, append product code
            if record.program_id and not record.project_id and record.product_id:
                middle += f"{record.product_id.categ_id.category_code or 'NO-CODE'}/"

            # Step 3: Append the selected GRZ Number B suffix (padded number)
            suffix = ''
            if record.grz_number_b:
                suffix = record.grz_number_b.number_padded or ''

            # Combine all parts
            record.grz_number = prefix + middle + suffix

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to mark GRZ number as used"""
        records = super().create(vals_list)
        # Trigger recomputation of is_used for the selected grz_number_b
        for record in records:
            if record.grz_number_b:
                record.grz_number_b._compute_is_used()
        return records

    def write(self, vals):
        """Override write to update is_used status when grz_number_b changes"""
        old_grz_numbers = {rec.id: rec.grz_number_b for rec in self}
        result = super().write(vals)
        if 'grz_number_b' in vals:
            # Recompute for old and new grz_number_b records
            for rec in self:
                old_num = old_grz_numbers.get(rec.id)
                if old_num:
                    old_num._compute_is_used()
                if rec.grz_number_b:
                    rec.grz_number_b._compute_is_used()
        return result

    def unlink(self):
        """Override unlink to mark GRZ number as available again"""
        grz_numbers_to_update = self.mapped('grz_number_b')
        result = super().unlink()
        # Recompute is_used for the freed numbers
        for num in grz_numbers_to_update:
            num._compute_is_used()
        return result