# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import exceptions, _
from odoo import SUPERUSER_ID

from .common import TASK_FIELDS_TO_SYNC


class ProjectTaskSnapshot(models.Model):
    _name = 'project.task.snapshot'

    report_id = fields.Many2one(comodel_name='project.status.report',
                                string='Report')
    project_id = fields.Many2one(comodel_name='project.project',
                                 related='report_id.project_id',
                                 store=True,
                                 readonly=True)
    task_id = fields.Many2one(comodel_name='project.task',
                              string='Task',
                              required=True,)
    name = fields.Char(related='task_id.name', readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User')
    date_deadline = fields.Date()
    progress = fields.Float()
    planned_hours = fields.Float()
    kanban_state = fields.Selection([('normal', 'In Progress'),
                                     ('done', 'Ready for next stage'),
                                     ('blocked', 'Blocked')],
                                    string='Kanban State',
                                    )
    stage_id = fields.Many2one(comodel_name='project.task.type',
                               string='Stage')

    def _prepare_update_vals(self, task):
        """
        prepare dict value to make a snapshot of a task
        """
        res = task.read(TASK_FIELDS_TO_SYNC.keys(), load='_classic_write')[0]
        del res['id']
        return res

    @api.onchange('task_id')
    def onchange_task_id(self):
        if self.task_id:
            vals = self._prepare_update_vals(self.task_id)
            self.update(vals)

    @api.model
    def create(self, values):
        """
            allow users != admin to create records only if the context
            contains the key 'status_report_creation'=True
        """
        if self.env.user.id != SUPERUSER_ID:
            if not self.env.context.get('status_report_creation', False):
                raise exceptions.AccessError(
                    _(
                        'User %s (id %s) is not allowed '
                        'to create an task snapshot'
                    ) % (self.env.user.name, self.env.uid)
                )

        record = super(ProjectTaskSnapshot, self).create(values)
        record.onchange_task_id()
        return record

    @api.multi
    def write(self, values):
        """
        allow users != admin to write records only if the context
        contains the key 'status_report_creation'=True
        """
        if self.env.user.id != SUPERUSER_ID:
            if not self.env.context.get('status_report_creation', False):
                raise exceptions.AccessError(
                    _(
                        'User %s (id %s) is not allowed '
                        'to write an task snapshot'
                    ) % (self.env.user.name, self.env.uid)
                )
        return super(ProjectTaskSnapshot, self).write(values)
