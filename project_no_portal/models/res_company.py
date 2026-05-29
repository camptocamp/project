# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    block_project_portal_access = fields.Boolean(
        string="Block portal access to projects and tasks",
        default=False,
        help="When enabled, portal users of this company cannot read its "
        "projects or tasks, and portal visibility cannot be set on them.",
    )
