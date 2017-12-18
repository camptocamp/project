# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo import _, exceptions
from odoo.tools.safe_eval import safe_eval

import sys
import compiler
import traceback

from .common import PYTHON_CODE_DEFAULT

import logging
logger = logging.getLogger('project_status_indicator')


class ProjectStatusIndicator(models.Model):
    _name = 'project.status.indicator'

    _order = 'sequence'

    active = fields.Boolean(
        string='Active',
        default=True,
    )
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    value_type = fields.Selection(selection=[('numeric', _('Numeric')),
                                             ('boolean', _('Boolean')),
                                             ('text', _('Text')),
                                             ('date', _('Date')),
                                             ],
                                  required=True,
                                  )
    python_code = fields.Text(default=PYTHON_CODE_DEFAULT)

    @api.multi
    @api.constrains('python_code')
    def _check_python_code_syntax(self):
        """
        Syntax check the python code of a step
        """
        for step in self:
            try:
                # Here we just want to check the code is interpretable,
                # but we don't want to execute it.
                # So compiler.parse is a good way to that.
                compiler.parse(step.python_code)
            except SyntaxError, exception:
                logger.error(''.join(traceback.format_exception(
                    sys.exc_type,
                    sys.exc_value,
                    sys.exc_traceback,
                )))
                raise exceptions.ValidationError(
                    _('Error in python code for step "%s"'
                      ' at line %d, offset %d:\n%s') % (
                        step.name,
                        exception.lineno,
                        exception.offset,
                        exception.msg,
                    ))

        return True

    @api.model
    def _construct_env_dict(self, project, date, **kwargs):
        analytic_account = project.analytic_account_id
        invoices = self.env['account.invoice.line'].search(
            [('account_analytic_id', '=', analytic_account.id)
             ]).mapped('invoice_id')
        sales = self.env['sale.order'].search(
            [('project_id', '=', analytic_account.id)]
        )
        analytic_lines = self.env['account.analytic.line'].search(
            [('account_id', '=', analytic_account.id)]
        )
        timesheets = analytic_lines.filtered(lambda a: a.is_timesheet)
        non_timesheets = analytic_lines - timesheets

        ld = {
            'self': project,
            'date': date,
            'sales': sales,
            'invoices': invoices,
            'analytic_lines': analytic_lines,
            'timesheets': timesheets,
            'non_timesheets': non_timesheets,
            'green': '#00FF00',
            'orange': '#FF6600',
            'red': '#FF0000',
            'color': '#00FF00',
            'value': None
        }
        if kwargs:
            ld.update(kwargs)

        return ld

    @api.multi
    def compute_value(self, project, date):
        ld = self._construct_env_dict(project, date)

        safe_eval(self.python_code.strip(), ld,
                  mode="exec", nocopy=True)
        ld.get('color', None)
        ld.get('value', None)

        vals = {
            'indicator_id': self.id,
            'color': ld.get('color', '#00FF00'),
            ('value_%s' % self.value_type): ld.get('value', None),
        }

        return vals


class ProjectStatusIndicatorValue(models.Model):
    _name = 'project.status.indicator.value'

    _order = 'project_id, date, sequence'

    @api.depends(
        'value_type',
        'value_boolean',
        'value_numeric',
        'value_text',
        'value_date',
    )
    def _compute_display_value(self):
        for rec in self:
            rec.display_value = str(rec['value_' + rec.value_type])

    indicator_id = fields.Many2one(comodel_name='project.status.indicator',
                                   required=True,
                                   string='Indicator')
    report_id = fields.Many2one(comodel_name='project.status.report',
                                string='Report',
                                ondelete='cascade',
                                )
    project_id = fields.Many2one(comodel_name='project.project',
                                 related='report_id.project_id',
                                 string='Project',
                                 store=True,
                                 readonly=True)
    date = fields.Date(related='report_id.date',
                       store=True,
                       readonly=True
                       )
    name = fields.Char(related='indicator_id.name',
                       store=True,
                       readonly=True)
    sequence = fields.Integer(related='indicator_id.sequence',
                              store=True,
                              readonly=True)
    value_type = fields.Selection(related='indicator_id.value_type',
                                  store=True,
                                  readonly=True)
    value_numeric = fields.Float()
    value_boolean = fields.Boolean()
    value_text = fields.Text()
    value_date = fields.Date()
    display_value = fields.Char(string='Value',
                                compute='_compute_display_value')
    color = fields.Char(size=7, required=True)

    _sql_constraint = [('unique value per indicator report',
                        'UNIQUE (indicator_id, report_id)',
                        'Value must be unique per indicator/report')]

    @api.model
    def create(self, values):
        """
            allow users != admin to create records only if the context
            contains the key 'status_report_creation'=True
        """
        if self.env.user._is_superuser():
            if not self.env.context.get('status_report_creation', False):
                raise exceptions.AccessError(
                    _(
                        'User %s (id %s) is not allowed '
                        'to create an indicator value'
                    ) % (self.env.user.name, self.env.uid)
                )

        return super(ProjectStatusIndicatorValue, self).create(values)

    @api.multi
    def write(self, values):
        """
        allow users != admin to write records only if the context
        contains the key 'status_report_creation'=True
        """
        if self.env.user._is_superuser():
            if not self.env.context.get('status_report_creation', False):
                raise exceptions.AccessError(
                    _(
                        'User %s (id %s) is not allowed '
                        'to write an indicator value'
                    ) % (self.env.user.name, self.env.uid)
                )
        return super(ProjectStatusIndicatorValue, self).write(values)
