from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run6.yml"
STATIC_WORKFLOW = ROOT / ".github/workflows/azure-ai-plan.yml"
EXECUTOR = ROOT / "scripts/azure_ai_go_live_run6.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run6.json"
CONTRACT = ROOT / ".project/contracts/azure-ai-manual-account-adoption-v1.json"
HANDOFF = ROOT / ".project/handoffs/azure-ai-go-live-run6.md"
ADOPTION_BICEP = ROOT / "infra/azure-ai-existing-account-adopt.bicep"
LIVE_BICEP = ROOT / "infra/azure-ai-live.bicep"
RUN5_TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run5-terminal-20260729.json"
)
RUN6_TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run6-terminal-and-runtime-wire-20260729.json"
)
STATE_INDEX = ROOT / ".project/state-index.json"


class AzureAiGoLiveRun6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.static_workflow = STATIC_WORKFLOW.read_text(encoding="utf-8")
        cls.executor = EXECUTOR.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.adoption_bicep = ADOPTION_BICEP.read_text(encoding="utf-8")
        cls.live_bicep = LIVE_BICEP.read_text(encoding="utf-8")
        cls.run5_terminal = json.loads(RUN5_TERMINAL.read_text(encoding="utf-8"))
        cls.run6_terminal = json.loads(RUN6_TERMINAL.read_text(encoding="utf-8"))
        cls.state_index = json.loads(STATE_INDEX.read_text(encoding="utf-8"))

    def test_workflow_remains_historical_single_merge_trigger(self) -> None:
        self.assertIn("name: Azure AI go live run 6", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run6.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.workflow)
        self.assertIn("bash scripts/azure_ai_go_live_run6.sh", self.workflow)

    def test_request_is_consumed_and_not_rerunnable(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run6")
        self.assertEqual(self.request["status"], "consumed_terminal_failure")
        self.assertFalse(self.request["active"])
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 1)
        terminal = self.request["terminal_execution"]
        self.assertEqual(terminal["workflow_run"], 30429010899)
        self.assertEqual(terminal["job_id"], 90501685520)
        self.assertEqual(terminal["failure_stage"], "pre_mutation_what_if")
        self.assertFalse(terminal["deployment_started"])
        self.assertFalse(terminal["model_request_performed"])
        self.assertFalse(terminal["endpoint_live"])
        authority = self.request["authority"]
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["second_deployment_attempt_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_historical_target_and_existing_only_boundary_are_preserved(self) -> None:
        scope = self.request["scope"]
        self.assertEqual(scope["subscription_name"], "Azure for Students")
        self.assertEqual(scope["resource_group_name"], "rg-ai-msp-dev-eastus")
        self.assertEqual(scope["account_name"], "oai-msp-anthony-dev-eastus")
        self.assertEqual(scope["location"], "eastus")
        self.assertEqual(scope["model_name"], "gpt-4.1-mini")
        self.assertEqual(scope["model_version"], "2025-04-14")
        self.assertEqual(scope["deployment_name"], "gpt-41-mini-msp-dev")
        self.assertIn("targetScope = 'resourceGroup'", self.adoption_bicep)
        self.assertIn("existing = {", self.adoption_bicep)
        self.assertIn(
            "resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' existing",
            self.adoption_bicep,
        )
        self.assertNotIn("Microsoft.Resources/resourceGroups", self.adoption_bicep)
        self.assertEqual(self.executor.count("az deployment group create"), 1)
        self.assertNotIn("az deployment sub create", self.executor)

    def test_live_checks_preceded_the_unreached_mutation(self) -> None:
        self.assertIn("existing-deployment-query.err", self.executor)
        self.assertIn("conflicting_existing_deployment", self.executor)
        self.assertIn("/models?api-version=2024-10-01", self.executor)
        self.assertIn("/modelCapacities?api-version=2024-10-01", self.executor)
        self.assertIn("az deployment group what-if", self.executor)
        self.assertLess(
            self.executor.index("az deployment group what-if"),
            self.executor.index("az deployment group create"),
        )
        self.assertEqual(
            self.run6_terminal["run6_terminal"]["failure_stage"],
            "pre_mutation_what_if",
        )
        self.assertFalse(
            self.run6_terminal["run6_terminal"]["deployment_started"]
        )

    def test_separate_verified_runtime_does_not_rewrite_run6(self) -> None:
        reconciliation = self.run6_terminal["reconciliation"]
        runtime = self.run6_terminal["verified_runtime"]
        self.assertFalse(reconciliation["run6_target_matches_verified_runtime"])
        self.assertFalse(
            reconciliation["verified_runtime_retroactively_makes_run6_successful"]
        )
        self.assertEqual(runtime["deployment"], "gpt-5-mini")
        self.assertEqual(runtime["request_status"], "completed")
        self.assertEqual(runtime["output_text"], "AZURE ENTRA CONNECTED")
        self.assertFalse(runtime["api_key_used"])
        self.assertFalse(runtime["azure_mcp_connected"])

    def test_run5_and_run6_are_consumed_with_no_active_authority(self) -> None:
        self.assertEqual(self.run5_terminal["attempt_id"], "azure-ai-go-live-run5")
        self.assertEqual(self.run5_terminal["status"], "consumed_terminal_failure")
        self.assertIsNone(self.state_index["active_azure_ai_activation_authorization"])
        self.assertEqual(
            self.state_index["latest_consumed_azure_ai_activation_authorization"],
            ".project/reconciliations/azure-ai-go-live-run6-terminal-and-runtime-wire-20260729.json",
        )
        self.assertEqual(
            self.state_index["latest_azure_ai_activation_request"],
            ".project/deployment-requests/azure-ai-go-live-run6.json",
        )
        self.assertEqual(
            self.state_index["azure_ai_run6_workflow"],
            ".github/workflows/azure-ai-go-live-run6.yml",
        )

    def test_static_validation_preserves_historical_files_without_cloud_identity(self) -> None:
        self.assertIn("infra.tests.test_azure_ai_go_live_run6", self.static_workflow)
        self.assertIn("bash -n scripts/azure_ai_go_live_run6.sh", self.static_workflow)
        self.assertIn("infra/azure-ai-existing-account-adopt.bicep", self.static_workflow)
        self.assertIn("id-token: none", self.static_workflow)
        self.assertIn("  'eastus'", self.live_bicep)


if __name__ == "__main__":
    unittest.main()
