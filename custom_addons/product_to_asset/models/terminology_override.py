# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def _setup_product_to_asset_translations(env):
    """Setup Product → Asset terminology translations"""
    
    # Core translation terms mapping - most common product-related terms
    translations = [
        ('Product', 'Asset'),
        ('Products', 'Assets'),
        ('product', 'asset'),
        ('products', 'assets'),
        ('Product Template', 'Asset Template'),
        ('Product Templates', 'Asset Templates'),
        ('Product Category', 'Asset Category'),
        ('Product Categories', 'Asset Categories'),
        ('Product Variant', 'Asset Variant'),
        ('Product Variants', 'Asset Variants'),
        ('Product Name', 'Asset Name'),
        ('Product Type', 'Asset Type'),
        ('Product Code', 'Asset Code'),
        ('Product Description', 'Asset Description'),
        ('Product Information', 'Asset Information'),
        ('Product Details', 'Asset Details'),
        ('Product Settings', 'Asset Settings'),
        ('New Product', 'New Asset'),
        ('Create Product', 'Create Asset'),
        ('Edit Product', 'Edit Asset'),
        ('Delete Product', 'Delete Asset'),
        ('Product Manager', 'Asset Manager'),
        ('Product Cost', 'Asset Cost'),
        ('Product Price', 'Asset Price'),
        ('Product Sale Price', 'Asset Sale Price'),
        ('Product Purchase Price', 'Asset Purchase Price'),
        ('Product Stock', 'Asset Stock'),
        ('Product Inventory', 'Asset Inventory'),
        ('Product Location', 'Asset Location'),
        ('Product Warehouse', 'Asset Warehouse'),
        ('Product Lot', 'Asset Lot'),
        ('Product Serial Number', 'Asset Serial Number'),
        ('Product Barcode', 'Asset Barcode'),
        ('Product Image', 'Asset Image'),
        ('Product Images', 'Asset Images'),
        ('Product Attributes', 'Asset Attributes'),
        ('Product Attribute', 'Asset Attribute'),
        ('Product UOM', 'Asset UOM'),
        ('Product Unit of Measure', 'Asset Unit of Measure'),
        ('Product Weight', 'Asset Weight'),
        ('Product Volume', 'Asset Volume'),
        ('Product Dimensions', 'Asset Dimensions'),
        ('Product Supplier', 'Asset Supplier'),
        ('Product Suppliers', 'Asset Suppliers'),
        ('Product Vendor', 'Asset Vendor'),
        ('Product Vendors', 'Asset Vendors'),
        ('Product Customer', 'Asset Customer'),
        ('Product Customers', 'Asset Customers'),
        ('Product Route', 'Asset Route'),
        ('Product Routes', 'Asset Routes'),
        ('Product Pricelist', 'Asset Pricelist'),
        ('Product Pricelists', 'Asset Pricelists'),
        ('Product Tag', 'Asset Tag'),
        ('Product Tags', 'Asset Tags'),
        ('Product Brand', 'Asset Brand'),
        ('Product Brands', 'Asset Brands'),
        ('Product Model', 'Asset Model'),
        ('Product Models', 'Asset Models'),
        ('Product Reference', 'Asset Reference'),
        ('Product Internal Reference', 'Asset Internal Reference'),
        ('Product Default Code', 'Asset Default Code'),
        ('Product Quantity', 'Asset Quantity'),
        ('Product Quantities', 'Asset Quantities'),
        ('Product Qty', 'Asset Qty'),
        ('Product Status', 'Asset Status'),
        ('Product Statuses', 'Asset Statuses'),
        ('Product State', 'Asset State'),
        ('Product States', 'Asset States'),
        ('Product Depreciation', 'Asset Depreciation'),
        ('Product Depreciation Method', 'Asset Depreciation Method'),
        ('Product Useful Life', 'Asset Useful Life'),
        ('Product Fair Value', 'Asset Fair Value'),
        ('Product Disposal Date', 'Asset Disposal Date'),
        ('Product Disposal Price', 'Asset Disposal Price'),
        ('Product Net Book Value', 'Asset Net Book Value'),
        ('Product Serial Status', 'Asset Serial Status'),
        ('Product Serial Statuses', 'Asset Serial Statuses'),
    ]
    
    # Get or create translations for each term
    for src_term, value_term in translations:
        # Search for existing translations with this source term
        existing = env['ir.translation'].search([
            ('lang', '=', 'en_US'),
            ('src', '=', src_term),
            ('type', 'in', ['model', 'model_terms', 'code'])
        ])
        
        # Update existing translations
        if existing:
            existing.write({'value': value_term})
        
        # Also create a generic code translation for the term
        # Check if it already exists to avoid duplicates
        existing_code = env['ir.translation'].search([
            ('type', '=', 'code'),
            ('name', '=', 'product_to_asset'),
            ('lang', '=', 'en_US'),
            ('src', '=', src_term),
            ('module', '=', 'product_to_asset')
        ])
        
        if not existing_code:
            try:
                env['ir.translation'].create({
                    'type': 'code',
                    'name': 'product_to_asset',
                    'lang': 'en_US',
                    'src': src_term,
                    'value': value_term,
                    'state': 'translated',
                    'module': 'product_to_asset',
                })
            except Exception:
                # Ignore duplicate key errors
                pass

