import hmac
import json
from hashlib import sha256
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from crm.antek_materials.integrations.fastapi_sync import (
	build_signature,
	push_credit_status,
)


class UnitTestBuildSignature(UnitTestCase):
	def test_build_signature_matches_hmac_sha256(self):
		payload = {"contract_id": "HD-3B-2026-001", "current_debt": 1000}
		secret = "secret-key"
		expected = hmac.new(
			secret.encode(),
			json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(),
			sha256,
		).hexdigest()
		self.assertEqual(build_signature(payload, secret), expected)


class IntegrationTestPushCreditStatus(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_push_credit_status_skips_when_sync_disabled(self):
		with patch("frappe.get_single") as mock_get_single:
			mock_settings = MagicMock()
			mock_settings.sync_enabled = False
			mock_get_single.return_value = mock_settings

			with patch("frappe.make_post_request") as mock_post:
				payload = {"event": "credit_status_changed", "contract_id": "HD-123"}
				push_credit_status(payload, "event-123")
				mock_post.assert_not_called()

	def test_push_credit_status_makes_request_when_enabled(self):
		with patch("frappe.get_single") as mock_get_single:
			mock_settings = MagicMock()
			mock_settings.sync_enabled = True
			mock_settings.get_password.return_value = "secret-key"
			mock_settings.fastapi_webhook_url = "https://api.example.com/webhook"
			mock_settings.request_timeout_seconds = 10
			mock_get_single.return_value = mock_settings

			with patch("frappe.make_post_request") as mock_post:
				payload = {"event": "credit_status_changed", "contract_id": "HD-123"}
				push_credit_status(payload, "event-456")
				mock_post.assert_called_once()
				call_kwargs = mock_post.call_args[1]
				self.assertEqual(call_kwargs["url"], "https://api.example.com/webhook")
				self.assertIn("X-AnTek-Signature", call_kwargs["headers"])
				self.assertEqual(call_kwargs["headers"]["X-AnTek-Event-Id"], "event-456")
				self.assertEqual(call_kwargs["timeout"], 10)
