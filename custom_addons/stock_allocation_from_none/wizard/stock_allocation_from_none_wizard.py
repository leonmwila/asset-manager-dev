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

        job = self.env['stock.allocation.from.none.job'].create({
            'name': _('Allocate %s Serials to %s') % (len(self.lot_ids), self.location_id.display_name),
            'user_id': self.env.user.id,
            'location_id': self.location_id.id,
            'lot_ids': [(6, 0, self.lot_ids.ids)],
            'total_count': len(self.lot_ids),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Allocation Queued'),
                'message': _('Job %s is running in the background. You will receive a popup when done.') % job.display_name,
                'type': 'info',
                'sticky': False,
            },
        }
