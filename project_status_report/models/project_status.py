# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo import _
from .common import INDICATOR_STATUS


class ProjectStatusReport(models.Model):
    _name = 'project.status.report'
    _inherit = ['mail.thread']
    _order = 'date desc, name'

    @api.depends('project_id', 'date')
    def _compute_name(self):
        """
        Compute the name of the status report.
        project_id.name + ' ' + date
        """
        for rec in self:
            rec.name = '%s %s' % (self.project_id.name or "", self.date)

    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('ready', _('Ready')),
                                        ('published', _('Published'))
                                        ],
                             string='Status', readonly=True, copy=False,
                             index=True, track_visibility='onchange',
                             default='draft'
                             )
    date = fields.Date(required=True,
                       default=fields.Date.today(),
                       readonly=True,
                       states={'draft': [('readonly', False)]})
    project_id = fields.Many2one(comodel_name='project.project',
                                 string="Project",
                                 required=True,
                                 readonly=True,
                                 states={'draft': [('readonly', False)]})
    name = fields.Char(compute='_compute_name',
                       store=True,
                       readonly=True,
                       states={'draft': [('readonly', False)]})
    cost_status = fields.Selection(selection=INDICATOR_STATUS,
                                   readonly=True,
                                   states={'draft': [('readonly', False)]})
    cost_color = fields.Char(readonly=True,
                             default='#00ff00',
                             states={'draft': [('readonly', False)]})
    cost_remarks = fields.Html(readonly=True,
                               states={'draft': [('readonly', False)]})
    quality_status = fields.Selection(selection=INDICATOR_STATUS,
                                      readonly=True,
                                      states={'draft': [('readonly', False)]})
    quality_color = fields.Char(readonly=True,
                                default='#00ff00',
                                states={'draft': [('readonly', False)]})
    quality_remarks = fields.Html(readonly=True,
                                  states={'draft': [('readonly', False)]})
    delay_status = fields.Selection(selection=INDICATOR_STATUS,
                                    readonly=True,
                                    states={'draft': [('readonly', False)]})
    delay_color = fields.Char(readonly=True,
                              default='#00ff00',
                              states={'draft': [('readonly', False)]})
    delay_remarks = fields.Html(readonly=True,
                                states={'draft': [('readonly', False)]})
    global_status = fields.Selection(selection=INDICATOR_STATUS,
                                     readonly=True,
                                     states={'draft': [('readonly', False)]})
    global_color = fields.Char(readonly=True,
                               default='#00ff00',
                               states={'draft': [('readonly', False)]})
    global_remarks = fields.Html(readonly=True,
                                 states={'draft': [('readonly', False)]})
    risks = fields.Html(readonly=True,
                        states={'draft': [('readonly', False)]})
    user_id = fields.Many2one(comodel_name='res.users',
                              related='project_id.user_id',
                              store=True,
                              readonly=True)
    indicator_ids = fields.One2many('project.status.indicator.value',
                                    'report_id',
                                    readonly=True,
                                    states={'draft': [('readonly', False)]})
    task_snapshot_ids = fields.One2many(
        'project.task.snapshot',
        'report_id',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    @api.multi
    def action_confirm(self):
        self.state = 'ready'

    @api.multi
    def action_validate(self):
        self.state = 'published'

    @api.model
    def compute_indicator_values(self, project, date):
        indicators = self.env['project.status.indicator.value'].browse()
        for indicator in self.env['project.status.indicator'].search([]):
            indicators |= indicator.compute_value(project, date)
        return indicators

    @api.model
    def create_task_snapshots(self, project):
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
        indicator_values = self.compute_indicator_values(project,
                                                         values['date'])
        update_dict = {
            'indicator_ids': [(6, 0, indicator_values.ids)],
            'task_snapshot_ids': [(6, 0, task_snapshots.ids)],
        }

        update_dict.update(values)
        update_dict.update(self.compute_last_statuses(project))
        report = super(ProjectStatusReport, self).create(update_dict)

        return report
