from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    service_company_id = fields.Many2one(
        'res.company',
        string='Service Provider Institution',
        domain="[('institution_type_2', '=', 'supplier')]",
        help='Institution that will provide the maintenance service.',
    )
    customer_company_type = fields.Selection(
        related='company_id.institution_type_2',
        string='Customer Institution Type',
        store=True,
        readonly=True,
    )
    service_company_type = fields.Selection(
        related='service_company_id.institution_type_2',
        string='Service Provider Institution Type',
        store=True,
        readonly=True,
    )

    technician_user_ids = fields.Many2many(
        'res.users',
        'maintenance_request_technician_rel',
        'request_id',
        'user_id',
        string='Technicians',
        domain="[('share', '=', False)]",
        help='Technicians assigned to work on this maintenance request.',
    )

    service_line_ids = fields.One2many(
        'maintenance.request.service.line',
        'request_id',
        string='Services',
    )
    part_line_ids = fields.One2many(
        'maintenance.request.part.line',
        'request_id',
        string='Parts',
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Customer Invoice',
        readonly=True,
        copy=False,
    )
    invoice_count = fields.Integer(
        string='Invoices',
        compute='_compute_invoice_count',
    )
    can_create_invoice = fields.Boolean(
        string='Can Create Invoice',
        compute='_compute_can_create_invoice',
    )

    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        for request in self:
            request.invoice_count = 1 if request.invoice_id else 0

    @api.depends('stage_id', 'stage_id.name', 'invoice_id', 'invoice_id.state')
    def _compute_can_create_invoice(self):
        for request in self:
            is_in_progress = bool(request.stage_id and (request.stage_id.name or '').strip().lower() == 'in progress')
            has_open_invoice = bool(request.invoice_id and request.invoice_id.state != 'cancel')
            request.can_create_invoice = is_in_progress and not has_open_invoice

    def _get_invoice_partner(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        partner = False

        def _is_company_compatible(candidate):
            commercial = candidate.commercial_partner_id
            candidate_company = candidate.company_id
            commercial_company = commercial.company_id
            return (
                (not candidate_company or candidate_company == company)
                and (not commercial_company or commercial_company == company)
            )

        candidates = []

        employee = getattr(self, 'employee_id', False)
        if employee:
            candidates.extend((employee.work_contact_id, employee.user_id.partner_id))

        owner_user = getattr(self, 'owner_user_id', False)
        if owner_user:
            candidates.append(owner_user.partner_id)

        if self.user_id:
            candidates.append(self.user_id.partner_id)

        if company.partner_id:
            candidates.append(company.partner_id)

        for candidate in candidates:
            if candidate and _is_company_compatible(candidate):
                partner = candidate
                break

        if not partner:
            raise UserError(_('No company-compatible invoice customer could be determined. Use a requester/contact in %s or set the institution contact for invoicing.') % company.display_name)

        return partner

    def _prepare_invoice_line_vals(self):
        self.ensure_one()
        chargeable_line_vals = []
        asset_details = self._get_asset_invoice_details()

        for service_line in self.service_line_ids.filtered(lambda line: line.product_uom_qty > 0):
            if not service_line.product_id:
                raise UserError(_('Each service line must have a Service product before creating an invoice.'))
            chargeable_line_vals.append((0, 0, {
                'product_id': service_line.product_id.id,
                'name': service_line.name or service_line.product_id.display_name,
                'quantity': service_line.product_uom_qty,
                'price_unit': service_line.price_unit,
            }))

        for part_line in self.part_line_ids.filtered(lambda line: line.qty > 0):
            chargeable_line_vals.append((0, 0, {
                'product_id': part_line.product_id.id,
                'name': part_line.product_id.display_name,
                'quantity': part_line.qty,
                'price_unit': part_line.price_unit,
            }))

        if not chargeable_line_vals:
            raise UserError(_('Add at least one service or part line with quantity greater than zero before creating an invoice.'))

        detail_parts = [
            _('Asset/Product: %s') % asset_details['asset_product'],
            _('Serial Number: %s') % asset_details['serial_number'],
            _('GRZ Number: %s') % asset_details['grz_number'],
        ]
        line_vals = [(0, 0, {
            'display_type': 'line_section',
            'name': _('Asset Details | %s') % (' | '.join(detail_parts)),
        })] + chargeable_line_vals

        return line_vals

    def _get_asset_invoice_details(self):
        self.ensure_one()
        equipment = self.equipment_id

        asset_product = equipment.product_id.display_name if equipment and equipment.product_id else (equipment.display_name if equipment else _('N/A'))

        serial_number = _('N/A')
        if equipment:
            serial_number = (
                getattr(equipment, 'serial_number', False)
                or getattr(equipment, 'serial_no', False)
                or (getattr(equipment, 'lot_id', False) and equipment.lot_id.name)
                or _('N/A')
            )

        grz_number = _('N/A')
        if equipment:
            grz_number = (
                getattr(equipment, 'grz_number', False)
                or (getattr(equipment, 'lot_id', False) and getattr(equipment.lot_id, 'grz_number', False))
                or _('N/A')
            )

        return {
            'asset_product': asset_product,
            'serial_number': serial_number,
            'grz_number': grz_number,
        }

    def action_create_invoice(self):
        for request in self:
            if not request.can_create_invoice:
                raise UserError(_('Invoice can only be created when the maintenance request is In Progress and no active invoice is linked.'))

            partner = request._get_invoice_partner()
            line_vals = request._prepare_invoice_line_vals()
            existing_invoice = request.invoice_id
            if existing_invoice and existing_invoice.state != 'cancel':
                raise UserError(_('An active invoice is already linked to this maintenance request.'))

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'company_id': request.company_id.id or self.env.company.id,
                'invoice_origin': request.name,
                'ref': request.name,
                'invoice_line_ids': line_vals,
                'narration': _(
                    'Asset Information\n'
                    'Asset/Product: %(asset_product)s\n'
                    'Serial Number: %(serial_number)s\n'
                    'GRZ Number: %(grz_number)s'
                ) % request._get_asset_invoice_details(),
            }
            company = request.company_id or self.env.company
            invoice = self.env['account.move'].with_company(company).create(invoice_vals)
            request.invoice_id = invoice.id
            request.message_post(body=_('Draft customer invoice %s has been created.') % invoice.display_name)

        return self.action_view_invoice()

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_('No invoice is linked to this maintenance request yet.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('company_id')
    def _onchange_company_id_role_filter(self):
        """Restrict requester and service-provider institutions to the correct roles."""
        if self.company_id and self.company_id.institution_type_2 != 'customer':
            self.company_id = False
        if self.service_company_id and self.service_company_id.id == self.company_id.id:
            self.service_company_id = False
        if self.service_company_id and self.service_company_id.institution_type_2 != 'supplier':
            self.service_company_id = False

    @api.onchange('service_company_id')
    def _onchange_service_company_id_role_filter(self):
        """Ensure the selected service provider is always a supplier institution."""
        if self.service_company_id and self.service_company_id.institution_type_2 != 'supplier':
            self.service_company_id = False

    @api.onchange('company_id')
    def _onchange_company_equipment_domain(self):
        """Limit equipment to the selected institution on repair requests."""
        domain = [('id', '=', False)]
        if self.company_id:
            domain = [('company_id', '=', self.company_id.id)]
            if self.equipment_id and self.equipment_id.company_id != self.company_id:
                self.equipment_id = False
        else:
            self.equipment_id = False
        return {'domain': {'equipment_id': domain}}

    def _notify_new_technicians(self, previous_technician_map):
        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        for request in self:
            previous_ids = previous_technician_map.get(request.id, set())
            new_technicians = request.technician_user_ids.filtered(lambda user: user.id not in previous_ids)
            if not new_technicians:
                continue

            request.message_subscribe(partner_ids=new_technicians.mapped('partner_id').ids)

            existing_activity_user_ids = set()
            if todo_type:
                existing_activity_user_ids = set(request.activity_ids.filtered(
                    lambda activity: activity.activity_type_id == todo_type and activity.user_id in new_technicians
                ).mapped('user_id').ids)

            for technician in new_technicians.filtered(lambda user: user.id not in existing_activity_user_ids):
                request.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=technician.id,
                    summary=_('Maintenance Request Assigned'),
                    note=_('You have been assigned to maintenance request %s.') % request.display_name,
                )

    @api.model_create_multi
    def create(self, vals_list):
        requests = super().create(vals_list)
        previous_technician_map = {request.id: set(request.technician_user_ids.ids) for request in requests}
        for request in requests:
            if request.user_id and request.user_id not in request.technician_user_ids:
                request.technician_user_ids = [(4, request.user_id.id)]
        requests._notify_new_technicians(previous_technician_map)
        return requests

    def write(self, vals):
        should_track_technicians = 'technician_user_ids' in vals or 'user_id' in vals
        previous_technician_map = {}
        if should_track_technicians:
            previous_technician_map = {request.id: set(request.technician_user_ids.ids) for request in self}

        result = super().write(vals)
        if 'user_id' in vals:
            for request in self:
                if request.user_id and request.user_id not in request.technician_user_ids:
                    request.technician_user_ids = [(4, request.user_id.id)]
        if should_track_technicians:
            self._notify_new_technicians(previous_technician_map)
        return result


