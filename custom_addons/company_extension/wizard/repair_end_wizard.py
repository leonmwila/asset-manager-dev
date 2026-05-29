from odoo import fields, models


class RepairEndWizard(models.TransientModel):
    _name = 'repair.end.wizard'
    _description = 'Repair End Wizard'

    repair_id = fields.Many2one('repair.order', string='Repair Order', required=True)
    result = fields.Selection([
        ('repaired', 'Repaired'),
        ('failed', 'Failed'),
    ], default='repaired', required=True)

    def action_confirm(self):
        self.ensure_one()
        if self.result == 'failed':
            self.repair_id.write({'state': 'failed'})
            return {'type': 'ir.actions.act_window_close'}
        self.repair_id.action_repair_done()
        return {'type': 'ir.actions.act_window_close'}
