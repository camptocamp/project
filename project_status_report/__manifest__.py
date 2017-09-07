# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Project Status Report",
    "summary": "Adds a customizable indicator-based reporting for project",
    "version": "10.0.1.0.0",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Project Management",
    "website": "http://www.camptocamp.com",
    "depends": ["project", "web_widget_color"],
    "data": [
        'security/ir.model.access.csv',
        'data/ir_rules.xml',
        'views/project_status_report.xml',
        'views/project_status_indicator.xml',
        'views/project.xml',
        'data/cron.xml',
        'data/project_status_indicator.xml',
    ],
    "installable": True,
}
