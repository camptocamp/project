# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import _, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_calendar(self, date_from=None):
        res = super()._get_calendar(date_from)
        if not date_from:
            return res

        contracts = (
            self.sudo()
            .with_context(active_test=True)
            .env["hr.contract"]
            .search([("employee_id", "=", self.id)])
        )

        if date_from:
            date_from = (
                date_from if not isinstance(date_from, datetime) else date_from.date()
            )
            contracts = contracts.filtered(lambda c: c.date_start <= date_from)

        date_to = self.env.context.get("date_to")
        if date_to:
            date_to = date_to if not isinstance(date_to, datetime) else date_to.date()
            contracts = contracts.filtered(
                lambda c: not c.date_end or c.date_end >= date_to
            )

        if contracts:
            # If only one contract, no matter it's state
            if len(contracts) == 1:
                return contracts[0].resource_calendar_id
            # But if not, do not take cancelled ones and see what's left
            contracts = contracts.filtered(lambda c: c.state != "cancel")
            if contracts:
                if len(contracts) == 1:
                    return contracts[0].resource_calendar_id
            # There are multiple contracts for this date period
            raise ValidationError(_("This period overlaps multiple contracts!"))

        return res

    def _get_work_days_data_batch(
        self,
        from_datetime,
        to_datetime,
        compute_leaves=True,
        calendar=None,
        domain=None,
    ):
        # OVERRIDE calendar in favor of the one taken from employee's contract
        # Only if one has not been already given in arguments
        result = {}
        for employee in self:
            calendar = calendar or employee.with_context(
                date_to=to_datetime
            )._get_calendar(from_datetime)
            result.update(
                super(HrEmployee, employee)._get_work_days_data_batch(
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    compute_leaves=compute_leaves,
                    calendar=calendar,
                    domain=domain,
                )
            )
        return result

    def _get_leave_days_data_batch(
        self, from_datetime, to_datetime, calendar=None, domain=None
    ):
        # OVERRIDE calendar in favor of the one taken from employee's contract
        # Only if one has not been already given in arguments
        result = {}
        for employee in self:
            calendar = calendar or employee.with_context(
                date_to=to_datetime
            )._get_calendar(from_datetime)
            result.update(
                super(HrEmployee, employee)._get_leave_days_data_batch(
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    calendar=calendar,
                    domain=domain,
                )
            )
        return result

    def list_work_time_per_day(
        self, from_datetime, to_datetime, calendar=None, domain=None
    ):
        # OVERRIDE calendar in favor of the one taken from employee's contract
        # Only if one has not been already given in arguments
        result = []
        for employee in self:
            calendar = calendar or employee.with_context(
                date_to=to_datetime
            )._get_calendar(from_datetime)
            result.extend(
                super(HrEmployee, employee).list_work_time_per_day(
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    calendar=calendar,
                    domain=domain,
                )
            )
        return result

    def list_leaves(self, from_datetime, to_datetime, calendar=None, domain=None):
        # OVERRIDE calendar in favor of the one taken from employee's contract
        # Only if one has not been already given in arguments
        result = []
        for employee in self:
            calendar = calendar or employee.with_context(
                date_to=to_datetime
            )._get_calendar(from_datetime)
            result.extend(
                super(HrEmployee, employee).list_leaves(
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    calendar=calendar,
                    domain=domain,
                )
            )
        return result
