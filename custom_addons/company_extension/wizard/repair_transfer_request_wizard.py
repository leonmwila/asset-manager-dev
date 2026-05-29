from odoo import fields, models


class RepairTransferRequestWizard(models.TransientModel):
    _name = 'repair.transfer.request.wizard'
    _description = 'Repair Transfer Request Wizard'

    repair_id = fields.Many2one('repair.order', string='Repair Order', required=True)
    dest_company_id = fields.Many2one('res.company', string='Destination Institution', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.env['repair.transfer.request'].create({
            'repair_id': self.repair_id.id,
            'dest_company_id': self.dest_company_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}
