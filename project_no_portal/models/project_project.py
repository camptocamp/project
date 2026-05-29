# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ProjectProject(models.Model):
    _name = "project.project"
    _inherit = ["project.project", "project.portal.block.mixin"]

    privacy_visibility = fields.Selection(
        default=lambda self: self._default_privacy_visibility()
    )

    def _default_privacy_visibility(self):
        # Core defaults to "portal"; avoid clashing with the constraint when the
        # current company blocks portal access.
        if self.env.company.block_project_portal_access:
            return "employees"
        return "portal"

    @api.constrains("privacy_visibility", "company_id")
    def _check_no_portal_visibility(self):
        for project in self:
            company = project.company_id or self.env.company
            if (
                company.block_project_portal_access
                and project.privacy_visibility == "portal"
            ):
                raise ValidationError(
                    _(
                        "Portal visibility is disabled for company %(company)s: "
                        "portal users must not access its projects or tasks.",
                        company=company.display_name,
                    )
                )

    def action_open_share_project_wizard(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        if company.block_project_portal_access:
            raise UserError(
                _(
                    "Sharing is disabled for company %(company)s: portal users "
                    "must not access its projects or tasks. An administrator can "
                    "allow it in Settings > Project.",
                    company=company.display_name,
                )
            )
        return super().action_open_share_project_wizard()

    def _set_share_project_action(self, enabled):
        """Toggle the "Share Project" action.

        "Share Project" has no contextual action in core (it is a header button,
        which this module removes), and ir.actions.act_window has no "active"
        field, so it is toggled as a cog action through binding_model_id. The
        wizard model project.share.wizard keeps its own manager-only ACL, so the
        action stays effectively manager-only without touching its groups_id.
        """
        action = self.env.ref(
            "project.project_share_wizard_action", raise_if_not_found=False
        )
        if not action:
            return
        model = self.env.ref("project.model_project_project", raise_if_not_found=False)
        if not model:
            return
        action.binding_model_id = model.id if enabled else False
