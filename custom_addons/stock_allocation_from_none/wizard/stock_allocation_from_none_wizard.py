from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockAllocationFromNoneWizard(models.TransientModel):
    _name = 'stock.allocation.from.none.wizard'
    _description = 'Stock Allocation from None Wizard'

    location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=True,
        domain="[('usage', '=', 'internal')]",
        help='Choose the internal stock location where the selected serials will be placed.',
    )
    lot_ids = fields.Many2many(
        'stock.lot',
        string='Serials',
        readonly=True,
    )
    serial_count = fields.Integer(string='Serial Count', compute='_compute_serial_count')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')
        if active_model == 'stock.lot' and active_ids:
            defaults['lot_ids'] = [(6, 0, active_ids)]
        return defaults

    @api.depends('lot_ids')
    def _compute_serial_count(self):
        for wizard in self:
            wizard.serial_count = len(wizard.lot_ids)

    def action_allocate(self):
        self.ensure_one()
        if not self.lot_ids:
            raise UserError(_('Select at least one serial number to allocate.'))
        if not self.location_id:
            raise UserError(_('Please choose a destination location.'))

        self.location_id.check_access_rights('read')
        self.location_id.check_access_rule('read')

        already_stocked = []
        allocated = []

        for lot in self.lot_ids:
            if lot.company_id and self.location_id.company_id and lot.company_id != self.location_id.company_id:
                raise UserError(
                    _('Serial %s belongs to %s and cannot be allocated to %s.')
                    % (lot.display_name, lot.company_id.display_name, self.location_id.display_name)
                )

            existing_quant = self.env['stock.quant'].search([
                ('lot_id', '=', lot.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0),
            ], limit=1)
            if existing_quant:
                already_stocked.append('%s (%s)' % (lot.display_name, existing_quant.location_id.display_name))
                continue

            self.env['stock.quant']._update_available_quantity(
                lot.product_id,
                self.location_id,
                1.0,
                lot_id=lot,
            )
            allocated.append(lot.display_name)

        if already_stocked and not allocated:
            raise UserError(
                _('All selected serials already have stock in an internal location: %s')
                % ', '.join(already_stocked)
            )

        if already_stocked:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Partial Allocation'),
                    'message': _('Allocated: %s. Skipped already stocked serials: %s') % (
                        ', '.join(allocated) or '-',
                        ', '.join(already_stocked),
                    ),
                    'type': 'warning',
                    'sticky': False,
                },
            }

        return {'type': 'ir.actions.act_window_close'}
