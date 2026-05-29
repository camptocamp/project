# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestProjectNoPortal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.company
        # The block is opt-in (off by default); enable it for the company so the
        # blocking tests exercise the feature. The "company allows" tests flip it
        # back off.
        cls.company.block_project_portal_access = True
        cls.portal_group = cls.env.ref("base.group_portal")
        cls.portal_partner = cls.env["res.partner"].create(
            {
                "name": "Portal Tester Partner",
                "email": "portal.tester@example.com",
            }
        )
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Portal Tester",
                "login": "portal.tester@example.com",
                "partner_id": cls.portal_partner.id,
                "company_id": cls.company.id,
                "company_ids": [(6, 0, [cls.company.id])],
                "groups_id": [(6, 0, [cls.portal_group.id])],
            }
        )

        cls.project = cls.env["project.project"].create(
            {
                "name": "Test No Portal Project",
                "privacy_visibility": "employees",
                "company_id": cls.company.id,
            }
        )
        cls.task = cls.env["project.task"].create(
            {
                "name": "Test No Portal Task",
                "project_id": cls.project.id,
            }
        )

        cls.PortalProject = cls.env["project.project"].with_user(cls.portal_user)
        cls.PortalTask = cls.env["project.task"].with_user(cls.portal_user)

    def _set_block(self, enabled):
        self.company.block_project_portal_access = enabled

    def _force_portal_visibility(self):
        """Set privacy_visibility='portal' via raw SQL to bypass the python
        constraint and simulate data that predates the block (or was created
        while the block was off)."""
        self.env.cr.execute(
            "UPDATE project_project SET privacy_visibility=%s WHERE id=%s",
            ("portal", self.project.id),
        )
        self.env.invalidate_all()

    def _follow_as_portal(self):
        self.project.message_subscribe(partner_ids=[self.portal_partner.id])
        self.task.message_subscribe(partner_ids=[self.portal_partner.id])

    # --- company blocks -----------------------------------------------------

    def test_block_on_constraint_rejects_portal_visibility(self):
        with self.assertRaises(ValidationError):
            self.env["project.project"].create(
                {
                    "name": "Portal",
                    "privacy_visibility": "portal",
                    "company_id": self.company.id,
                }
            )

    def test_default_visibility_is_employees(self):
        project = self.env["project.project"].create({"name": "Default Visibility"})
        self.assertEqual(project.privacy_visibility, "employees")

    def test_block_on_share_wizard_raises(self):
        with self.assertRaises(UserError):
            self.project.action_open_share_project_wizard()

    def test_block_on_python_layer_denies_even_with_portal_data(self):
        """Even if a project slips to privacy_visibility='portal' through a path
        that skips the constraint (raw SQL here), the python block denies portal
        users at search and direct-read time."""
        self._force_portal_visibility()
        self._follow_as_portal()

        self.assertFalse(self.PortalProject.search([("id", "=", self.project.id)]))
        self.assertFalse(self.PortalTask.search([("id", "=", self.task.id)]))
        with self.assertRaises(AccessError):
            self.PortalProject.browse(self.project.id).check_access("read")
        with self.assertRaises(AccessError):
            self.PortalTask.browse(self.task.id).check_access("read")

    # --- company allows ------------------------------------------------------

    def test_block_off_share_wizard_opens(self):
        self._set_block(False)
        self.project.privacy_visibility = "portal"
        action = self.project.action_open_share_project_wizard()
        self.assertEqual(action.get("res_model"), "project.share.wizard")

    def test_share_task_action_binding_toggle(self):
        action = self.env.ref("project.portal_share_action")

        self.env["project.task"]._set_share_task_action(False)
        self.assertFalse(action.binding_model_id)

        self.env["project.task"]._set_share_task_action(True)
        self.assertEqual(
            action.binding_model_id, self.env.ref("project.model_project_task")
        )

    def test_share_project_action_binding_toggle(self):
        action = self.env.ref("project.project_share_wizard_action")

        self.env["project.project"]._set_share_project_action(True)
        self.assertEqual(
            action.binding_model_id, self.env.ref("project.model_project_project")
        )

        self.env["project.project"]._set_share_project_action(False)
        self.assertFalse(action.binding_model_id)

    def test_block_off_portal_follower_can_access(self):
        """With the company's block off, standard Odoo behaviour is restored: a
        portal follower of a 'portal' project can read it and its tasks. Relies
        on the core portal ACLs still being present (we never deleted them)."""
        self._set_block(False)
        self.project.privacy_visibility = "portal"
        self._follow_as_portal()

        self.assertTrue(self.PortalProject.search([("id", "=", self.project.id)]))
        self.assertTrue(self.PortalTask.search([("id", "=", self.task.id)]))
