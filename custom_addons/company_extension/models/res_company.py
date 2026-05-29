from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    company_code = fields.Char(string='Company Code', size=5, help='A unique code to identify the company.', required=False)
    province = fields.Many2one('res.province', string='Province')
    district = fields.Many2one('res.district', string='District')
    company_type = fields.Selection([
        ('grz', 'Government'),
        ('council', 'Council'),
        ('private', 'Private'),
        ('ngo', 'NGO'),
        ('parastatal', 'Parastatal')
    ], string='Company Type')
    program_ids = fields.One2many('oe.program', 'company_id', string='Programs', required=False)
    project_ids = fields.One2many('oe.project', 'company_id', string='Projects', required=False)
    serial_range_ids = fields.One2many('res.serial.range', 'company_id', string='Serial Ranges', required=False)
    parent_serial_range_ids = fields.Many2many(
        'res.serial.range', 
        compute='_compute_parent_serial_ranges',
        string='Parent Company Serial Ranges',
        readonly=True
    )
    
    @api.depends('parent_id', 'parent_id.serial_range_ids')
    def _compute_parent_serial_ranges(self):
        """Compute serial ranges from parent company for child companies"""
        for company in self:
            if company.parent_id:
                company.parent_serial_range_ids = company.parent_id.serial_range_ids
            else:
                company.parent_serial_range_ids = False

