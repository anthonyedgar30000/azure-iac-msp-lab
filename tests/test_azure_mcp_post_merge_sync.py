from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_azure_mcp_post_merge_sync.py"


class AzureMcpCloudShellPlanTests(unittest.TestCase):
    def test_current_contract_selects_openai_without_claiming_connection(self) -> None:
        contract = json.loads(
            (ROOT / ".project" / "contracts" / "azure-mcp-reality-bridge.json").read_text(encoding="utf-8")
        )
        selection = contract["client_paths"]["selection"]
        self.assertEqual(selection["selected_client_path"], "openai_responses_api")
        self.assertFalse(selection["configured"])
        self.assertFalse(selection["connection_observed"])
        self.assertFalse(contract["client_paths"]["openai_responses_api"]["api_execution_authorized"])

    def test_cloud_shell_and_managed_identity_are_design_choices_not_runtime(self) -> None:
        contract = json.loads(
            (ROOT / ".project" / "contracts" / "azure-mcp-reality-bridge.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["hosting"]["selected_service"], "azure_container_apps")
        self.assertEqual(contract["hosting"]["deployment_interface"], "azure_cloud_shell")
        self.assertFalse(contract["hosting"]["deployed"])
        self.assertEqual(
            contract["authentication"]["server_to_azure"]["selected_model"],
            "managed_identity_shared_service_identity",
        )
        self.assertFalse(contract["authentication"]["server_to_azure"]["implemented"])
        self.assertFalse(contract["transport"]["remote_endpoint_deployed"])
        self.assertIsNone(contract["transport"]["endpoint_url"])

    def test_tools_scopes_and_cost_remain_fail_closed(self) -> None:
        contract = json.loads(
            (ROOT / ".project" / "contracts" / "azure-mcp-reality-bridge.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["azure_scope"]["subscription_ids"], [])
        self.assertEqual(contract["azure_scope"]["resource_group_allowlist"], [])
        self.assertEqual(contract["tool_admission"]["namespace_allowlist"], [])
        self.assertEqual(contract["tool_admission"]["allowed_tool_names"], [])
        self.assertIsNone(contract["tool_admission"]["tool_inventory_digest"])
        self.assertFalse(contract["hosting"]["cost_estimate_observed"])
        self.assertFalse(contract["hosting"]["quota_observed"])

    def test_preflight_contains_observation_but_no_mutation_entry_point(self) -> None:
        script = (ROOT / "scripts" / "azure_mcp_cloud_shell_preflight.sh").read_text(encoding="utf-8")
        for command in ("az account show", "az provider show", "az group show", "az resource list", "azd init"):
            self.assertIn(command, script)
        for pattern in (
            r"^\s*azd\s+(?:up|provision|deploy|down)\b",
            r"^\s*az\s+provider\s+register\b",
            r"^\s*az\s+group\s+(?:create|delete)\b",
            r"^\s*az\s+role\s+assignment\s+(?:create|delete)\b",
            r"^\s*az\s+containerapp\s+(?:create|update|delete)\b",
        ):
            self.assertIsNone(re.search(pattern, script, flags=re.MULTILINE))

    def test_historical_azure_and_pr78_conflict_are_preserved(self) -> None:
        active = json.loads((ROOT / ".project" / "active-work.json").read_text(encoding="utf-8"))
        post_merge = json.loads(
            (ROOT / ".project" / "reconciliations" / "post-merge-pr75-pr77.json").read_text(encoding="utf-8")
        )
        independent = active["deployment_state"]["independent_demo_api"]
        self.assertEqual(independent["last_planner_run_id"], 30064289707)
        self.assertEqual(independent["requested_location"], "eastus")
        self.assertEqual(independent["requested_vm_size"], "Standard_B2ats_v2")
        self.assertFalse(independent["deployed"])
        self.assertEqual(post_merge["resolution"]["verification_status"], "conflicting")
        self.assertFalse(post_merge["azure_evidence_boundary"]["protected_westus2_f1alsv7_evidence"])

    def test_historical_pr74_record_is_not_rewritten(self) -> None:
        historical = json.loads(
            (ROOT / ".project" / "reconciliations" / "azure-mcp-pr74.json").read_text(encoding="utf-8")
        )
        self.assertFalse(historical["runtime_claims"]["client_path_selected"])
        self.assertFalse(historical["runtime_claims"]["remote_endpoint_deployed"])

    def test_validator_executes(self) -> None:
        spec = importlib.util.spec_from_file_location("azure_mcp_post_merge_sync", MODULE_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.main(), 0)


if __name__ == "__main__":
    unittest.main()
