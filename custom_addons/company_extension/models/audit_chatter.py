from odoo import _, api, models


class AuditChatterMixin(models.AbstractModel):
    _name = 'company_extension.audit_chatter_mixin'
    _description = 'Audit Chatter Logging Helpers'

    _audit_ignored_fields = {
        'message_ids',
        'message_follower_ids',
        'activity_ids',
        'activity_state',
        'activity_exception_decoration',
        'activity_exception_icon',
        'activity_user_id',
        'activity_type_id',
        'activity_date_deadline',
        'write_uid',
        'write_date',
        '__last_update',
        'display_name',
    }

    def _audit_candidate_fields(self, vals):
        return [
            key for key in vals
            if key in self._fields and key not in self._audit_ignored_fields
        ]

    def _audit_value_changed(self, field, old_value, new_value):
        if field.type == 'many2one':
            return (old_value.id if old_value else False) != (new_value.id if new_value else False)
        if field.type in ('one2many', 'many2many'):
            return set(old_value.ids) != set(new_value.ids)
        return old_value != new_value

    def _audit_format_value(self, field, value):
        if field.type == 'many2one':
            return value.display_name if value else _('empty')

        if field.type in ('one2many', 'many2many'):
            if not value:
                return _('empty')
            names = value.mapped('display_name')
            preview = ', '.join(names[:5])
            if len(names) > 5:
                preview += _(' ... (+%s more)') % (len(names) - 5)
            return preview

        if field.type == 'selection':
            if value in (False, None, ''):
                return _('empty')
            selections = field.selection
            if isinstance(selections, (list, tuple)):
                return dict(selections).get(value, value)
            return value

        if field.type == 'boolean':
            return _('Yes') if value else _('No')

        if field.type == 'binary':
            return _('binary content') if value else _('empty')

        if value in (False, None, ''):
            return _('empty')

        text = str(value)
        if len(text) > 120:
            return text[:117] + '...'
        return text

    def _post_audit_create_log(self, vals):
        changed_fields = self._audit_candidate_fields(vals)
        if not changed_fields:
            self.message_post(body=_('Record created.'))
            return

        lines = []
        for field_name in changed_fields:
            field = self._fields[field_name]
            new_value = self[field_name]
            lines.append(
                '<li><b>%s</b>: %s</li>' % (
                    field.string,
                    self._audit_format_value(field, new_value),
                )
            )

        body = _('<b>Record created</b><br/><ul>%s</ul>') % ''.join(lines)
        self.message_post(body=body)

    def _post_audit_write_logs(self, vals, old_values_by_record):
        changed_fields = self._audit_candidate_fields(vals)
        if not changed_fields:
            return

        for record in self:
            lines = []
            for field_name in changed_fields:
                field = record._fields[field_name]
                old_value = old_values_by_record[record.id][field_name]
                new_value = record[field_name]
                if not record._audit_value_changed(field, old_value, new_value):
                    continue

                lines.append(
                    '<li><b>%s</b>: %s %s %s</li>' % (
                        field.string,
                        record._audit_format_value(field, old_value),
                        '&rarr;',
                        record._audit_format_value(field, new_value),
                    )
                )

            if lines:
                body = _('<b>Record updated</b><br/><ul>%s</ul>') % ''.join(lines)
                record.message_post(body=body)


class StockLotAuditChatter(models.Model):
    _name = 'stock.lot'
    _inherit = ['stock.lot', 'company_extension.audit_chatter_mixin']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            record._post_audit_create_log(vals)
        return records

    def write(self, vals):
        changed_fields = self._audit_candidate_fields(vals)
        old_values_by_record = {
            record.id: {field_name: record[field_name] for field_name in changed_fields}
            for record in self
        }
        result = super().write(vals)
        self._post_audit_write_logs(vals, old_values_by_record)
        return result


class ProductTemplateAuditChatter(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'company_extension.audit_chatter_mixin']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            record._post_audit_create_log(vals)
        return records

    def write(self, vals):
        changed_fields = self._audit_candidate_fields(vals)
        old_values_by_record = {
            record.id: {field_name: record[field_name] for field_name in changed_fields}
            for record in self
        }
        result = super().write(vals)
        self._post_audit_write_logs(vals, old_values_by_record)
        return result


class ProductProductAuditChatter(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'company_extension.audit_chatter_mixin']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            record._post_audit_create_log(vals)
        return records

    def write(self, vals):
        changed_fields = self._audit_candidate_fields(vals)
        old_values_by_record = {
            record.id: {field_name: record[field_name] for field_name in changed_fields}
            for record in self
        }
        result = super().write(vals)
        self._post_audit_write_logs(vals, old_values_by_record)
        return result