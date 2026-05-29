from odoo import models, fields, api


class GrzAvailableNumber(models.Model):
    _name = 'grz.available.number'
    _description = 'Available GRZ Number'
    _order = 'number'

    name = fields.Char(string='Number', compute='_compute_name', store=True)
    number = fields.Integer(string='Number Value', required=True)
    number_padded = fields.Char(string='Padded Number', compute='_compute_number_padded', store=True)
    company_id = fields.Many2one('res.company', string='Company/Institution', required=True, ondelete='cascade')
    serial_range_id = fields.Many2one('res.serial.range', string='Serial Range', required=True, ondelete='cascade')
    is_used = fields.Boolean(string='Is Used', compute='_compute_is_used', store=True)

    _sql_constraints = [
        ('unique_number_per_company', 'unique(number, company_id)', 'Each number must be unique per company!')
    ]

    @api.depends('number')
    def _compute_number_padded(self):
        for record in self:
            # Pad to 7 digits with leading zeros (e.g., 311401 -> 0311401)
            record.number_padded = str(record.number).zfill(7)

    @api.depends('number_padded')
    def _compute_name(self):
        for record in self:
            record.name = record.number_padded

    @api.depends('company_id', 'number_padded')
    def _compute_is_used(self):
        """Check if this number is already used in a stock.lot for this company"""
        for record in self:
            if not record.company_id or not record.number_padded:
                record.is_used = False
                continue
            
            # Search for lots with this number suffix for this company
            # Check both with the padded number and the raw number to catch all cases
            used_lot = self.env['stock.lot'].search([
                ('company_id', '=', record.company_id.id),
                ('grz_number_b', '=', record.id)
            ], limit=1)
            
            record.is_used = bool(used_lot)

    @api.model
    def generate_numbers_for_range(self, serial_range):
        """Generate available number records for a serial range for the parent company"""
        if not serial_range or not serial_range.company_id:
            return
        
        try:
            start = int(serial_range.start_serial)
            end = int(serial_range.end_serial)
        except (ValueError, TypeError):
            return
        
        # Generate for the parent company (owner of range)
        self._generate_numbers_for_company(serial_range, serial_range.company_id, start, end)
        
        # Also generate for all child companies
        child_companies = self.env['res.company'].search([
            ('parent_id', '=', serial_range.company_id.id)
        ])
        for child in child_companies:
            self._generate_numbers_for_company(serial_range, child, start, end)

    def _generate_numbers_for_company(self, serial_range, company, start, end):
        """Generate numbers for a specific company within a range"""
        existing_numbers = self.search([
            ('serial_range_id', '=', serial_range.id),
            ('company_id', '=', company.id)
        ]).mapped('number')
        
        numbers_to_create = []
        for num in range(start, end + 1):
            if num not in existing_numbers:
                numbers_to_create.append({
                    'number': num,
                    'company_id': company.id,
                    'serial_range_id': serial_range.id,
                })
        
        if numbers_to_create:
            self.create(numbers_to_create)

    @api.model
    def ensure_numbers_for_company(self, company):
        """Ensure numbers exist for a company based on its serial ranges (or parent's)"""
        if not company:
            return
        
        # Get the serial ranges - either own or parent's
        if company.parent_id:
            serial_ranges = company.parent_id.serial_range_ids
        else:
            serial_ranges = company.serial_range_ids
        
        for sr in serial_ranges:
            try:
                start = int(sr.start_serial)
                end = int(sr.end_serial)
            except (ValueError, TypeError):
                continue
            
            self._generate_numbers_for_company(sr, company, start, end)

    def refresh_used_status(self):
        """Manually refresh the is_used status for all records"""
        self._compute_is_used()

    @api.model
    def generate_all_missing_numbers(self):
        """Generate numbers for all serial ranges and all companies - utility method"""
        serial_ranges = self.env['res.serial.range'].search([])
        for sr in serial_ranges:
            self.generate_numbers_for_range(sr)
        return True
