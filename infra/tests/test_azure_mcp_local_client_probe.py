from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from azure_mcp_reality.local_client_probe import run_probe


ROOT = Path(__file__).resolve().parents[2]
PROBE_PATH = ROOT / "azure_mcp_reality" / "local_client_probe.py"


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AzureMcpLocalClientProbeTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_client_calls_only_repository_lab_factory_tools(self) -> None:
        receipt = await run_probe()

        self.assertEqual(receipt["schema_version"], "azure-mcp.local-client-probe.v1")
        self.assertEqual(receipt["transport"]["type"], "stdio_subprocess")
        self.assertFalse(receipt["transport"]["network_listener_created"])
        self.assertFalse(receipt["transport"]["remote_endpoint_used"])
        self.assertTrue(receipt["protocol"]["initialized"])
        self.assertEqual(
            receipt["tool_inventory"],
            [
                "get_current_reality",
                "list_lab_profiles",
                "prepare_lab_request",
            ],
        )

        listed = receipt["calls"]["list_lab_profiles"]
        self.assertFalse(listed["is_error"])
        self.assertEqual(listed["profile_ids"], ["servicetracer-demo-api"])
        self.assertEqual(listed["release_states"], ["candidate"])

        prepared = receipt["calls"]["prepare_lab_request"]
        self.assertFalse(prepared["is_error"])
        self.assertEqual(prepared["operation"], "prepare_only")
        self.assertEqual(prepared["resource_group"], "rg-st-demo-api-test-westus2")
        self.assertEqual(prepared["missing_required_parameters"], [])
        self.assertTrue(prepared["ready_for_preflight"])
        self.assertTrue(prepared["what_if_required"])
        self.assertTrue(prepared["explicit_deployment_authorization_required"])
        self.assertEqual(prepared["next_gate"], "preflight_required")
        self.assertRegex(prepared["plan_digest"], r"^sha256:[0-9a-f]{64}$")

        negative = receipt["negative_evidence"]
        self.assertFalse(negative["get_current_reality_called"])
        self.assertFalse(negative["azure_credentials_forwarded_to_server"])
        self.assertFalse(negative["azure_authentication_performed"])
        self.assertFalse(negative["azure_queries_performed"])
        self.assertFalse(negative["azure_mutations_performed"])
        self.assertFalse(negative["arm_what_if_performed"])
        self.assertFalse(negative["deployment_authorized"])
        self.assertFalse(negative["deployment_performed"])
        self.assertFalse(negative["model_call_performed"])
        self.assertFalse(negative["remote_mcp_endpoint_deployed"])
        self.assertFalse(negative["chatgpt_connection_configured"])
        self.assertFalse(negative["cleanup_authorized"])
        self.assertFalse(negative["cleanup_performed"])

        digest = receipt.pop("receipt_digest")
        expected = "sha256:" + hashlib.sha256(
            _canonical_json(receipt).encode("utf-8")
        ).hexdigest()
        self.assertEqual(digest, expected)

    def test_probe_has_no_azure_command_or_model_client(self) -> None:
        source = PROBE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "az account",
            "az group",
            "az resource",
            "az deployment",
            "OpenAI(",
            "AzureOpenAI(",
            "responses.create",
            "streamable_http_client",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn('session.call_tool("list_lab_profiles"', source)
        self.assertIn('session.call_tool(\n                "prepare_lab_request"', source)
        self.assertNotIn('session.call_tool("get_current_reality"', source)


if __name__ == "__main__":
    unittest.main()
