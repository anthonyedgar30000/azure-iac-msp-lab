from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run5.yml"
STATIC_WORKFLOW = ROOT / ".github/workflows/azure-ai-plan.yml"
EXECUTOR = ROOT / "scripts/azure_ai_go_live_run5.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run5.json"
CONTRACT = ROOT / ".project/contracts/azure-ai-go-live-run5-selector-v1.json"
HANDOFF = ROOT / ".project/handoffs/azure-ai-go-live-run5-terminal.md"
TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run5-terminal-20260729.json"
)
RUN4_TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run4-terminal-20260729.json"
)
STATE_INDEX = ROOT / ".project/state-index.json"
BICEP = ROOT / "infra/azure-ai-live.bicep"
BICEP_MODULE = ROOT / "infra/modules/azure_ai_openai.bicep"


class AzureAiGoLiveRun5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.static_workflow = STATIC_WORKFLOW.read_text(encoding="utf-8")
        cls.executor = EXECUTOR.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.terminal = json.loads(TERMINAL.read_text(encoding="utf-8"))
        cls.run4_terminal = json.loads(RUN4_TERMINAL.read_text(encoding="utf-8"))
        cls.state_index = json.loads(STATE_INDEX.read_text(encoding="utf-8"))
        cls.bicep = BICEP.read_text(encoding="utf-8")
        cls.bicep_module = BICEP_MODULE.read_text(encoding="utf-8")

    def test_workflow_remains_historical_single_merge_trigger(self) -> None:
        self.assertIn("name: Azure AI go live run 5", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run5.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn("bash scripts/azure_ai_go_live_run5.sh", self.workflow)

    def test_request_is_consumed_and_not_rerunnable(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run5")
        self.assertEqual(self.request["status"], "consumed_terminal_failure")
        self.assertFalse(self.request["active"])
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 1)
        execution = self.request["terminal_execution"]
        self.assertEqual(execution["workflow_run"], 30425884534)
        self.assertEqual(execution["job_id"], 90492164065)
        self.assertFalse(execution["deployment_started"])
        self.assertFalse(execution["model_request_performed"])
        self.assertFalse(execution["endpoint_live"])
        authority = self.request["authority"]
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["second_deployment_attempt_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_terminal_evidence_preserves_capacity_and_template_failure(self) -> None:
        self.assertEqual(self.terminal["attempt_id"], "azure-ai-go-live-run5")
        self.assertEqual(self.terminal["status"], "consumed_terminal_failure")
        self.assertEqual(self.terminal["workflow"]["run_id"], 30425884534)
        self.assertEqual(self.terminal["artifact"]["artifact_id"], 8713618498)
        self.assertEqual(
            self.terminal["artifact"]["digest"],
            "sha256:39491be1c1292ffb9f31064645dd289ed718cebb4c862b4d5c57d712acb7162a",
        )
        gpt4o = self.terminal["candidate_observations"]["gpt_4o_mini"]
        self.assertTrue(gpt4o["model_listed_in_all_regions"])
        self.assertEqual(gpt4o["reported_available_capacity_each_region"], 0)
        gpt41 = self.terminal["candidate_observations"]["gpt_4_1_mini"]
        self.assertTrue(gpt41["model_listed_in_all_regions"])
        self.assertEqual(gpt41["reported_available_capacity_each_region"], 200)
        self.assertTrue(gpt41["capacity_sufficient_for_requested_capacity"])
        self.assertFalse(gpt41["what_if_change_plan_produced"])
        self.assertEqual(
            self.terminal["root_cause"]["classification"],
            "bicep_location_allowlist_excluded_all_capacity_sufficient_candidates",
        )
        self.assertFalse(
            self.terminal["root_cause"]["subscription_policy_block_established_for_run5_candidates"]
        )

    def test_no_azure_ai_resources_or_billable_request_were_established(self) -> None:
        deployment = self.terminal["deployment_state"]
        self.assertFalse(deployment["deployment_started"])
        self.assertFalse(deployment["resource_group_created"])
        self.assertFalse(deployment["azure_openai_account_created"])
        self.assertFalse(deployment["model_deployment_created"])
        self.assertFalse(deployment["inference_role_assignment_created"])
        self.assertFalse(deployment["model_request_performed"])
        self.assertFalse(deployment["endpoint_live"])
        self.assertFalse(deployment["cleanup_required"])
        self.assertEqual(self.terminal["cost"]["Azure_resource_cost_delta_established"], 0)
        self.assertFalse(self.terminal["cost"]["billable_model_request_performed"])

    def test_region_allowlist_repair_covers_observed_candidates(self) -> None:
        for location in (
            "westus3",
            "westus",
            "eastus",
            "northcentralus",
            "southcentralus",
        ):
            self.assertIn(f"  '{location}'", self.bicep)
        self.assertIn("  'canadaeast'", self.bicep)
        self.assertIn("  'eastus2'", self.bicep)
        self.assertIn("deployAzureAi bool = false", self.bicep)
        self.assertIn("'GlobalStandard'", self.bicep_module)
        self.assertIn("disableLocalAuth: true", self.bicep_module)
        self.assertIn("scope: account", self.bicep_module)
        self.assertIn("repair prepared != repair merged", self.handoff)
        self.assertFalse(self.terminal["repair_state"]["repair_merged"])
        self.assertFalse(self.terminal["repair_state"]["new_deployment_authorized"])

    def test_original_selector_remains_bounded_historical_evidence(self) -> None:
        candidates = self.request["scope"]["candidate_order"]
        self.assertEqual(len(candidates), 10)
        self.assertEqual(self.executor.count("az deployment sub create"), 1)
        self.assertEqual(self.executor.count("curl --silent --show-error"), 1)
        self.assertNotIn("for propagation_attempt", self.executor)
        self.assertEqual(self.contract["mutation"]["deployment_attempt_limit"], 1)
        self.assertEqual(self.contract["verification"]["model_request_count"], 1)

    def test_state_index_consumes_run5_and_disables_active_authority(self) -> None:
        self.assertIsNone(self.state_index["active_azure_ai_activation_authorization"])
        self.assertEqual(
            self.state_index["latest_consumed_azure_ai_activation_authorization"],
            ".project/reconciliations/azure-ai-go-live-run5-terminal-20260729.json",
        )
        self.assertEqual(
            self.state_index["latest_azure_ai_activation_reconciliation"],
            ".project/reconciliations/azure-ai-go-live-run5-terminal-20260729.json",
        )
        self.assertEqual(
            self.state_index["azure_ai_run5_location_allowlist_repair"],
            "infra/azure-ai-live.bicep",
        )
        self.assertEqual(
            self.state_index["previous_azure_ai_activation_reconciliation"],
            ".project/reconciliations/azure-ai-go-live-run4-terminal-20260729.json",
        )
        self.assertEqual(self.run4_terminal["workflow"]["run_id"], 30423217542)

    def test_static_validation_includes_repair_without_cloud_identity(self) -> None:
        self.assertIn("infra.tests.test_azure_ai_go_live_run5", self.static_workflow)
        self.assertIn("bash -n scripts/azure_ai_go_live_run5.sh", self.static_workflow)
        self.assertIn("infra/azure-ai-live.bicep", self.static_workflow)
        self.assertIn("id-token: none", self.static_workflow)


if __name__ == "__main__":
    unittest.main()
