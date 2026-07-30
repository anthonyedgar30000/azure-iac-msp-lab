from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run7.yml"
STATIC_WORKFLOW = ROOT / ".github/workflows/azure-ai-plan.yml"
EXECUTOR = ROOT / "scripts/azure_ai_go_live_run7.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run7.json"
CONTRACT = ROOT / ".project/contracts/azure-ai-existing-role-activation-v1.json"
CANDIDATE_HANDOFF = ROOT / ".project/handoffs/azure-ai-go-live-run7.md"
TERMINAL_HANDOFF = ROOT / ".project/handoffs/azure-ai-go-live-run7-terminal.md"
TERMINAL = ROOT / ".project/reconciliations/azure-ai-go-live-run7-terminal-20260730.json"
REPAIR_PATCH = ROOT / ".project/repairs/azure-ai-go-live-run7-role-query.patch"
TEMPLATE = ROOT / "infra/azure-ai-existing-account-model-only.bicep"
RUN6_TERMINAL = ROOT / ".project/reconciliations/azure-ai-go-live-run6-terminal-and-runtime-wire-20260729.json"
SELECTOR = ROOT / ".project/selectors/post-pr251-current.json"


class AzureAiGoLiveRun7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.static_workflow = STATIC_WORKFLOW.read_text(encoding="utf-8")
        cls.executor = EXECUTOR.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.candidate_handoff = CANDIDATE_HANDOFF.read_text(encoding="utf-8")
        cls.terminal_handoff = TERMINAL_HANDOFF.read_text(encoding="utf-8")
        cls.terminal = json.loads(TERMINAL.read_text(encoding="utf-8"))
        cls.repair_patch = REPAIR_PATCH.read_text(encoding="utf-8")
        cls.template = TEMPLATE.read_text(encoding="utf-8")
        cls.run6 = json.loads(RUN6_TERMINAL.read_text(encoding="utf-8"))
        cls.selector = json.loads(SELECTOR.read_text(encoding="utf-8"))

    def test_request_is_consumed_single_attempt(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run7")
        self.assertEqual(self.request["status"], "consumed_terminal_failure")
        self.assertFalse(self.request["active"])
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 1)
        execution = self.request["terminal_execution"]
        self.assertEqual(execution["workflow_run"], 30507904540)
        self.assertEqual(execution["job_id"], 90761544877)
        self.assertEqual(execution["artifact_id"], 8746021488)
        self.assertEqual(
            execution["artifact_digest"],
            "sha256:89a101055b5df556b5e4bab47a2487ab13690e5824c9ec26cf219fbb345449df",
        )
        self.assertFalse(execution["deployment_started"])
        self.assertFalse(execution["model_request_performed"])
        self.assertFalse(execution["azure_mutations_performed"])

    def test_terminal_evidence_preserves_exact_cli_failure(self) -> None:
        self.assertEqual(self.terminal["status"], "consumed_terminal_failure")
        self.assertEqual(self.terminal["workflow"]["run_id"], 30507904540)
        result = self.terminal["terminal_result"]
        self.assertEqual(result["failure_stage"], "existing_direct_role_validation")
        self.assertEqual(result["failure_status"], "role_assignment_query_failed")
        self.assertEqual(
            result["failure_classification"],
            "azure_cli_mutually_exclusive_scope_and_all_arguments",
        )
        self.assertEqual(
            result["exact_error"],
            "ERROR: group or scope are not required when --all is used",
        )
        self.assertTrue(result["role_query_started"])
        self.assertFalse(result["role_query_completed"])
        self.assertFalse(result["required_role_exists_established"])
        self.assertFalse(result["required_role_missing_established"])

    def test_account_observed_but_no_later_stage_or_mutation(self) -> None:
        target = self.terminal["observed_target"]
        self.assertEqual(target["resource_group"]["name"], "rg-ai-msp-dev-eastus")
        account = target["account"]
        self.assertEqual(account["name"], "oai-msp-anthony-dev-eastus")
        self.assertEqual(account["kind"], "OpenAI")
        self.assertEqual(account["sku"], "S0")
        self.assertEqual(account["public_network_access"], "Enabled")
        self.assertIsNone(account["disable_local_auth"])
        result = self.terminal["terminal_result"]
        for key in (
            "deployment_inventory_queried",
            "model_listing_queried",
            "capacity_queried",
            "what_if_started",
            "deployment_started",
            "account_hardening_started",
            "model_request_performed",
            "endpoint_live",
            "azure_mutations_performed",
            "separate_verified_gpt5_runtime_modified",
        ):
            self.assertFalse(result[key], key)
        self.assertEqual(self.terminal["cost"]["azure_resource_cost_delta_established"], 0)
        self.assertEqual(self.terminal["cost"]["tokens_consumed"], 0)

    def test_run6_and_run7_are_separately_consumed(self) -> None:
        self.assertEqual(self.run6["run6_terminal"]["attempt_id"], "azure-ai-go-live-run6")
        self.assertTrue(self.run6["run6_terminal"]["authorization_consumed"])
        self.assertTrue(self.terminal["authorization"]["consumed"])
        self.assertFalse(self.terminal["authorization"]["manual_rerun_authorized"])
        self.assertFalse(self.terminal["authorization"]["new_attempt_authorized"])
        self.assertIn("Run 7 is consumed", self.terminal_handoff)

    def test_workflow_remains_historical_single_merge_trigger(self) -> None:
        self.assertIn("name: Azure AI go live run 7", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run7.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)

    def test_template_cannot_create_account_group_or_role(self) -> None:
        self.assertIn("targetScope = 'resourceGroup'", self.template)
        self.assertIn("Microsoft.CognitiveServices/accounts@2024-10-01' existing", self.template)
        self.assertIn("Microsoft.CognitiveServices/accounts/deployments@2024-10-01", self.template)
        self.assertNotIn("Microsoft.Resources/resourceGroups", self.template)
        self.assertNotIn("Microsoft.Authorization/roleAssignments", self.template)

    def test_historical_executor_and_repair_are_traceable(self) -> None:
        self.assertIn('ROLE_NAME="Cognitive Services OpenAI User"', self.executor)
        self.assertEqual(self.executor.count("az deployment group create"), 1)
        self.assertEqual(self.executor.count("az resource update"), 1)
        self.assertEqual(self.executor.count("curl --silent --show-error"), 1)
        self.assertNotIn("az role assignment create", self.executor)
        self.assertIn("--scope \"$account_id\"", self.executor)
        self.assertEqual(self.repair_patch.count("-  --all"), 3)
        self.assertIn(
            "retain --all only for the unscoped principal-discovery fallback",
            self.terminal["repair_state"]["repair_description"],
        )
        self.assertFalse(self.terminal["repair_state"]["repair_authorizes_new_attempt"])
        self.assertFalse(self.terminal["repair_state"]["run8_authorized"])

    def test_model_and_separate_runtime_boundaries_are_preserved(self) -> None:
        scope = self.request["scope"]
        self.assertEqual(scope["model_name"], "gpt-4.1-mini")
        self.assertEqual(scope["deployment_name"], "gpt-41-mini-msp-dev")
        separate = scope["separate_verified_runtime_untouched"]
        self.assertEqual(separate["deployment"], "gpt-5-mini")
        self.assertFalse(separate["modified_by_run7"])
        self.assertIn("separate verified gpt-5-mini runtime modified: false", self.terminal_handoff)

    def test_selector_preserves_run7_lineage_after_later_terminal_syncs(self) -> None:
        run8_trigger_sync = ".project/reconciliations/azure-ai-go-live-run8-trigger-sync-20260730.json"
        self.assertEqual(self.selector["authoritative_current_reality"], ".project/current-reality-v4.json")
        self.assertEqual(self.selector["authoritative_state_index"], ".project/state-index-v13.json")
        self.assertEqual(self.selector["prior_azure_ai_trigger_sync"], run8_trigger_sync)
        self.assertEqual(
            self.selector["latest_azure_ai_terminal_reconciliation"],
            ".project/reconciliations/azure-ai-go-live-run8-terminal-20260730.json",
        )
        self.assertEqual(
            self.selector["latest_operational_overlay"],
            ".project/reconciliations/servicetracer-demo-api-plan-run1-terminal-20260730.json",
        )
        self.assertIsNone(self.selector["pending_azure_ai_terminal_reconciliation"])
        self.assertIsNone(self.selector["active_azure_ai_activation_authorization"])
        self.assertIsNone(self.selector["active_servicetracer_planning_authorization"])

    def test_static_validation_and_contract_remain_bounded(self) -> None:
        self.assertIn("infra.tests.test_azure_ai_go_live_run7", self.static_workflow)
        self.assertIn("bash -n scripts/azure_ai_go_live_run7.sh", self.static_workflow)
        self.assertIn("id-token: none", self.static_workflow)
        architecture = self.contract["architecture"]
        self.assertFalse(architecture["resource_group_creation_available"])
        self.assertFalse(architecture["account_creation_available"])
        self.assertFalse(architecture["role_assignment_creation_available"])
        self.assertIn("fresh one-attempt authority", self.candidate_handoff)


if __name__ == "__main__":
    unittest.main()
