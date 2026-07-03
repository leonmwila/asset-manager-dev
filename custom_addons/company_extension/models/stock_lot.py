from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


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
    condition_state = fields.Selection(
        [
            ('NEW', 'NEW'),
            ('GOOD', 'GOOD'),
            ('FUNCTIONAL', 'FUNCTIONAL'),
            ('BAD', 'BAD'),
            ('NON_FUNCTIONAL', 'NON FUNCTIONAL'),
        ],
        string='Condition',
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
        if self.env.context.get('preserve_donation_grz') and self.grz_number and self.grz_number_b:
            return

        self.grz_number_b = False
        # Ensure available numbers exist for this company
        if self.company_id:
            self.env['grz.available.number'].ensure_numbers_for_company(self.company_id)

    @api.onchange('company_id', 'program_id', 'project_id', 'product_id', 'grz_number_b')
    def _onchange_build_grz_number(self):
        for record in self:
            if record.env.context.get('preserve_donation_grz') and record.grz_number and record.grz_number_b:
                continue

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

    def _resolve_grz_number_b(self, vals):
        """If grz_number is supplied but grz_number_b is not, extract the
        trailing numeric segment from grz_number and look it up in
        grz.available.number so the user never has to supply GRZ Number B
        manually (e.g. during Excel import).

        Example: 'GRZ/SZI/OE/06435587'  →  number_padded '06435587'  →
        number value 6435587  →  grz.available.number for company.
        """
        if self.env.context.get('allow_external_grz_number'):
            return vals

        if vals.get('grz_number_b') or not vals.get('grz_number'):
            return vals

        raw = (vals['grz_number'] or '').strip()
        if not raw:
            return vals

        last_segment = raw.rsplit('/', 1)[-1].strip()
        if not last_segment.isdigit():
            return vals

        try:
            number_int = int(last_segment)
        except ValueError:
            return vals

        company_id = vals.get('company_id')
        if not company_id:
            return vals

        grz_rec = self.env['grz.available.number'].search([
            ('company_id', '=', company_id),
            ('number', '=', number_int),
        ], limit=1)

        if grz_rec:
            vals = dict(vals)
            vals['grz_number_b'] = grz_rec.id
            return vals

        # Number not found — build a helpful error showing the accepted range.
        company = self.env['res.company'].browse(company_id)
        available = self.env['grz.available.number'].search([
            ('company_id', '=', company_id),
            ('is_used', '=', False),
        ], order='number asc')

        if available:
            accepted = '%s – %s' % (
                available[0].number_padded,
                available[-1].number_padded,
            )
            hint = _("Accepted range for %(company)s: %(range)s") % {
                'company': company.name,
                'range': accepted,
            }
        else:
            hint = _("No available GRZ numbers remain for %(company)s.") % {
                'company': company.name,
            }

        raise ValidationError(
            _("GRZ Number '%(grz)s' — suffix '%(suffix)s' is not in the allocated "
              "range for this institution.\n%(hint)s") % {
                'grz': raw,
                'suffix': last_segment,
                'hint': hint,
            }
        )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-link grz_number_b from grz_number and mark as used."""
        vals_list = [self._resolve_grz_number_b(v) for v in vals_list]
        records = super().create(vals_list)
        # Trigger recomputation of is_used for the selected grz_number_b
        for record in records:
            if record.grz_number_b:
                record.grz_number_b._compute_is_used()
        return records

    def write(self, vals):
        """Override write to auto-link grz_number_b from grz_number and update is_used."""
        vals = self._resolve_grz_number_b(vals)
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