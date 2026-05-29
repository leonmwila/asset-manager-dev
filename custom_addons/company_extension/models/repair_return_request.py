from odoo import fields, models, _
from odoo.exceptions import UserError


class RepairReturnRequest(models.Model):
    _name = 'repair.return.request'
    _description = 'Repair Return Request'
    _order = 'create_date desc'

    repair_id = fields.Many2one('repair.order', string='Repair Order', required=True, ondelete='cascade')
    lot_id = fields.Many2one(related='repair_id.lot_id', string='Asset', store=True, readonly=True)
    product_id = fields.Many2one(related='repair_id.product_id', string='Product', store=True, readonly=True)
    source_company_id = fields.Many2one(related='repair_id.company_id', string='Current Institution', store=True, readonly=True)
    dest_company_id = fields.Many2one('res.company', string='Return To Institution', required=True)
    dest_location_id = fields.Many2one('stock.location', string='Destination Location', readonly=True)
    state = fields.Selection(
        [('pending', 'Pending Approval'), ('approved', 'Approved'), ('cancelled', 'Cancelled')],
        default='pending',
        string='Status',
        tracking=True,
    )
    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approved On', readonly=True)

    def action_approve(self):
        for request in self.filtered(lambda r: r.state == 'pending'):
            request.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            if request.repair_id:
                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'repair_operation'),
                    ('company_id', '=', request.dest_company_id.id),
                ], limit=1)
                if not picking_type:
                    raise UserError(_("No repair operation type found for %s.") % request.dest_company_id.display_name)
                request.repair_id.write({
                    'state': 'returned',
                    'company_id': request.dest_company_id.id,
                    'picking_type_id': picking_type.id,
                })
        return True

    def action_cancel(self):
        self.filtered(lambda r: r.state == 'pending').write({'state': 'cancelled'})
        return True

    # No stock transfer is performed; only the repair order institution/state changes.
