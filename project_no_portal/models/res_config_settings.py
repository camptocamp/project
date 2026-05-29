# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    block_project_portal_access = fields.Boolean(
        related="company_id.block_project_portal_access",
        readonly=False,
        string="Block portal access to projects and tasks",
        help="When enabled, portal users of the selected company cannot read "
        "its projects or tasks, and portal visibility cannot be set on them.",
    )

    def set_values(self):
        res = super().set_values()
        # Re-sync the global share actions with the per-company flags.
        enabled = bool(
            self.env["res.company"]
            .sudo()
            .search_count([("block_project_portal_access", "=", False)], limit=1)
        )
        self.env["project.task"]._set_share_task_action(enabled)
        self.env["project.project"]._set_share_project_action(enabled)
        return res
