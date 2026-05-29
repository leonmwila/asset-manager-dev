from odoo import models, fields, api

class ResSerialRange(models.Model):
    _name = 'res.serial.range'
    _description = 'Serial Range'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    start_serial = fields.Char(string='Start Serial', required=True)
    end_serial = fields.Char(string='End Serial', required=True)
    available_number_ids = fields.One2many('grz.available.number', 'serial_range_id', string='Available Numbers')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            self.env['grz.available.number'].generate_numbers_for_range(record)
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'start_serial' in vals or 'end_serial' in vals:
            for record in self:
                self.env['grz.available.number'].generate_numbers_for_range(record)
        return result