class MaintenanceRequestServiceLine(models.Model):
    _name = 'maintenance.request.service.line'
    _description = 'Maintenance Request Service Line'
    _order = 'id asc'

    request_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance Request',
        required=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        related='request_id.company_id',
        string='Institution',
        store=True,
        readonly=True,
    )
    equipment_id = fields.Many2one(
        related='request_id.equipment_id',
        string='Equipment',
        store=True,
        readonly=True,
    )
    name = fields.Text(string='Description', required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Service',
        domain="[('type', '=', 'service')]",
    )
    product_uom_qty = fields.Float(string='Quantity', default=1.0, digits='Product Unit of Measure')
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_price_subtotal', store=True)
    currency_id = fields.Many2one(related='request_id.company_id.currency_id', store=True, readonly=True)
    note = fields.Text(string='Notes')

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_uom_qty * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name
            self.price_unit = self.product_id.lst_price


class MaintenanceRequestPartLine(models.Model):
    _name = 'maintenance.request.part.line'
    _description = 'Maintenance Request Part Line'
    _order = 'id asc'

    request_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance Request',
        required=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        related='request_id.company_id',
        string='Institution',
        store=True,
        readonly=True,
    )
    equipment_id = fields.Many2one(
        related='request_id.equipment_id',
        string='Equipment',
        store=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Part',
        required=True,
        domain="[('type', 'in', ['consu', 'spares'])]",
    )
    qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unit', required=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_price_subtotal', store=True)
    currency_id = fields.Many2one(related='request_id.company_id.currency_id', store=True, readonly=True)
    note = fields.Text(string='Notes')

    @api.depends('qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.qty * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            self.price_unit = self.product_id.lst_price