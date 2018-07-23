# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _


PYTHON_CODE_DEFAULT = """
# <self> is the project for which this indicator is computed
# <date> is the date at which the computation is done
# <sales> is a recordset representing all sales related to the project
# <invoices> is a recordset representing all invoices related to the project
# <analytic_lines> is a recordset representing all analytic lines
#                  related to the project
# <timesheets> is a recordset representing all timesheets
#               related to the project
# <non_timesheets> is a recordset representing all analytic lines
#                  that are not timesheets related to the project
# <green>, <orange> and <red> are strings containing the RGB code of colors
#
# The code must set the value of the following variables
# <value>: a float or boolean or string
#         (depending on the value_type of the indicator)
# <color>: a string containing the RGB code associated
#         to the value of the indicator

"""

INDICATOR_STATUS = [('ok', 'OK'),
                    ('to_monitor', 'To monitor'),
                    ('warning', 'Warning'),
                    ]

INDICATOR_COLORS = {
    'ok': 'green',
    'to_monitor': 'orange',
    'warning': 'red',
}

TASK_FIELDS_TO_SYNC = {
    'user_id': 'm2o',
    'date_deadline': 'simple',
    'progress': 'simple',
    'planned_hours': 'simple',
    'kanban_state': 'simple',
    'stage_id': 'm2o',
}
