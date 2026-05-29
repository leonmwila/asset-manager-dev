from odoo import fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    labelled = fields.Boolean(
        string='Labelled',
        default=False,
        help='Ticked when the physical item label has been applied.',
    )

    def action_label_items(self):
        """Mark selected items as labelled."""
        self.write({'labelled': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'{len(self)} item(s) marked as labelled.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_remove_label_items(self):
        """Mark selected items as not labelled."""
        self.write({'labelled': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'{len(self)} item(s) label(s) removed.',
                'type': 'success',
                'sticky': False,
            }
        }
