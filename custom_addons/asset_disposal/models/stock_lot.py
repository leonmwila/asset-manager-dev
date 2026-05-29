from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    active = fields.Boolean(default=True)

    asset_state = fields.Selection([
        ('active', 'Active'),
        ('disposed', 'Disposed'),
    ], string='Asset State', default='active', tracking=True)

    disposal_method = fields.Selection([
        ('discard', 'Discarded/Dumped/Thrown'),
        ('donate_internal', 'Donated (Internal)'),
        ('donate_external', 'Donated (External)'),
        ('sold', 'Sold'),
    ], string='Disposal Method', tracking=True)

    disposal_date = fields.Date(string='Disposal Date', tracking=True)
    disposal_record_id = fields.Many2one('asset.disposal', string='Disposal Record', readonly=True)

    disposal_ids = fields.One2many('asset.disposal', 'asset_id', string='Disposals')
    disposal_count = fields.Integer(compute='_compute_disposal_count')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        donation_id = self.env.context.get('donation_id')
        if donation_id:
            donation = self.env['asset.donation'].browse(donation_id)
            if donation and donation.state == 'pending':
                donation.write({'state': 'accepted', 'new_lot_id': records[:1].id})
        return records

    @api.depends('disposal_ids')
    def _compute_disposal_count(self):
        for lot in self:
            lot.disposal_count = len(lot.disposal_ids)

    @api.depends('product_id.company_id')
    def _compute_company_id(self):
        donation_company_id = self.env.context.get('donation_company_id')
        donation_company = self.env['res.company'].browse(donation_company_id) if donation_company_id else False
        for lot in self:
            if donation_company and not lot.product_id.company_id:
                lot.company_id = donation_company
                continue
            if self.env.company in lot.product_id.company_id.all_child_ids and lot.product_id.company_id not in self.env.companies:
                lot.company_id = self.env.company
            else:
                lot.company_id = lot.product_id.company_id

    def action_open_disposals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asset Disposals',
            'res_model': 'asset.disposal',
            'view_mode': 'list,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {
                'default_asset_id': self.id,
            },
        }
