from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    cr.execute("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'res_company' AND column_name = 'institution_type_2'
    """)
    if cr.fetchone():
        return

    cr.execute("""
        ALTER TABLE res_company
        ADD COLUMN institution_type_2 varchar
    """)
