from odoo import models, fields, api

class OEProject(models.Model):
    _name = 'oe.project'
    _description = 'OE Project'

    name = fields.Char(string='Project Name', required=True)
    proj_code = fields.Char(string='Project Code', required=True, size=6)
    description = fields.Text(string='Description')
    program_id = fields.Many2one('oe.program', string='Program', ondelete='set null')

    company_id = fields.Many2one('res.company', string='Company', required=True, compute='_compute_company_id', store=True, readonly=False)

    @api.depends('program_id')
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = rec.program_id.company_id if rec.program_id else False
