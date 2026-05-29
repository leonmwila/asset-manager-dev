from odoo import fields, models, _
from odoo.exceptions import UserError


class RepairSparePartRequest(models.Model):
    _name = 'repair.spare.part.request'
    _description = 'Repair Spare Part Request'
    _order = 'create_date desc'

    name = fields.Char(string='Request Reference', compute='_compute_name', store=True)
    repair_id = fields.Many2one('repair.order', string='Repair Order', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='repair_id.company_id', string='Institution', store=True, readonly=True)
    lot_id = fields.Many2one(related='repair_id.lot_id', string='Asset', store=True, readonly=True)
    product_id = fields.Many2one(related='repair_id.product_id', string='Asset Type', store=True, readonly=True)
    requested_by = fields.Many2one('res.users', string='Technician', required=True, readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approved On', readonly=True)
    collected_by = fields.Many2one('res.users', string='Collected By', readonly=True)
    collected_date = fields.Datetime(string='Collected On', readonly=True)
    technician_signature = fields.Binary(string='Technician Signature', attachment=True)
    technician_signature_name = fields.Char(string='Signed By')
    state = fields.Selection([
        ('approved', 'Approved'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='approved', tracking=True)
    note = fields.Text(string='Notes')
    line_ids = fields.One2many('repair.spare.part.request.line', 'request_id', string='Requested Parts', copy=True)

    def _compute_name(self):
        for request in self:
            request.name = f"SPR/{request.repair_id.name}" if request.repair_id else _('Spare Part Request')

    def action_mark_collected(self):
        for request in self.filtered(lambda r: r.state == 'approved'):
            if not request.technician_signature:
                raise UserError(_("Technician signature is required before marking as collected."))
            request.write({
                'state': 'collected',
                'collected_by': self.env.user.id,
                'collected_date': fields.Datetime.now(),
            })
        return True

    def action_cancel(self):
        self.filtered(lambda r: r.state in ('approved',)).write({'state': 'cancelled'})
        return True


class RepairSparePartRequestLine(models.Model):
    _name = 'repair.spare.part.request.line'
    _description = 'Repair Spare Part Request Line'
    _order = 'id asc'

    request_id = fields.Many2one('repair.spare.part.request', string='Request', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Spare Part', required=True)
    qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unit', required=True)
    repair_move_id = fields.Many2one('stock.move', string='Repair Part Line', readonly=True)
