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
        # Data
        'data/cron.xml',
        'data/ir_rules.xml',
        'data/project_status_indicator.xml',
        # Report
        'report/project_status_report.xml',
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/project_status_indicator.xml',
        'views/project_status_report.xml',
        'views/project.xml',
    ],
    "installable": True,
}
