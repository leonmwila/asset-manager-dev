from odoo import models
from odoo.fields import Domain


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    def _get_product_catalog_domain(self):
        return (
            Domain('company_id', '=', False) | Domain('company_id', 'parent_of', self.company_id.id)
        ) & Domain('type', 'in', ['consu', 'spares'])
