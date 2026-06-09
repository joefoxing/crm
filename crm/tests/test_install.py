from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.install import create_antek_partner_role_fields


class IntegrationTestInstall(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_create_antek_partner_role_fields_creates_fields(self):
		with patch("frappe.custom.doctype.custom_field.custom_field.create_custom_fields") as mock_create:
			create_antek_partner_role_fields()
			mock_create.assert_called_once()
			call_args = mock_create.call_args[0][0]
			self.assertIn("CRM Organization", call_args)
			self.assertIn("Contact", call_args)
			# Check that partner_role field is defined for CRM Organization
			crm_org_fields = call_args.get("CRM Organization", [])
			partner_role_fields = [f for f in crm_org_fields if f.get("fieldname") == "partner_role"]
			self.assertEqual(len(partner_role_fields), 1)
			self.assertEqual(partner_role_fields[0].get("fieldtype"), "Select")
