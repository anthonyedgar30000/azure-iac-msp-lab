from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_azure_mcp_post_merge_sync.py"


class AzureMcpPostMergeSyncTests(unittest.TestCase):
    def test_reconciliation_is_fail_closed(self) -> None:
        record = json.loads(
            (ROOT / ".project" / "reconciliations" / "azure-mcp-pr74.json").read_text(encoding="utf-8")
        )
        runtime = record["runtime_claims"]
        self.assertFalse(runtime["remote_endpoint_deployed"])
        self.assertIsNone(runtime["endpoint_url"])
        self.assertFalse(runtime["client_path_selected"])
        self.assertFalse(runtime["client_connected"])
        self.assertFalse(runtime["azure_authentication_authorized"])
        self.assertEqual(runtime["tool_names_admitted"], [])
        self.assertEqual(runtime["azure_runtime_state"], "not_observed")

    def test_newer_planner_evidence_is_preserved(self) -> None:
        active = json.loads((ROOT / ".project" / "active-work.json").read_text(encoding="utf-8"))
        independent = active["deployment_state"]["independent_demo_api"]
        self.assertEqual(independent["last_planner_run_id"], 30064289707)
        self.assertTrue(independent["azure_authentication_succeeded"])
        self.assertFalse(independent["requested_sku_unrestricted"])
        self.assertEqual(independent["requested_sku_restriction_reason"], "NotAvailableForSubscription")
        self.assertFalse(independent["arm_validation_performed"])
        self.assertFalse(independent["what_if_performed"])
        self.assertFalse(independent["deployed"])
        self.assertEqual(
            active["safe_next_gate"]["operation"],
            "select_candidate_and_authorize_fresh_read_only_planner",
        )

    def test_reconciliation_does_not_replace_shared_project_state(self) -> None:
        record = json.loads(
            (ROOT / ".project" / "reconciliations" / "azure-mcp-pr74.json").read_text(encoding="utf-8")
        )
        integration = record["repository_integration"]
        self.assertFalse(integration["active_work_modified"])
        self.assertFalse(integration["environment_state_modified"])
        self.assertFalse(integration["current_project_handoff_modified"])
        self.assertEqual(
            integration["dedicated_handoff"],
            ".project/handoffs/azure-mcp-current-state.md",
        )

    def test_base_contract_still_denies_tools_and_authentication(self) -> None:
        contract = json.loads(
            (ROOT / ".project" / "contracts" / "azure-mcp-reality-bridge.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["tool_admission"]["allowed_tool_names"], [])
        self.assertFalse(contract["authority"]["azure_authentication_authorized"])
        self.assertFalse(contract["transport"]["remote_endpoint_deployed"])
        self.assertIsNone(contract["transport"]["endpoint_url"])

    def test_validator_executes(self) -> None:
        spec = importlib.util.spec_from_file_location("azure_mcp_post_merge_sync", MODULE_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.main(), 0)


if __name__ == "__main__":
    unittest.main()
