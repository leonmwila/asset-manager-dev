# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def _setup_ministry_translations(env):
    """Setup Company → Ministry terminology translations"""
    
    # Translation terms mapping
    translations = [
        ('Company', 'Ministry'),
        ('Companies', 'Ministries'),
        ('Allowed Companies', 'Allowed Ministries'),
        ('company', 'ministry'),
        ('companies', 'ministries'),
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
        env['ir.translation'].create({
            'type': 'code',
            'name': 'company_extension',
            'lang': 'en_US',
            'src': src_term,
            'value': value_term,
            'state': 'translated',
            'module': 'company_extension',
        })
