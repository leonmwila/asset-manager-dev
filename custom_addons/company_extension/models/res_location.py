from odoo import models, fields

class ResProvince(models.Model):
    _name = 'res.province'
    _description = 'Province'

    name = fields.Char(string='Province Name', required=True)
    district_ids = fields.One2many('res.district', 'province_id', string='Districts')

class ResDistrict(models.Model):
    _name = 'res.district'
    _description = 'District'

    name = fields.Char(string='District Name', required=True)
    province_id = fields.Many2one('res.province', string='Province', required=True)