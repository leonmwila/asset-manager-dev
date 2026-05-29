from odoo import models, fields, api


class StockLot(models.Model):
    _inherit = 'stock.lot'

    print_barcode = fields.Boolean(
        string='Print Barcode',
        help='Check this to include this serial number in barcode printing'
    )

    company_logo_image = fields.Binary(
        string='Company Logo',
        compute='_compute_company_logo_image',
        help='Company logo image for label printing'
    )
    
    company_logo_data_uri = fields.Char(
        string='Company Logo Data URI',
        compute='_compute_company_logo_image',
        help='Company logo as data URI for PDF reports'
    )

    @api.depends('company_id', 'company_id.logo')
    def _compute_company_logo_image(self):
        """Compute the company logo image as Binary field for PDF reports"""
        for record in self:
            # Get company from lot's company_id, or from product's company_id, or use current company
            company = record.company_id or (record.product_id and record.product_id.company_id) or self.env.company
            # Read the logo field explicitly
            if company:
                logo = company.logo
                if logo:
                    record.company_logo_image = logo
                    # Also create data URI for direct use in templates
                    # The logo is already base64 encoded, just need to add the data URI prefix
                    try:
                        logo_b64 = logo.decode('utf-8') if isinstance(logo, bytes) else str(logo)
                        record.company_logo_data_uri = f"data:image/png;base64,{logo_b64}"
                    except Exception:
                        record.company_logo_data_uri = False
                else:
                    record.company_logo_image = False
                    record.company_logo_data_uri = False
            else:
                record.company_logo_image = False
                record.company_logo_data_uri = False

    def action_open_label_layout(self):
        """Open the label layout wizard for printing serial number barcodes"""
        # Try to get the view, but don't fail if it doesn't exist
        view_id = False
        try:
            view_id = self.env.ref('product.product_label_layout_form_view').id
        except ValueError:
            # If the view doesn't exist, get the default form view for the model
            try:
                views = self.env['ir.ui.view'].search([
                    ('model', '=', 'product.label.layout'),
                    ('type', '=', 'form')
                ], limit=1, order='priority desc, id')
                if views:
                    view_id = views[0].id
            except Exception:
                pass
        
        action = {
            'name': 'Choose Labels Layout',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.label.layout',
            'target': 'new',
            'context': {
                'default_product_ids': [],
                'default_lot_ids': self.ids,
                'default_print_format': '4x7',
            }
        }
        
        if view_id:
            action['views'] = [(view_id, 'form')]
            action['view_id'] = view_id
        
        return action
