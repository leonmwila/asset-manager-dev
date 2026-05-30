from odoo import _, api, fields, models


class StockAllocationFromNoneJob(models.Model):
    _name = 'stock.allocation.from.none.job'
    _description = 'Stock Allocation from None Job'
    _order = 'create_date desc'

    name = fields.Char(required=True, default=lambda self: _('Stock Allocation Job'))
    user_id = fields.Many2one('res.users', string='Requested By', required=True, default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', string='Institution', related='location_id.company_id', store=True, readonly=True)
    location_id = fields.Many2one('stock.location', string='Destination Location', required=True, readonly=True)
    lot_ids = fields.Many2many('stock.lot', string='Serials', readonly=True)
    total_count = fields.Integer(string='Total', readonly=True)
    success_count = fields.Integer(string='Succeeded', readonly=True)
    failed_count = fields.Integer(string='Failed', readonly=True)
    skipped_count = fields.Integer(string='Skipped', readonly=True)
    error_log = fields.Text(string='Errors', readonly=True)
    state = fields.Selection(
        [
            ('queued', 'Queued'),
            ('running', 'Running'),
            ('done', 'Done'),
            ('partial', 'Partial'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='queued',
        required=True,
        readonly=True,
    )

    def _send_popup(self, title, message, notif_type='info'):
        self.ensure_one()
        if not self.user_id or not self.user_id.partner_id:
            return
        self.env['bus.bus']._sendone(
            self.user_id.partner_id,
            'simple_notification',
            {
                'title': title,
                'message': message,
                'type': notif_type,
                'sticky': False,
            },
        )

    def _run_job(self):
        self.ensure_one()
        if self.state not in ('queued', 'running'):
            return

        self.write({'state': 'running'})

        success_count = 0
        failed_count = 0
        skipped_count = 0
        errors = []

        for lot in self.lot_ids:
            try:
                if lot.company_id and self.location_id.company_id and lot.company_id != self.location_id.company_id:
                    skipped_count += 1
                    errors.append(
                        _('%s skipped: company mismatch (%s -> %s).')
                        % (lot.display_name, lot.company_id.display_name, self.location_id.display_name)
                    )
                    continue

                existing_quant = self.env['stock.quant'].search([
                    ('lot_id', '=', lot.id),
                    ('location_id.usage', '=', 'internal'),
                    ('quantity', '>', 0),
                ], limit=1)
                if existing_quant:
                    skipped_count += 1
                    continue

                self.env['stock.quant']._update_available_quantity(
                    lot.product_id,
                    self.location_id,
                    1.0,
                    lot_id=lot,
                )
                success_count += 1
            except Exception as exc:
                failed_count += 1
                errors.append(_('%s failed: %s') % (lot.display_name, str(exc)))

        if success_count and not failed_count and not skipped_count:
            state = 'done'
            notif_type = 'success'
            title = _('Stock Allocation Completed')
        elif success_count:
            state = 'partial'
            notif_type = 'warning'
            title = _('Stock Allocation Partially Completed')
        else:
            state = 'failed'
            notif_type = 'danger'
            title = _('Stock Allocation Failed')

        self.write({
            'state': state,
            'success_count': success_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
            'error_log': '\n'.join(errors[:200]),
        })

        self._send_popup(
            title,
            _('Processed %s serials. Succeeded: %s, Failed: %s, Skipped: %s.')
            % (self.total_count, success_count, failed_count, skipped_count),
            notif_type=notif_type,
        )

    @api.model
    def _cron_process_queued_jobs(self):
        jobs = self.search([('state', '=', 'queued')], order='create_date asc', limit=3)
        for job in jobs:
            job._run_job()
