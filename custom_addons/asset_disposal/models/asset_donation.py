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
        donation = self.sudo()
        if donation.state != 'pending':
            return False
        if not donation.recipient_company_id:
            raise UserError(_('Recipient institution is required.'))

        vals = donation._prepare_new_lot_vals()
        create_ctx = dict(self.env.context)
        create_ctx.update({
            'donation_id': donation.id,
            'donation_company_id': donation.recipient_company_id.id,
            'preserve_donation_grz': True,
            # Donated serials may carry a GRZ number outside the recipient
            # institution's allocated range. Keep GRZ Number B empty.
            'allow_external_grz_number': True,
        })

        self.env['stock.lot'].with_context(create_ctx).sudo().create(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_reject(self):
        self.filtered(lambda r: r.state == 'pending').write({'state': 'rejected'})
        return True

    def _prepare_new_lot_vals(self):
        self.ensure_one()
        donation = self.sudo()
        lot = donation.asset_id
        # Use a conservative whitelist to avoid bringing cross-company linked
        # relation values into defaults during donation acceptance.
        data = {
            'name': lot.name,
            'product_id': lot.product_id.id,
            'company_id': donation.recipient_company_id.id,
        }

        optional_simple_fields = [
            'program_id', 'project_id', 'assigned_to', 'condition_state',
            'vehicle_make', 'engine_no', 'plate_no', 'department_id',
            'acquisition_date', 'supplier_id', 'fair_value', 'lot_acquisition_price',
            'depreciation_amount', 'nbv', 'disposal_price',
        ]
        for field_name in optional_simple_fields:
            if field_name in lot._fields:
                value = lot[field_name]
                data[field_name] = value.id if getattr(value, 'id', False) else value

        if 'grz_number' in lot._fields:
            data['grz_number'] = lot.grz_number or False
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
