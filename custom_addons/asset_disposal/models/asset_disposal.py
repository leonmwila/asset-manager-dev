from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetDisposal(models.Model):
    _name = 'asset.disposal'
    _description = 'Asset Disposal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', default='New', copy=False, readonly=True)
    asset_id = fields.Many2one('stock.lot', string='Asset', required=True, ondelete='restrict')
    product_id = fields.Many2one(related='asset_id.product_id', string='Product', store=True, readonly=True)
    company_id = fields.Many2one(related='asset_id.company_id', string='Institution', store=True, readonly=True)

    method = fields.Selection([
        ('discard', 'Discarded/Dumped/Thrown'),
        ('donate_internal', 'Donated (Internal)'),
        ('donate_external', 'Donated (External)'),
        ('sold', 'Sold'),
    ], string='Method', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)

    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approved On', readonly=True)

    recipient_company_id = fields.Many2one('res.company', string='Recipient Institution')
    recipient_partner_id = fields.Many2one('res.partner', string='Recipient')
    recipient_name = fields.Char(string='Recipient (External)')

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    sale_price = fields.Monetary(string='Sale Price')

    note = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('asset.disposal') or 'New'
        return super().create(vals_list)

    def action_approve(self):
        for record in self:
            if record.state != 'draft':
                continue
            record._validate_before_approve()
            record.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
        return True

    def action_done(self):
        for record in self:
            if record.state == 'draft':
                record.action_approve()
            if record.state != 'approved':
                continue
            record._apply_disposal()
            record.state = 'done'
        return True

    def action_cancel(self):
        self.filtered(lambda r: r.state in ('draft', 'approved')).write({'state': 'cancelled'})
        return True

    def action_set_to_draft(self):
        self.filtered(lambda r: r.state == 'cancelled').write({'state': 'draft'})
        return True

    def _validate_before_approve(self):
        if not self.asset_id:
            raise UserError(_('Asset is required.'))
        if self.asset_id.asset_state == 'disposed':
            raise UserError(_('This asset is already disposed.'))
        if self.method == 'donate_internal' and not self.recipient_company_id:
            raise UserError(_('Recipient institution is required for internal donation.'))
        if self.method == 'donate_internal' and self.recipient_company_id == self.asset_id.company_id:
            raise UserError(_('Recipient institution must be different from the current institution.'))
        if self.method in ('donate_external', 'sold') and not (self.recipient_partner_id or self.recipient_name):
            raise UserError(_('Recipient is required for external donation or sale.'))
        if self.method == 'sold' and (self.sale_price or 0.0) <= 0.0:
            raise UserError(_('Sale price must be greater than zero.'))

    def _apply_disposal(self):
        self.ensure_one()
        asset = self.asset_id
        if self.method == 'donate_internal':
            self.env['asset.donation'].create({
                'disposal_id': self.id,
                'asset_id': asset.id,
                'recipient_company_id': self.recipient_company_id.id,
                'requested_by': self.requested_by.id,
                'note': self.note or False,
            })
            asset.message_post(body=_('Asset donated internally via disposal %s.') % self.name)

        if self.method == 'sold':
            self._create_sale_order_and_invoice()

        asset.write({
            'asset_state': 'disposed',
            'disposal_method': self.method,
            'disposal_date': fields.Date.today(),
            'disposal_record_id': self.id,
            'active': False,
        })
        asset.message_post(body=_('Asset disposed via %s (ref %s).') % (self.method, self.name))

    def _create_sale_order_and_invoice(self):
        asset = self.asset_id
        partner = self.recipient_partner_id
        if not partner:
            return

        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'company_id': asset.company_id.id,
            'origin': self.name,
        })

        line_name = 'Asset: %s | Serial: %s' % (asset.product_id.display_name, asset.name)
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': asset.product_id.id,
            'name': line_name,
            'product_uom_qty': 1.0,
            'product_uom': asset.product_id.uom_id.id,
            'price_unit': self.sale_price,
        })

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_origin': self.name,
            'invoice_user_id': self.env.user.id,
            'company_id': asset.company_id.id,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': line_name,
                'product_id': asset.product_id.id,
                'quantity': 1.0,
                'price_unit': self.sale_price,
                'tax_ids': [(6, 0, asset.product_id.taxes_id.ids)] if asset.product_id.taxes_id else False,
            })],
        }
        invoice = self.env['account.move'].create(invoice_vals)

        self.sale_order_id = order.id
        self.invoice_id = invoice.id
