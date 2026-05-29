from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetDonation(models.Model):
    _name = 'asset.donation'
    _description = 'Asset Donation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', default='New', copy=False, readonly=True)
    disposal_id = fields.Many2one('asset.disposal', string='Disposal', ondelete='set null')
    asset_id = fields.Many2one('stock.lot', string='Asset', required=True, ondelete='restrict')
    product_id = fields.Many2one(related='asset_id.product_id', string='Product', store=True, readonly=True)
    source_company_id = fields.Many2one(related='asset_id.company_id', string='Source Institution', store=True, readonly=True)
    recipient_company_id = fields.Many2one('res.company', string='Recipient Institution', required=True)

    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, readonly=True)

    state = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], default='pending', tracking=True)

    new_lot_id = fields.Many2one('stock.lot', string='New Asset', readonly=True)
    note = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('asset.donation') or 'New'
        return super().create(vals_list)

    def action_accept(self):
        self.ensure_one()
        if self.state != 'pending':
            return False
        if not self.recipient_company_id:
            raise UserError(_('Recipient institution is required.'))
        ctx = dict(self.env.context)
        defaults = self._prepare_new_lot_vals()
        for key, value in defaults.items():
            ctx['default_%s' % key] = value
        ctx['donation_id'] = self.id
        ctx['donation_company_id'] = self.recipient_company_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Asset From Donation'),
            'res_model': 'stock.lot',
            'view_mode': 'form',
            'target': 'current',
            'context': ctx,
        }

    def action_reject(self):
        self.filtered(lambda r: r.state == 'pending').write({'state': 'rejected'})
        return True

    def _prepare_new_lot_vals(self):
        self.ensure_one()
        lot = self.asset_id
        excluded = {
            'id', 'display_name', 'create_uid', 'create_date', 'write_uid', 'write_date',
            'company_id', 'asset_state', 'disposal_method', 'disposal_date',
            'disposal_record_id', 'disposal_ids', 'disposal_count',
            'quant_ids', 'product_qty', 'location_id', 'delivery_ids', 'delivery_count',
            'partner_ids', 'lot_properties', 'ref',
        }
        fields_to_copy = []
        for field_name, field in lot._fields.items():
            if not field.store or field.compute or field.related:
                continue
            if field_name in excluded:
                continue
            fields_to_copy.append(field_name)
        data = lot.read(fields_to_copy)[0] if fields_to_copy else {}
        data.pop('id', None)
        data['product_id'] = lot.product_id.id
        data['company_id'] = self.recipient_company_id.id
        if 'name' in lot._fields and not data.get('name'):
            data['name'] = lot.name
        if 'grz_number' in lot._fields:
            data['grz_number'] = False
        if 'grz_number_b' in lot._fields:
            data['grz_number_b'] = False
        if 'asset_state' in lot._fields:
            data['asset_state'] = 'active'
        if 'disposal_method' in lot._fields:
            data['disposal_method'] = False
        if 'disposal_date' in lot._fields:
            data['disposal_date'] = False
        if 'disposal_record_id' in lot._fields:
            data['disposal_record_id'] = False
        return data
