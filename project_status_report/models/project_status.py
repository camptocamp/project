# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo import _
from .common import INDICATOR_STATUS, INDICATOR_COLORS


class ProjectStatusReport(models.Model):
    _name = 'project.status.report'
    _inherit = ['mail.thread']
    _order = 'date desc, name'

    @api.depends('project_id', 'date')
    def _compute_name(self):
        """Compute the name of the status report.

        project_id.name + ' ' + date
        """
        for rec in self:
            rec.name = '%s %s' % (rec.project_id.name or "", rec.date)

    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('ready', 'Ready'),
                   ('published', 'Published')],
        string='Status', readonly=True, copy=False,
        index=True, track_visibility='onchange',
        default='draft')
    date = fields.Date(
        required=True,
        default=fields.Date.today,
        readonly=True,
        states={'draft': [('readonly', False)]})
    project_id = fields.Many2one(
        comodel_name='project.project',
        string="Project",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]})
    name = fields.Char(
        compute='_compute_name',
        store=True,
        readonly=True,
        states={'draft': [('readonly', False)]})
    cost_status = fields.Selection(
        selection=INDICATOR_STATUS,
        readonly=True,
        states={'draft': [('readonly', False)]})
    cost_color = fields.Char(
        readonly=True,
        compute='_compute_colors',
        store=True)
    cost_remarks = fields.Html(
        readonly=True,
        states={'draft': [('readonly', False)]})
    quality_status = fields.Selection(
        selection=INDICATOR_STATUS,
        readonly=True,
        states={'draft': [('readonly', False)]})
    quality_color = fields.Char(
        readonly=True,
        compute='_compute_colors',
        store=True)
    quality_remarks = fields.Html(
        readonly=True,
        states={'draft': [('readonly', False)]})
    delay_status = fields.Selection(
        selection=INDICATOR_STATUS,
        readonly=True,
        states={'draft': [('readonly', False)]})
    delay_color = fields.Char(
        readonly=True,
        compute='_compute_colors',
        store=True)
    delay_remarks = fields.Html(
        readonly=True,
        states={'draft': [('readonly', False)]})
    global_status = fields.Selection(
        selection=INDICATOR_STATUS,
        readonly=True,
        states={'draft': [('readonly', False)]})
    global_color = fields.Char(
        readonly=True,
        compute='_compute_colors',
        store=True)
    global_remarks = fields.Html(
        readonly=True,
        states={'draft': [('readonly', False)]})
    risks = fields.Html(
        readonly=True,
        states={'draft': [('readonly', False)]})
    user_id = fields.Many2one(
        comodel_name='res.users',
        related='project_id.user_id',
        string='User',
        store=True,
        readonly=True)
    indicator_ids = fields.One2many(
        'project.status.indicator.value',
        'report_id',
        string='Indicators',
        readonly=True)
    task_snapshot_ids = fields.One2many(
        'project.task.snapshot',
        'report_id',
        string='Task snapshots',
        readonly=True
    )

    @api.multi
    @api.depends(
        'cost_status', 'quality_status', 'delay_status', 'global_status'
    )
    def _compute_colors(self):
        for status in self:
            for attr in ['cost', 'quality', 'delay', 'global']:
                status_value = getattr(status, attr + '_status')
                setattr(
                    status,
                    attr + '_color',
                    (
                        INDICATOR_COLORS[status_value]
                        if status_value
                        else 'green'
                    )
                )

    @api.multi
    def action_confirm(self):
        self.write({
            'state': 'ready',
        })

    @api.multi
    def action_draft(self):
        self.write({
            'state': 'draft',
        })

    @api.multi
    def action_validate(self):
        self.write({'state': 'published'})

    @api.model
    def compute_indicator_values(self, project, date):
        """ Compute indicator values for all indicator defined """
        indicators = []
        for indicator in self.env['project.status.indicator'].search([]):
            indicators.append((0, 0, indicator.compute_value(project, date)))
        return indicators

    @api.model
    def create_task_snapshots(self, project):
        """ Compute task snapshots for all tasks defined on the project """
        tasks = self.env['project.task.snapshot'].browse()
        task_snap_obj = self.env['project.task.snapshot']
        for task in project.task_ids:
            tasks |= task_snap_obj.create({'task_id': task.id})
        return tasks

    @api.model
    def compute_last_statuses(self, project):
        res = {}
        fields = [
            'cost_status',
            'cost_color',
            'cost_remarks',
            'quality_status',
            'quality_color',
            'quality_remarks',
            'delay_status',
            'delay_color',
            'delay_remarks',
            'global_status',
            'global_color',
            'global_remarks',
            'risks'
        ]
        # find last report for the given project
        last_report = self.search([('project_id', '=', project.id),
                                   ('state', '=', 'published')], limit=1)
        if last_report:
            for f in fields:
                res[f] = last_report[f]

        return res

    @api.model
    def default_get(self, fields):
        result = super(ProjectStatusReport, self).default_get(fields)

        if self._context.get('active_id'):
            project = self.env['project.project'].browse(
                self._context.get('active_id'))
            result['project_id'] = project.id
            result.update(self.compute_last_statuses(project))
        return result

    @api.model
    def create(self, values):
        project = self.env['project.project'].browse(values['project_id'])

        task_snapshots = self.create_task_snapshots(project)
        indicator_values = self.sudo().compute_indicator_values(project,
                                                         values['date'])
        update_dict = {
            'indicator_ids': indicator_values,
            'task_snapshot_ids': [(6, 0, task_snapshots.ids)],
        }

        update_dict.update(values)
        update_dict.update(self.compute_last_statuses(project))

        report = super(ProjectStatusReport, self).create(update_dict)

        return report

    def get_evaluation_indicators_for_report(self):
        return [
            (_('Cost'), self.cost_color, self.cost_remarks),
            (_('Quality'), self.quality_color, self.quality_remarks),
            (_('Delay'), self.delay_color, self.delay_remarks),
            (_('Global'), self.global_color, self.global_remarks)
        ]
