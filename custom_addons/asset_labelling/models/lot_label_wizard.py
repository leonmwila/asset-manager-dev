from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class StockLotLabelWizard(models.TransientModel):
    _name = "stock.lot.label.wizard"
    _description = "Lot/Serial Label Wizard"

    scan_serial_input = fields.Char(
        string="Scan Serial / GRZ Number",
        help="Scan a barcode or type a serial/GRZ and press Enter to auto-add a line.",
    )
    line_ids = fields.One2many(
        "stock.lot.label.wizard.line",
        "wizard_id",
        string="Serials",
    )

    @api.onchange("scan_serial_input")
    def _onchange_scan_serial_input(self):
        serial = (self.scan_serial_input or "").strip()
        if not serial:
            return

        self.line_ids = [(0, 0, {"serial_number": serial})]
        self.scan_serial_input = False

    def _get_serials(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Please add at least one serial line before continuing."))

        serials = []
        for line in self.line_ids:
            serial = (line.serial_number or "").strip()
            if not serial:
                raise ValidationError(_("Each line must contain a Serial/GRZ value."))
            serials.append(serial)

        serials_lc = [s.lower() for s in serials]
        duplicates = sorted({s for s in serials if serials_lc.count(s.lower()) > 1})
        if duplicates:
            raise ValidationError(
                _("Duplicate values in the input: %s") % ", ".join(duplicates)
            )
        return serials

    def _find_lots(self, serials):
        lot_model = self.env["stock.lot"].with_context(active_test=False)
        exact_domain = [
            "|",
            "|",
            ("name", "in", serials),
            ("ref", "in", serials),
            ("grz_number", "in", serials),
        ]
        lots = lot_model.search(exact_domain)
        if lots:
            return lots

        # Fallback for scanners or manual input with case variance.
        or_prefix = ["|"] * (len(serials) * 3 - 1)
        fuzzy_terms = []
        for value in serials:
            fuzzy_terms.extend([
                ("name", "ilike", value),
                ("ref", "ilike", value),
                ("grz_number", "ilike", value),
            ])
        return lot_model.search(or_prefix + fuzzy_terms)

    def _toggle_labelled(self, labelled):
        self.ensure_one()
        serials = self._get_serials()
        lots = self._find_lots(serials)

        found_keys = {
            (value or "").strip().lower()
            for value in (lots.mapped("name") + lots.mapped("ref") + lots.mapped("grz_number"))
            if value
        }
        missing = sorted([
            serial for serial in serials
            if serial.strip().lower() not in found_keys
        ])
        if missing:
            raise UserError(
                _("No asset found for value(s): %s") % ", ".join(missing)
            )

        lots.write({"labelled": labelled})

        message = _("%(count)s item(s) marked as labelled.") if labelled else _("%(count)s item(s) label removed.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": message % {"count": len(lots)},
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_label_assets(self):
        return self._toggle_labelled(True)

    def action_remove_assets(self):
        return self._toggle_labelled(False)


class StockLotLabelWizardLine(models.TransientModel):
    _name = "stock.lot.label.wizard.line"
    _description = "Lot/Serial Label Wizard Line"

    wizard_id = fields.Many2one(
        "stock.lot.label.wizard",
        required=True,
        ondelete="cascade",
    )
    serial_number = fields.Char(string="Serial / GRZ Number", required=True)
