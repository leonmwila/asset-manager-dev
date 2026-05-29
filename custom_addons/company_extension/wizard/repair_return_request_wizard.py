from odoo import fields, models


class RepairReturnRequestWizard(models.TransientModel):
    _name = 'repair.return.request.wizard'
    _description = 'Repair Return Request Wizard'

    repair_id = fields.Many2one('repair.order', string='Repair Order', required=True)
    dest_company_id = fields.Many2one('res.company', string='Return To Institution', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.env['repair.return.request'].create({
            'repair_id': self.repair_id.id,
            'dest_company_id': self.dest_company_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}
