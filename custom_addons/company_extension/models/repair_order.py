from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import UserError

class RepairOrder(models.Model):
    _inherit = 'repair.order'
    
    # Disable automatic company checking to allow cross-company lot selection
    _check_company_auto = False
    
    # Override the lot_id field to remove company restrictions
    lot_id = fields.Many2one(
        'stock.lot',
        'Asset Serial',
        domain="[('product_id', '=', product_id)]",  # Base filter; refined by onchange
        check_company=False,  # Disable company consistency check
        help="Serial number of the asset to repair. This field shows serial numbers from all companies."
    )

    def _get_repair_lot_domain(self):
        """Return lot domain based on selected asset and customer."""
        domain = []
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.partner_id:
            domain.append(('company_id.partner_id', 'child_of', self.partner_id.id))
        return domain

    @api.onchange('partner_id', 'product_id')
    def _onchange_partner_product_lot_domain(self):
        domain = []
        for repair in self:
            domain = repair._get_repair_lot_domain()
            if repair.lot_id:
                partner_ok = not repair.partner_id or (
                    repair.lot_id.company_id and repair.lot_id.company_id.partner_id and
                    repair.lot_id.company_id.partner_id in repair.partner_id.child_ids | repair.partner_id
                )
                if repair.lot_id.product_id != repair.product_id or not partner_ok:
                    repair.lot_id = False
        return {'domain': {'lot_id': domain}}
    
    # Add new states for approvals and repair outcomes
    state = fields.Selection(
        selection_add=[
            ('parts_approved', 'Parts Approved'),
            ('failed', 'Failed'),
            ('transferred', 'Transferred'),
            ('returned', 'Returned'),
        ],
        ondelete={
            'parts_approved': 'set default',
            'failed': 'set default',
            'transferred': 'set default',
            'returned': 'set default',
        },
    )
    
    parts_approved = fields.Boolean(string="Parts Approved", default=False, tracking=True)
    parts_approved_by = fields.Many2one('res.users', string="Parts Approved By", readonly=True, tracking=True)
    parts_approved_date = fields.Datetime(string="Parts Approval Date", readonly=True, tracking=True)
    responsible_user_ids = fields.Many2many(
        'res.users',
        'repair_order_responsible_user_rel',
        'repair_id',
        'user_id',
        string='Responsible',
        tracking=True,
        domain="[('share', '=', False)]",
        default=lambda self: [(6, 0, [self.env.user.id])],
        help='Users responsible for this repair order.'
    )

    transfer_request_ids = fields.One2many('repair.transfer.request', 'repair_id', string='Transfer Requests')
    return_request_ids = fields.One2many('repair.return.request', 'repair_id', string='Return Requests')
    spare_part_request_id = fields.Many2one('repair.spare.part.request', string='Spare Part Request', readonly=True, copy=False)
    has_pending_transfer_request = fields.Boolean(compute='_compute_pending_requests')
    has_pending_return_request = fields.Boolean(compute='_compute_pending_requests')
    
    # Add Operations/Services fees
    fees_lines = fields.One2many('repair.fee', 'repair_id', string='Operations')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                   default=lambda self: self.env.company.currency_id)
    fees_amount = fields.Monetary(string='Operations Total', compute='_compute_fees_amount', store=True)
    parts_amount = fields.Monetary(string='Parts Total', compute='_compute_parts_amount', store=True)
    total_amount = fields.Monetary(string='Total', compute='_compute_total_amount', store=True)
    # Link to automatically created invoice (customer invoice)
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False, readonly=True)
    
    # Payment tracking fields
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ], string='Payment Status', default='not_paid', tracking=True)
    paid_amount = fields.Monetary(string='Paid Amount', default=0.0, tracking=True)
    balance_amount = fields.Monetary(string='Balance', compute='_compute_balance_amount', store=True)
    payment_date = fields.Date(string='Payment Date', tracking=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
    ], string='Payment Method', tracking=True)
    payment_reference = fields.Char(string='Payment Reference', tracking=True)
    received_by = fields.Many2one('res.users', string='Received By', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('responsible_user_ids') and not vals.get('user_id'):
                command = vals['responsible_user_ids']
                if command and command[0][0] == 6 and command[0][2]:
                    vals['user_id'] = command[0][2][0]
            elif vals.get('user_id') and not vals.get('responsible_user_ids'):
                vals['responsible_user_ids'] = [(6, 0, [vals['user_id']])]
        records = super().create(vals_list)
        for repair in records.filtered(lambda r: r.user_id and not r.responsible_user_ids):
            repair.responsible_user_ids = [(6, 0, [repair.user_id.id])]
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'responsible_user_ids' in vals:
            for repair in self:
                if repair.responsible_user_ids:
                    repair.user_id = repair.responsible_user_ids[0].id
        elif 'user_id' in vals:
            for repair in self.filtered('user_id'):
                if repair.user_id not in repair.responsible_user_ids:
                    repair.responsible_user_ids = [(4, repair.user_id.id)]
        return result
    
    @api.depends('fees_lines.price_subtotal')
    def _compute_fees_amount(self):
        for repair in self:
            repair.fees_amount = sum(repair.fees_lines.mapped('price_subtotal'))

    @api.depends('transfer_request_ids.state', 'return_request_ids.state')
    def _compute_pending_requests(self):
        for repair in self:
            repair.has_pending_transfer_request = any(req.state == 'pending' for req in repair.transfer_request_ids)
            repair.has_pending_return_request = any(req.state == 'pending' for req in repair.return_request_ids)
    
    @api.depends('move_ids', 'move_ids.product_id')
    def _compute_parts_amount(self):
        """Compute total cost of parts used"""
        for repair in self:
            total = 0.0
            for move in repair.move_ids:
                # Use product cost from product
                cost = move.product_id.standard_price if move.product_id else 0.0
                total += cost * move.product_uom_qty
            repair.parts_amount = total
    
    @api.depends('fees_amount', 'parts_amount')
    def _compute_total_amount(self):
        for repair in self:
            repair.total_amount = repair.fees_amount + repair.parts_amount
    
    @api.depends('total_amount', 'paid_amount')
    def _compute_balance_amount(self):
        for repair in self:
            repair.balance_amount = repair.total_amount - repair.paid_amount
    
    @api.onchange('paid_amount', 'total_amount')
    def _onchange_paid_amount(self):
        """Auto-update payment state based on paid amount"""
        for repair in self:
            if repair.paid_amount <= 0:
                repair.payment_state = 'not_paid'
            elif repair.paid_amount >= repair.total_amount:
                repair.payment_state = 'paid'
            else:
                repair.payment_state = 'partial'
    
    def action_mark_paid(self):
        """Mark repair as fully paid"""
        for repair in self:
            repair.write({
                'paid_amount': repair.total_amount,
                'payment_state': 'paid',
                'payment_date': fields.Date.today(),
                'received_by': self.env.user.id,
            })
        return True

    def action_open_transfer_request_wizard(self):
        self.ensure_one()
        return {
            'name': 'Transfer Request',
            'type': 'ir.actions.act_window',
            'res_model': 'repair.transfer.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_repair_id': self.id},
        }

    def action_open_return_request_wizard(self):
        self.ensure_one()
        return {
            'name': 'Return Request',
            'type': 'ir.actions.act_window',
            'res_model': 'repair.return.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_repair_id': self.id},
        }

    def action_approve_transfer_request(self):
        for repair in self:
            request = repair.transfer_request_ids.filtered(lambda r: r.state == 'pending')
            if request:
                request[-1].action_approve()
        return True

    def action_approve_return_request(self):
        for repair in self:
            request = repair.return_request_ids.filtered(lambda r: r.state == 'pending')
            if request:
                request[-1].action_approve()
        return True

    def action_open_end_repair_wizard(self):
        self.ensure_one()
        return {
            'name': 'End Repair',
            'type': 'ir.actions.act_window',
            'res_model': 'repair.end.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_repair_id': self.id},
        }

    def action_validate(self):
        """Override to skip stock check for cross-company repairs"""
        self.ensure_one()
        
        if self.filtered(lambda repair: any(m.product_uom_qty < 0 for m in repair.move_ids)):
            raise UserError(_("You can not enter negative quantities."))
        
        if not self.product_id or not self.product_id.is_storable:
            return self._action_repair_confirm()
        
        # Skip stock availability check if lot belongs to different company
        if self.lot_id and self.lot_id.company_id and self.lot_id.company_id != self.company_id:
            return self._action_repair_confirm()
        
        # Otherwise, perform normal stock validation
        return super(RepairOrder, self).action_validate()
    
    def action_approve_parts(self):
        """Approve the parts selected for repair"""
        for repair in self:
            if not repair.move_ids:
                raise UserError(_("Please add parts to repair before approving."))
            repair._reserve_spares_moves()
            repair._create_spare_part_request()
            repair.write({
                'parts_approved': True,
                'parts_approved_by': self.env.user.id,
                'parts_approved_date': fields.Datetime.now(),
                'state': 'parts_approved'
            })
        return True

    def _create_spare_part_request(self):
        """Create a Spare Part Request record when parts are approved.

        This is an approval/pickup tracking record only. It does not perform stock moves.
        """
        self.ensure_one()

        if self.spare_part_request_id and self.spare_part_request_id.state != 'cancelled':
            return self.spare_part_request_id

        spares_moves = self.move_ids.filtered(
            lambda m: m.repair_line_type == 'add'
            and m.product_id
            and getattr(m.product_id, 'type', False) == 'spares'
            and m.product_uom_qty
        )
        if not spares_moves:
            return False

        technician_user = self.responsible_user_ids[:1] if self.responsible_user_ids else self.user_id
        line_values = []
        for move in spares_moves:
            line_values.append((0, 0, {
                'product_id': move.product_id.id,
                'qty': move.product_uom_qty,
                'product_uom_id': move.product_uom.id or move.product_id.uom_id.id,
                'repair_move_id': move.id,
            }))

        request = self.env['repair.spare.part.request'].create({
            'repair_id': self.id,
            'requested_by': technician_user.id if technician_user else self.env.user.id,
            'approved_by': self.env.user.id,
            'approved_date': fields.Datetime.now(),
            'state': 'approved',
            'line_ids': line_values,
        })

        self.spare_part_request_id = request.id
        self.message_post(body=_("Spare Part Request created: %s") % request.display_name)
        return request
    
    def action_repair_start(self):
        """Override to check parts approval before starting repair"""
        for repair in self:
            # If there are parts but not approved, prevent starting repair
            if repair.move_ids and not repair.parts_approved:
                raise UserError(_("Parts must be approved before starting the repair."))
        
        return super(RepairOrder, self).action_repair_start()

    def action_repair_cancel(self):
        spares_moves = self.move_ids.filtered(
            lambda m: m.repair_line_type == 'add'
            and m.product_id
            and getattr(m.product_id, 'type', False) == 'spares'
        )
        spares_moves.filtered(lambda m: m.state in ('assigned', 'partially_available'))._do_unreserve()
        return super(RepairOrder, self).action_repair_cancel()

    def action_repair_done(self):
        """Consume spares without stock moves and close the repair."""
        self._consume_spares_without_moves()

        # Cancel moves with 0 quantity
        self.move_ids.filtered(lambda m: m.product_uom.is_zero(m.quantity))._action_cancel()

        no_service_policy = 'service_policy' not in self.env['product.template']
        for repair in self:
            if all(not move.picked for move in repair.move_ids):
                repair.move_ids.picked = True

            # Keep the base delivery behavior for service-only repair products
            if repair.sale_order_line_id:
                ro_origin_product = repair.sale_order_line_id.product_template_id
                if ro_origin_product.type == 'service' and (no_service_policy or ro_origin_product.service_policy == 'ordered_prepaid'):
                    repair.sale_order_line_id.qty_delivered = repair.sale_order_line_id.product_uom_qty

            # Update sales delivery for spares without relying on stock moves
            spares_moves = repair.move_ids.filtered(
                lambda m: m.repair_line_type == 'add'
                and m.product_id
                and getattr(m.product_id, 'type', False) == 'spares'
                and m.product_uom_qty
            )
            for move in spares_moves:
                if move.sale_line_id:
                    qty = move.product_uom._compute_quantity(move.product_uom_qty, move.sale_line_id.product_uom_id)
                    price_unit = move.sale_line_id.price_unit
                    move.sale_line_id.write({
                        'qty_delivered': qty,
                        'product_uom_qty': qty,
                        'price_unit': price_unit,
                    })

        self.write({'state': 'done'})
        return True

    def _consume_spares_without_moves(self):
        """Reduce on-hand for spares without creating stock moves."""
        Quant = self.env['stock.quant']
        for repair in self:
            consumed_lines = []
            spares_moves = repair.move_ids.filtered(
                lambda m: m.repair_line_type == 'add'
                and m.product_id
                and getattr(m.product_id, 'type', False) == 'spares'
                and m.product_uom_qty
            )
            for move in spares_moves:
                product = move.product_id
                location = move.location_id or repair.location_id
                if not location:
                    raise UserError(_("No source location found to consume spares for %s.") % product.display_name)

                if move.state in ('assigned', 'partially_available'):
                    move._do_unreserve()

                if product.tracking == 'none':
                    qty = move.product_uom._compute_quantity(move.product_uom_qty, product.uom_id)
                    Quant._update_available_quantity(product, location, -qty)
                    consumed_lines.append(f"{product.display_name}: {qty:g} {product.uom_id.name}")
                    continue

                move_lines = move.move_line_ids.filtered(
                    lambda line: line.lot_id and (line.quantity or line.quantity_product_uom)
                )
                if move_lines:
                    for line in move_lines:
                        line_qty = line.quantity_product_uom or line.product_uom_id._compute_quantity(line.quantity, product.uom_id)
                        Quant._update_available_quantity(product, location, -line_qty, lot_id=line.lot_id)
                        consumed_lines.append(
                            f"{product.display_name} - {line.lot_id.name}: {line_qty:g} {product.uom_id.name}"
                        )
                    continue

                lots = move.move_line_ids.mapped('lot_id') | move.lot_ids
                if not lots:
                    tracked_quants = Quant.search([
                        ('product_id', '=', product.id),
                        ('location_id', '=', location.id),
                        ('lot_id', '!=', False),
                        ('quantity', '>', 0),
                    ])
                    lots = tracked_quants.mapped('lot_id')
                if not lots:
                    raise UserError(_("Lot/Serial is required to consume tracked spare: %s") % product.display_name)

                qty = move.product_uom._compute_quantity(move.product_uom_qty, product.uom_id)
                if product.tracking == 'serial':
                    if product.uom_id.compare(qty, len(lots)) != 0:
                        raise UserError(_(
                            "Serial-tracked spare %s needs %s lots for quantity %s."
                        ) % (product.display_name, len(lots), qty))
                    for lot in lots:
                        Quant._update_available_quantity(product, location, -1, lot_id=lot)
                        consumed_lines.append(
                            f"{product.display_name} - {lot.name}: 1 {product.uom_id.name}"
                        )
                else:
                    if len(lots) > 1:
                        raise UserError(_(
                            "Lot-tracked spare %s has multiple lots; set quantities per lot."
                        ) % product.display_name)
                    Quant._update_available_quantity(product, location, -qty, lot_id=lots[0])
                    consumed_lines.append(
                        f"{product.display_name} - {lots[0].name}: {qty:g} {product.uom_id.name}"
                    )

            if consumed_lines:
                repair.message_post(
                    body=_('Spares consumed (no stock moves):<br/>%s') % '<br/>'.join(consumed_lines)
                )

    def _reserve_spares_moves(self):
        """Reserve spares quantities without completing stock moves."""
        for repair in self:
            spares_moves = repair.move_ids.filtered(
                lambda m: m.repair_line_type == 'add'
                and m.product_id
                and getattr(m.product_id, 'type', False) == 'spares'
                and m.product_uom_qty
            )
            if not spares_moves:
                continue

            moves_to_confirm = spares_moves.filtered(lambda m: m.state == 'draft')
            if moves_to_confirm:
                moves_to_confirm._action_confirm()

            spares_moves._action_assign()
            unassigned = spares_moves.filtered(lambda m: m.state != 'assigned')
            if unassigned:
                unassigned._do_unreserve()
                raise UserError(_(
                    "Not enough stock to reserve all spares. Check lots/serials and availability."
                ))

    def _add_operations_to_sale_order(self):
        """Add operations/services and asset info lines to the linked quotation."""
        self.ensure_one()
        if not self.sale_order_id:
            return

        order = self.sale_order_id
        SaleLine = self.env['sale.order.line']

        # Parts lines created from stock moves for this repair
        part_lines = order.order_line.filtered(
            lambda l: l.move_ids and l.move_ids.repair_id == self and not l.display_type
        )

        # Ensure parts lines appear after sections
        next_seq = 60
        for line in part_lines:
            line.sequence = next_seq
            next_seq += 1

        asset_label = f"Asset: {self.product_id.display_name}" if self.product_id else "Asset"
        if self.lot_id:
            asset_label = f"{asset_label} | Serial: {self.lot_id.name}"

        SaleLine.create({
            'order_id': order.id,
            'display_type': 'line_note',
            'name': asset_label,
            'sequence': 1,
        })

        SaleLine.create({
            'order_id': order.id,
            'display_type': 'line_section',
            'name': 'Operations/Services',
            'sequence': 2,
        })

        seq = 3
        for fee in self.fees_lines:
            tax_ids = [(6, 0, fee.tax_id.ids)] if fee.tax_id else []
            SaleLine.create({
                'order_id': order.id,
                'product_id': fee.product_id.id if fee.product_id else False,
                'name': fee.name or (fee.product_id.display_name if fee.product_id else 'Operation'),
                'product_uom_qty': fee.product_uom_qty or 1.0,
                'price_unit': fee.price_unit or 0.0,
                'tax_ids': tax_ids,
                'sequence': seq,
            })
            seq += 1

        if part_lines:
            SaleLine.create({
                'order_id': order.id,
                'display_type': 'line_section',
                'name': 'Parts',
                'sequence': 50,
            })

    def action_create_sale_order(self):
        res = super().action_create_sale_order()
        for repair in self:
            repair._add_operations_to_sale_order()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Create repair orders and automatically generate a customer invoice for each new repair.

        The invoice is created from operations/fees lines and parts (move_ids) when present.
        """
        records = super(RepairOrder, self).create(vals_list)
        invoices = self.env['account.move']
        for rec in records:
            try:
                inv_vals = rec._prepare_invoice_vals()
                if inv_vals and inv_vals.get('invoice_line_ids'):
                    inv = self.env['account.move'].sudo().create(inv_vals)
                    # Link invoice to repair
                    rec.invoice_id = inv.id
                    invoices |= inv
            except Exception:
                # Don't block repair creation if invoicing fails; log and continue
                _logger = getattr(self, '_logger', None) or __import__('logging').getLogger('odoo.addons.company_extension')
                _logger.exception('Failed to auto-create invoice for Repair Order %s', rec.name)
        return records

    def _prepare_invoice_vals(self):
        """Prepare `account.move` values for this repair order.

        Returns dict usable with `account.move.create()`.
        """
        self.ensure_one()
        # Basic invoice header
        partner = self.partner_id or self.picking_id.partner_id
        if not partner:
            return {}
        currency = self.currency_id.id if hasattr(self, 'currency_id') and self.currency_id else (self.env.company.currency_id.id)
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_origin': self.name,
            'invoice_user_id': self.user_id.id if self.user_id else self.env.user.id,
            'company_id': self.company_id.id if self.company_id else self.env.company.id,
            'currency_id': currency,
            'invoice_line_ids': [],
        }

        # Add fee lines (operations/services)
        for fee in self.fees_lines:
            line = {
                'name': fee.name or (fee.product_id.name if fee.product_id else 'Operation'),
                'product_id': fee.product_id.id if fee.product_id else False,
                'quantity': fee.product_uom_qty or 1.0,
                'price_unit': fee.price_unit or 0.0,
                'tax_ids': [(6, 0, fee.tax_id.ids)] if fee.tax_id else False,
            }
            invoice_vals['invoice_line_ids'].append((0, 0, line))

        # Add parts lines (stock moves)
        for move in self.move_ids.filtered(lambda m: m.product_uom_qty):
            product = move.product_id
            if not product:
                continue
            # Use sale price (list price) as default unit price
            price_unit = getattr(product, 'list_price', 0.0) or 0.0
            # Taxes from product
            taxes = product.taxes_id.ids if hasattr(product, 'taxes_id') else []
            line = {
                'name': product.name,
                'product_id': product.id,
                'quantity': move.product_uom_qty,
                'price_unit': price_unit,
                'tax_ids': [(6, 0, taxes)] if taxes else False,
            }
            invoice_vals['invoice_line_ids'].append((0, 0, line))

        # If no lines to invoice, return empty dict
        if not invoice_vals['invoice_line_ids']:
            return {}
        return invoice_vals
