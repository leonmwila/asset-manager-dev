from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class StockLotBulkWizard(models.TransientModel):
    _name = "stock.lot.bulk.wizard"
    _description = "Bulk Lot/Serial Creation Wizard"

    # Common data section
    product_id = fields.Many2one("product.product", string="Asset", required=True)
    company_id = fields.Many2one("res.company", string="Institution", required=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'company_id' in fields_list and not defaults.get('company_id'):
            # Prefer the company the user has currently active in the top-right
            # corner (first entry of allowed_company_ids) over the user's home
            # company, so the GRZ range search always uses the correct institution.
            allowed = self.env.context.get('allowed_company_ids')
            if allowed:
                defaults['company_id'] = allowed[0]
            else:
                defaults['company_id'] = self.env.user.company_id.id
        return defaults

    lot_acquisition_price = fields.Float(string="Acquisition Price")
    acquisition_date = fields.Date(string="Acquisition Date", default=fields.Date.today)
    supplier_id = fields.Many2one(
        "res.partner",
        string="Supplier",
        domain="[('supplier_rank', '>', 0)]",
    )
    program_id = fields.Many2one("oe.program", string="Program", domain="[('company_id', '=', company_id)]")
    project_id = fields.Many2one("oe.project", string="Project", domain="[('company_id', '=', company_id)]")
    assigned_to = fields.Many2one("hr.employee", string="Assigned To", domain="[('company_id', '=', company_id)]")
    department_id = fields.Many2one("hr.department", string="Department")
    vehicle_make = fields.Char(string="Make")
    engine_no = fields.Char(string="Engine No")
    plate_no = fields.Char(string="Plate No")
    is_vehicle = fields.Boolean(string="Is Vehicle", compute="_compute_is_vehicle")

    # Barcode scan helper: scanner can type value + Enter to append a new line automatically.
    scan_serial_input = fields.Char(string="Scan Serial Number", help="Scan a barcode or type serial and press Enter to auto-add a line.")

    # Dynamic data section
    line_ids = fields.One2many("stock.lot.bulk.wizard.line", "wizard_id", string="Serials")

    @api.depends("product_id", "product_id.categ_id", "product_id.categ_id.name")
    def _compute_is_vehicle(self):
        for wizard in self:
            category_name = (wizard.product_id.categ_id.name or "").strip().lower() if wizard.product_id.categ_id else ""
            wizard.is_vehicle = category_name == "vehicle"

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if not self.is_vehicle:
            self.vehicle_make = False
            self.engine_no = False
            self.plate_no = False

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id:
            self.env["grz.available.number"].ensure_numbers_for_company(self.company_id)
        # Clear any GRZ numbers already assigned to lines — they came from the
        # previous institution's range and are invalid for the newly selected one.
        for line in self.line_ids:
            line.grz_number_b = False
            line.grz_number = False

    def _build_grz_number(self, grz_num_record):
        """Build the full GRZ number string for a given grz.available.number record."""
        company = self.company_id
        if not company or not grz_num_record:
            return ""
        prefix = "GRZ/%s/" % company.company_code if company.company_type == "grz" else "%s/" % company.company_code
        middle = ""
        if self.program_id:
            middle += "%s/" % self.program_id.prog_code
            if self.project_id:
                middle += "%s/" % self.project_id.proj_code
        elif self.product_id:
            middle += "%s/" % (self.product_id.categ_id.category_code or "NO-CODE")
        if self.program_id and not self.project_id and self.product_id:
            middle += "%s/" % (self.product_id.categ_id.category_code or "NO-CODE")
        return "%s%s%s" % (prefix, middle, grz_num_record.number_padded or "")

    def _next_available_grz(self, exclude_ids=None):
        """Return the next unused grz.available.number for the wizard's company,
        skipping any IDs already claimed by existing lines in this session."""
        if not self.company_id:
            return self.env["grz.available.number"]
        # Keep available numbers in sync with the institution serial ranges.
        self.env["grz.available.number"].ensure_numbers_for_company(self.company_id)
        domain = [
            ("company_id", "=", self.company_id.id),
            ("is_used", "=", False),
        ]
        if exclude_ids:
            domain.append(("id", "not in", exclude_ids))
        return self.env["grz.available.number"].search(domain, order="number asc", limit=1)

    def _assign_missing_grz_numbers(self):
        """Assign next available GRZ numbers to lines with serials but no GRZ selection yet."""
        self.ensure_one()
        taken_ids = self.line_ids.filtered("grz_number_b").mapped("grz_number_b").ids
        for line in self.line_ids:
            if not (line.serial_number or "").strip() or line.grz_number_b:
                continue
            next_num = self._next_available_grz(exclude_ids=taken_ids)
            if not next_num:
                break
            line.grz_number_b = next_num
            line.grz_number = self._build_grz_number(next_num)
            taken_ids.append(next_num.id)

    @api.onchange("scan_serial_input")
    def _onchange_scan_serial_input(self):
        serial = (self.scan_serial_input or "").strip()
        if not serial:
            return

        # IDs already taken by lines already in this wizard session
        taken_ids = self.line_ids.filtered("grz_number_b").mapped("grz_number_b").ids
        next_num = self._next_available_grz(exclude_ids=taken_ids)

        line_vals = {"serial_number": serial}
        if next_num:
            line_vals["grz_number_b"] = next_num.id
            line_vals["grz_number"] = self._build_grz_number(next_num)

        self.line_ids = [(0, 0, line_vals)]
        self.scan_serial_input = False

    @api.onchange("line_ids", "line_ids.serial_number", "line_ids.grz_number_b", "company_id", "product_id", "program_id", "project_id")
    def _onchange_line_ids_auto_assign_grz(self):
        self._assign_missing_grz_numbers()

    def _validate_lines(self):
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("Please add at least one serial line before saving."))

        serials = []
        for line in self.line_ids:
            serial = (line.serial_number or "").strip()
            if not serial:
                raise ValidationError(_("Each line must contain a Serial Number."))
            serials.append(serial)

        duplicate_serials = sorted({s for s in serials if serials.count(s) > 1})
        if duplicate_serials:
            raise ValidationError(
                _("Duplicate serials in the input: %s") % ", ".join(duplicate_serials)
            )

        existing = self.env["stock.lot"].search([
            ("name", "in", serials),
            ("company_id", "=", self.company_id.id),
        ])
        if existing:
            raise ValidationError(
                _("These serial numbers already exist for this institution: %s")
                % ", ".join(existing.mapped("name"))
            )

    def action_save_bulk(self):
        self.ensure_one()
        self._assign_missing_grz_numbers()
        self._validate_lines()

        created_lot_ids = []
        for line in self.line_ids:
            vals = {
                "name": line.serial_number.strip(),
                "product_id": self.product_id.id,
                "company_id": self.company_id.id,
                "grz_number_b": line.grz_number_b.id or False,
                "lot_acquisition_price": self.lot_acquisition_price,
                "acquisition_date": self.acquisition_date,
                "supplier_id": self.supplier_id.id or False,
                "program_id": self.program_id.id or False,
                "project_id": self.project_id.id or False,
                "assigned_to": self.assigned_to.id or False,
                "department_id": self.department_id.id or False,
            }

            if line.grz_number:
                vals["grz_number"] = line.grz_number

            if self.is_vehicle:
                vals.update({
                    "vehicle_make": self.vehicle_make,
                    "engine_no": self.engine_no,
                    "plate_no": self.plate_no,
                })

            lot = self.env["stock.lot"].create(vals)
            created_lot_ids.append(lot.id)

        return {
            "type": "ir.actions.act_window",
            "name": _("Bulk Created Lots/Serials"),
            "res_model": "stock.lot",
            "view_mode": "list,form",
            "domain": [("id", "in", created_lot_ids)],
            "target": "current",
        }


