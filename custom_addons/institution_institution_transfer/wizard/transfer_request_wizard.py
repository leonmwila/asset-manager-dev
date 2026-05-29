from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InstitutionTransferRequest(models.TransientModel):
    _name = 'institution.transfer.request.wizard'
    _description = 'Institution Transfer Request Wizard'

    dest_company_id = fields.Many2one('res.company', string='Institution', required=True)
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [False, dest_company_id])]")

    quantity = fields.Float(string='Quantity', default=1.0)
    max_qty = fields.Float(string='Max Quantity', readonly=True, compute='_compute_max_qty')
    is_spares = fields.Boolean(string='Is Spares', readonly=True, compute='_compute_max_qty')

    @api.depends_context('active_ids')
    def _compute_max_qty(self):
        lots = self.env['stock.lot'].browse(self.env.context.get('active_ids', [])).filtered('product_id')
        if not lots:
            self.max_qty = 0.0
            self.is_spares = False
            return

        is_spares = all(lot.product_id.type == 'spares' for lot in lots)
        if not is_spares:
            self.max_qty = 1.0
            self.is_spares = False
            self.quantity = 1.0
            return

        quantities = []
        for lot in lots:
            quant = self.env['stock.quant'].search([
                ('lot_id', '=', lot.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0),
            ], limit=1)
            quantities.append(quant.quantity if quant else 0.0)
        self.max_qty = min(quantities) if quantities else 0.0
        self.is_spares = True
        if self.quantity <= 0:
            self.quantity = 1.0
        if self.quantity > self.max_qty:
            self.quantity = self.max_qty
    def action_confirm(self):
        lot_ids = self.env.context.get('active_ids', [])
        if not lot_ids:
            raise UserError(_("No assets selected for transfer."))

        lots = self.env['stock.lot'].browse(lot_ids)
        transfers = []
        for lot in lots:
            quant = self.env['stock.quant'].search([
                ('lot_id', '=', lot.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0),
            ], limit=1)
            if not quant:
                raise UserError(_("No available stock found for asset %s.") % lot.display_name)

            quantity = 1.0
            if lot.product_id.type == 'spares':
                quantity = self.quantity
                if quantity <= 0:
                    raise UserError(_("Quantity must be greater than zero for %s.") % lot.display_name)
                if quantity > quant.quantity:
                    raise UserError(_("Quantity exceeds available stock for %s.") % lot.display_name)

            transfers.append({
                'lot_id': lot.id,
                'source_company_id': quant.location_id.company_id.id or lot.company_id.id,
                'source_location_id': quant.location_id.id,
                'dest_company_id': self.dest_company_id.id,
                'dest_location_id': self.dest_location_id.id,
                'quantity': quantity,
                'state': 'pending',
            })

        self.env['institution.transfer'].create(transfers)
        return {'type': 'ir.actions.act_window_close'}
