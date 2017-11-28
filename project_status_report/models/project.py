# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.depends('report_ids')
    def _compute_report_count(self):
        for rec in self:
            rec.report_count = len(rec.report_ids)

    report_ids = fields.One2many(comodel_name='project.status.report',
                                 inverse_name='project_id',
                                 string='Reports')
    report_count = fields.Integer(compute='_compute_report_count')

    @api.multi
    def action_generate_report(self):
        """Create a draft status report for project at the current date.

        Give 'status_report_creation'=True in the context
        """
        report_obj = self.env['project.status.report']
        today = fields.Date.today()
        for project in self:
            report_obj.with_context(status_report_creation=True).create(
                {
                    'date': today,
                    'project_id': project.id,
                }
            )

    @api.model
    def action_generate_report_cron(self):
        return self.search([]).action_generate_report()
