# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import models


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "project.portal.block.mixin"]

    def _set_share_task_action(self, enabled):
        """
        Toggle the "Share Task" action, which opens portal.share.wizard
        """
        action = self.env.ref("project.portal_share_action", raise_if_not_found=False)
        if not action:
            return
        model = self.env.ref("project.model_project_task")
        action.binding_model_id = model.id if enabled else False
