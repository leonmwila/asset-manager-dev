FROM odoo:19

USER root

COPY odoo/addons/ /mnt/extra-addons/
COPY custom_addons/ /mnt/custom-addons/
COPY odoo/config/odoo.conf /etc/odoo/odoo.conf

RUN chown -R odoo:odoo /mnt/extra-addons /mnt/custom-addons /etc/odoo/odoo.conf

USER odoo

CMD ["odoo", "-c", "/etc/odoo/odoo.conf"]
