from odoo import models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    def action_print_labeler_barcodes(self):
        return self.env.ref(
            'serial_barcode_printer_from_labeler.report_lot_barcode_labeler'
        ).report_action(self)
