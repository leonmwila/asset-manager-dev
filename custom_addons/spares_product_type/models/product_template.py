from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type = fields.Selection(
        selection_add=[('spares', 'Spares')],
        ondelete={'spares': 'set default'},
    )

    part_number = fields.Char(
        string='Part Number',
        help='Manufacturer or internal part number for spares.'
    )

    @api.onchange('type')
    def _onchange_type_set_spares_storable(self):
        if self.type == 'spares' and 'is_storable' in self._fields:
            self.is_storable = True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('type') == 'spares' and 'is_storable' not in vals and 'is_storable' in self._fields:
                vals['is_storable'] = True
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('type') == 'spares' and 'is_storable' not in vals and 'is_storable' in self._fields:
            vals = dict(vals)
            vals['is_storable'] = True
        return super().write(vals)
