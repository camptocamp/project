# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.depends("product_id", "date_order")
    def _compute_account_analytic_id(self):
        # prevent standard account_analytic_id computation
        # if order is created from project with smart button
        # providing analytic_distribution in context
        if self.env.context.get("default_analytic_distribution"):
            return True
        return super()._compute_account_analytic_id()