class StockLotBulkWizardLine(models.TransientModel):
    _name = "stock.lot.bulk.wizard.line"
    _description = "Bulk Lot/Serial Creation Wizard Line"

    wizard_id = fields.Many2one("stock.lot.bulk.wizard", required=True, ondelete="cascade")
    serial_number = fields.Char(string="Serial Number", required=True)
    grz_number_b = fields.Many2one(
        "grz.available.number",
        string="GRZ Number B",
        domain="[('company_id', '=', parent.company_id), '|', ('is_used', '=', False), ('id', '=', grz_number_b)]",
    )
    grz_number = fields.Char(string="GRZ Number")

    @api.onchange("serial_number")
    def _onchange_serial_number_auto_grz(self):
        """When a serial number is entered, auto-assign the next available GRZ number."""
        serial = (self.serial_number or "").strip()
        if not serial or not self.wizard_id or not self.wizard_id.company_id:
            return
        # If user already manually set a GRZ number, don't overwrite it
        if self.grz_number_b:
            return
        # IDs already claimed by sibling lines in this session
        taken_ids = self.wizard_id.line_ids.filtered(
            lambda l: l != self and l.grz_number_b
        ).mapped("grz_number_b").ids
        next_num = self.wizard_id._next_available_grz(exclude_ids=taken_ids)
        if not next_num:
            return
        self.grz_number_b = next_num
        self.grz_number = self.wizard_id._build_grz_number(next_num)

    @api.onchange("grz_number_b")
    def _onchange_grz_number_b(self):
        if self.grz_number_b and self.wizard_id and self.wizard_id.company_id:
            company = self.wizard_id.company_id
            prefix = "GRZ/%s/" % company.company_code if company.company_type == "grz" else "%s/" % company.company_code

            middle = ""
            if self.wizard_id.program_id:
                middle += "%s/" % self.wizard_id.program_id.prog_code
                if self.wizard_id.project_id:
                    middle += "%s/" % self.wizard_id.project_id.proj_code
            elif self.wizard_id.product_id:
                middle += "%s/" % (self.wizard_id.product_id.categ_id.category_code or "NO-CODE")

            if self.wizard_id.program_id and not self.wizard_id.project_id and self.wizard_id.product_id:
                middle += "%s/" % (self.wizard_id.product_id.categ_id.category_code or "NO-CODE")

            self.grz_number = "%s%s%s" % (prefix, middle, self.grz_number_b.number_padded or "")
