from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    part_request_ids = fields.One2many(
        'maintenance.part.request',
        'maintenance_request_id',
        string='Part Requests',
    )
    part_request_count = fields.Integer(
        string='Part Requests',
        compute='_compute_part_request_count',
    )

    def _compute_part_request_count(self):
        for request in self:
            request.part_request_count = len(request.part_request_ids)

    def action_submit_parts_request(self):
        self.ensure_one()
        if not self.part_line_ids:
            raise UserError(_('Add parts in the Parts tab before submitting a request.'))

        line_vals = []
        for line in self.part_line_ids:
            if line.qty <= 0:
                continue
            line_vals.append((0, 0, {
                'product_id': line.product_id.id,
                'qty': line.qty,
                'product_uom_id': line.product_uom_id.id,
                'note': line.note,
            }))

        if not line_vals:
            raise UserError(_('Requested part quantities must be greater than zero.'))

        approver = self.user_id or self.env.user
        source_company = self.company_id or self.env.company
        source_location = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', '=', source_company.id),
        ], limit=1)
        if not source_location:
            raise UserError(_('No internal supplying location found for %s. Configure one before submitting parts requests.') % source_company.display_name)

        part_request = self.env['maintenance.part.request'].create({
            'maintenance_request_id': self.id,
            'approver_id': approver.id,
            'source_company_id': source_company.id,
            'source_location_id': source_location.id,
            'line_ids': line_vals,
        })
        part_request.action_submit()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.part.request',
            'res_id': part_request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_part_requests(self):
        self.ensure_one()
        action = self.env.ref('maintenance_parts_workflow.action_maintenance_part_request').read()[0]
        action['domain'] = [('maintenance_request_id', '=', self.id)]
        action['context'] = {
            'default_maintenance_request_id': self.id,
            'default_approver_id': self.user_id.id,
        }
        return action


