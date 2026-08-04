import re

from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    product_id = fields.Many2one('product.product', string='Product')
    # Note: cost field already exists in standard maintenance.equipment model
    # Make serial_number a related field to the standard serial_no field
    # This maintains backward compatibility while using Odoo's standard field
    serial_number = fields.Char(string='Serial Number', related='serial_no', store=True, readonly=False)

    @staticmethod
    def _extract_grz_from_text(text):
        if not text:
            return False
        match = re.search(r'(GRZ/[A-Za-z0-9/_-]+)', text)
        return match.group(1) if match else False

    def _build_lot_grz_map(self):
        lot_model = self.env['stock.lot'].sudo()
        lots = lot_model.search([('equipment_id', 'in', self.ids)], order='id desc')
        grz_by_equipment = {}
        for lot in lots:
            equipment_id = lot.equipment_id.id
            if equipment_id in grz_by_equipment:
                continue

            grz_number = False
            if 'grz_number' in lot._fields:
                grz_number = lot.grz_number or False
            if not grz_number:
                grz_number = self._extract_grz_from_text(lot.ref)
            if not grz_number:
                grz_number = self._extract_grz_from_text(lot.name)

            if grz_number:
                grz_by_equipment[equipment_id] = grz_number

        return grz_by_equipment

    def name_get(self):
        grz_by_equipment = self._build_lot_grz_map()
        result = []
        for equipment in self:
            base_name = equipment.display_name or equipment.name or ''
            grz_number = grz_by_equipment.get(equipment.id)
            if grz_number and grz_number not in base_name:
                base_name = '%s/%s' % (base_name, grz_number)
            result.append((equipment.id, base_name))
        return result

    def _compute_display_name(self):
        super()._compute_display_name()
        grz_by_equipment = self._build_lot_grz_map()
        for equipment in self:
            grz_number = grz_by_equipment.get(equipment.id)
            if not grz_number:
                continue
            base_name = equipment.display_name or equipment.name or ''
            if grz_number not in base_name:
                equipment.display_name = '%s/%s' % (base_name, grz_number)