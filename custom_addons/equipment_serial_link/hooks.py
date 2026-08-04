from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    lots = env['stock.lot'].sudo().search([])
    lots._sync_maintenance_equipment()
