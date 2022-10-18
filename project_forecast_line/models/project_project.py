# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ProjectProject(models.Model):
    _inherit = "project.project"

    def _update_forecast_lines_trigger_fields(self):
        return ["stage_id"]

    def _get_written_computed_fields(self, values):
        # get written and computed field names
        task_computed = []
        written_fields = list(values.keys())
        tree = self.pool.field_triggers.get(self._fields[next(iter(written_fields))])
        tocompute = self.sudo().with_context(active_test=False)._modified_triggers(tree)
        for field, _records, _create in tocompute:
            if field.model_name == "project.project":
                task_computed.append(field.name)
        return written_fields + task_computed

    def write(self, values):
        res = super().write(values)
        written_computed_fields = self._get_written_computed_fields(values)
        trigger_fields = self._update_forecast_lines_trigger_fields()
        if any(field in written_computed_fields for field in trigger_fields):
            self.task_ids._update_forecast_lines()
        return res
