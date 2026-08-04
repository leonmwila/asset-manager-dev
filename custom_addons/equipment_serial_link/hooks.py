from odoo import SUPERUSER_ID, api


def post_init_hook(env_or_cr, registry=None):
    # Support both hook call signatures used by different Odoo runtimes:
    # 1) post_init_hook(env)
    # 2) post_init_hook(cr, registry)
    if registry is None and hasattr(env_or_cr, 'cr'):
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})

    lots = env['stock.lot'].sudo().search([])
    lots._sync_maintenance_equipment()
