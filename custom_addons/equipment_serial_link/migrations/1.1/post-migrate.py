from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    cr.execute("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'maintenance_request' AND column_name = 'service_company_id'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE maintenance_request
            ADD COLUMN service_company_id integer
        """)

    cr.execute("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'maintenance_request' AND column_name = 'customer_company_type'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE maintenance_request
            ADD COLUMN customer_company_type varchar
        """)

    cr.execute("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'maintenance_request' AND column_name = 'service_company_type'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE maintenance_request
            ADD COLUMN service_company_type varchar
        """)