class MaintenancePartRequest(models.Model):
    _name = 'maintenance.part.request'
    _description = 'Maintenance Part Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, copy=False, default='New', readonly=True)
    maintenance_request_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance Request',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    company_id = fields.Many2one(related='maintenance_request_id.company_id', string='Institution', store=True, readonly=True)
    equipment_id = fields.Many2one(related='maintenance_request_id.equipment_id', string='Equipment', store=True, readonly=True)
    source_company_id = fields.Many2one(
        'res.company',
        string='Supplying Institution',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string='Supplying Location',
        domain="[('usage', '=', 'internal'), ('company_id', '=', source_company_id)]",
        tracking=True,
    )
    picking_id = fields.Many2one('stock.picking', string='Issue Transfer', readonly=True, copy=False)
    requested_by = fields.Many2one('res.users', string='Requested By', required=True, default=lambda self: self.env.user, tracking=True)
    approver_id = fields.Many2one('res.users', string='Approver', tracking=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, tracking=True)
    approved_date = fields.Datetime(string='Approved On', readonly=True, tracking=True)
    collected_by = fields.Many2one('res.users', string='Collected By', readonly=True, tracking=True)
    collected_date = fields.Datetime(string='Collected On', readonly=True, tracking=True)
    technician_signature = fields.Binary(string='Technician Signature', attachment=True)
    technician_signature_name = fields.Char(string='Signed By')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'Waiting Approval'),
        ('approved', 'Ready for Collection'),
        ('rejected', 'Rejected'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    note = fields.Text(string='Notes')
    line_ids = fields.One2many('maintenance.part.request.line', 'part_request_id', string='Requested Parts', copy=True)

    def action_open_picking(self):
        self.ensure_one()
        if not self.picking_id:
            raise UserError(_('No stock transfer has been generated yet for this request.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': self.picking_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_for_signature(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.part.request',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.part.request') or 'New'
            if not vals.get('source_company_id') and vals.get('maintenance_request_id'):
                maintenance_request = self.env['maintenance.request'].browse(vals['maintenance_request_id'])
                vals['source_company_id'] = maintenance_request.company_id.id or self.env.company.id
        return super().create(vals_list)

    @api.onchange('maintenance_request_id')
    def _onchange_maintenance_request_id_set_source_company(self):
        if self.maintenance_request_id and not self.source_company_id:
            self.source_company_id = self.maintenance_request_id.company_id

    @api.onchange('source_company_id')
    def _onchange_source_company_id(self):
        if self.source_location_id and self.source_location_id.company_id != self.source_company_id:
            self.source_location_id = False

        if self.source_company_id and not self.source_location_id:
            location = self.env['stock.location'].search([
                ('usage', '=', 'internal'),
                ('company_id', '=', self.source_company_id.id),
            ], limit=1)
            self.source_location_id = location

    def _check_approver_rights(self):
        if not self.env.user.has_group('maintenance.group_equipment_manager'):
            raise AccessError(_('Only maintenance managers can approve or reject part requests.'))

    def action_submit(self):
        for request in self:
            if request.state not in ('draft', 'rejected'):
                continue
            if not request.line_ids:
                raise UserError(_('Add at least one part line before submitting for approval.'))
            if not request.approver_id:
                raise UserError(_('Set an approver before submitting this request.'))
            if not request.source_company_id:
                raise UserError(_('Set the supplying institution before submitting this request.'))
            if not request.source_location_id:
                raise UserError(_('Set the supplying location before submitting this request.'))
            if request.source_location_id.company_id != request.source_company_id:
                raise UserError(_('Supplying location must belong to the selected supplying institution.'))

            request.write({'state': 'to_approve'})
            request.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=request.approver_id.id,
                note=_('A maintenance part request requires your approval.'),
            )

    def _get_issue_picking_type(self):
        company = self.source_company_id or self.company_id or self.env.company
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            '|',
            ('company_id', '=', company.id),
            ('warehouse_id.company_id', '=', company.id),
        ], limit=1)
        if not picking_type:
            raise UserError(_('No outgoing picking operation type is configured for %s.') % company.display_name)
        return picking_type

    def _get_issue_source_location(self):
        if self.source_location_id:
            return self.source_location_id

        picking_type = self._get_issue_picking_type()
        if picking_type.warehouse_id and picking_type.warehouse_id.lot_stock_id:
            return picking_type.warehouse_id.lot_stock_id
        company = self.source_company_id or self.company_id or self.env.company
        source_location = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', '=', company.id),
        ], limit=1)
        if not source_location:
            raise UserError(_('No internal stock location could be found for this company.'))
        return source_location

    def _get_issue_destination_location(self):
        return self.env.ref('stock.stock_location_customers')

    def _ensure_issue_picking(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda line: line.qty > 0)
        if not lines:
            raise UserError(_('Add at least one part line before creating the stock issue transfer.'))

        source_location = self._get_issue_source_location()
        dest_location = self._get_issue_destination_location()
        picking_type = self._get_issue_picking_type()
        company = self.source_company_id or self.company_id or self.env.company

        if source_location.company_id and source_location.company_id != company:
            raise UserError(_('Supplying location must belong to the selected supplying institution.'))

        if self.picking_id:
            existing_picking = self.picking_id.sudo()
            is_mismatch = (
                existing_picking.company_id != company
                or existing_picking.location_id != source_location
                or existing_picking.location_dest_id != dest_location
                or existing_picking.picking_type_id != picking_type
            )
            if not is_mismatch:
                return existing_picking

            if existing_picking.state == 'done':
                raise UserError(_(
                    'Existing transfer %s is already done and does not match the current supplying institution/location. '
                    'Create a new part request for the new source configuration.'
                ) % existing_picking.display_name)

            if existing_picking.state != 'cancel':
                existing_picking.button_cancel()
            self.picking_id = False

        partner = self.requested_by.partner_id or self.maintenance_request_id.user_id.partner_id
        partner_id = False
        if partner and (not partner.company_id or partner.company_id == company):
            partner_id = partner.id

        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'company_id': company.id,
            'partner_id': partner_id,
            'origin': self.name,
        })

        if not self.source_location_id:
            self.source_location_id = source_location

        for line in lines:
            self.env['stock.move'].sudo().create({
                'description_picking': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'product_uom': line.product_uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
                'picking_id': picking.id,
            })

        picking.action_confirm()
        picking.action_assign()
        self.picking_id = picking.id
        return picking

    def _cancel_issue_picking(self):
        for request in self.filtered(lambda record: record.picking_id and record.picking_id.state not in ('done', 'cancel')):
            request.picking_id.sudo().button_cancel()

    def action_approve(self):
        self._check_approver_rights()
        for request in self:
            if request.state != 'to_approve':
                continue
            request._ensure_issue_picking()
            request.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            request.activity_unlink(['mail.mail_activity_data_todo'])

    def action_reject(self):
        self._check_approver_rights()
        for request in self:
            if request.state != 'to_approve':
                continue
            request._cancel_issue_picking()
            request.write({'state': 'rejected'})
            request.activity_unlink(['mail.mail_activity_data_todo'])

    def action_mark_collected(self):
        move_line_model = self.env['stock.move.line']
        if 'qty_done' in move_line_model._fields:
            done_qty_field = 'qty_done'
        elif 'quantity' in move_line_model._fields:
            done_qty_field = 'quantity'
        else:
            raise UserError(_('Unable to find a supported done quantity field on stock move lines.'))

        for request in self:
            if request.state != 'approved':
                continue
            if not request.technician_signature:
                raise UserError(_('Technician signature is required before marking as collected.'))
            if not request.technician_signature_name:
                raise UserError(_('Signed By is required before marking as collected.'))

            picking = request._ensure_issue_picking()
            moves = picking.move_ids_without_package if 'move_ids_without_package' in picking._fields else picking.move_ids
            for move in moves:
                move_lines = move.move_line_ids
                if move_lines:
                    for move_line in move_lines:
                        reserved_qty = move_line.reserved_uom_qty if 'reserved_uom_qty' in move_line._fields else 0.0
                        move_line.write({done_qty_field: reserved_qty or move.product_uom_qty})
                else:
                    vals = {
                        'picking_id': picking.id,
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                    }
                    vals[done_qty_field] = move.product_uom_qty
                    move_line_model.sudo().create(vals)

            picking.sudo().button_validate()
            request.write({
                'state': 'collected',
                'collected_by': self.env.user.id,
                'collected_date': fields.Datetime.now(),
            })

    def action_cancel(self):
        self.filtered(lambda r: r.state in ('draft', 'to_approve', 'approved', 'rejected'))._cancel_issue_picking()
        self.filtered(lambda r: r.state in ('draft', 'to_approve', 'approved', 'rejected')).write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.filtered(lambda r: r.state in ('rejected', 'cancelled')).write({'state': 'draft'})


class MaintenancePartRequestLine(models.Model):
    _name = 'maintenance.part.request.line'
    _description = 'Maintenance Part Request Line'
    _order = 'id asc'

    part_request_id = fields.Many2one(
        'maintenance.part.request',
        string='Part Request',
        required=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(related='part_request_id.company_id', string='Institution', store=True, readonly=True)
    product_id = fields.Many2one(
        'product.product',
        string='Part',
        required=True,
        domain="[('type', 'in', ['consu', 'spares'])]",
    )
    qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unit', required=True)
    note = fields.Text(string='Notes')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
