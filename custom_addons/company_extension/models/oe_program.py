from odoo import models, fields

class OEProgram(models.Model):
    _name = 'oe.program'
    _description = 'Program'

    name = fields.Char(string='Program Name', required=True)
    prog_code = fields.Char(string='Program Code', required=True, size=4)
    description = fields.Text(string='Description')
    project_ids = fields.One2many('oe.project','program_id', string='Related Projects')
    company_id = fields.Many2one('res.company', string='Company/Ministry', required=True, default=lambda self: self.env.company)
