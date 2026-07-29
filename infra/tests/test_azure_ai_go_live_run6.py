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
        cls.state_index = json.loads(STATE_INDEX.read_text(encoding="utf-8"))

    def test_workflow_is_one_merge_trigger_and_exact_commit_bound(self) -> None:
        self.assertIn("name: Azure AI go live run 6", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run6.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.workflow)
        self.assertIn("bash scripts/azure_ai_go_live_run6.sh", self.workflow)

    def test_request_targets_exact_manual_resource_and_one_model(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run6")
        self.assertEqual(self.request["status"], "active_one_attempt")
        self.assertTrue(self.request["active"])
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 0)
        scope = self.request["scope"]
        self.assertEqual(scope["subscription_name"], "Azure for Students")
        self.assertEqual(scope["resource_group_name"], "rg-ai-msp-dev-eastus")
        self.assertEqual(scope["account_name"], "oai-msp-anthony-dev-eastus")
        self.assertEqual(scope["location"], "eastus")
        self.assertTrue(scope["account_preexisting_required"])
        self.assertTrue(scope["resource_group_preexisting_required"])
        self.assertFalse(scope["duplicate_account_authorized"])
        self.assertFalse(scope["duplicate_resource_group_authorized"])
        self.assertEqual(scope["model_name"], "gpt-4.1-mini")
        self.assertEqual(scope["model_version"], "2025-04-14")
        self.assertEqual(scope["deployment_name"], "gpt-41-mini-msp-dev")
        self.assertEqual(scope["deployment_sku"], "GlobalStandard")
        self.assertEqual(scope["deployment_capacity"], 1)
        self.assertEqual(scope["model_request_count"], 1)
        self.assertEqual(scope["max_output_tokens"], 32)

    def test_existing_resource_adoption_is_fail_closed_against_duplicates(self) -> None:
        self.assertIn("targetScope = 'resourceGroup'", self.adoption_bicep)
        self.assertIn("existing = {", self.adoption_bicep)
        self.assertIn("resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' existing", self.adoption_bicep)
        self.assertNotIn("Microsoft.Resources/resourceGroups", self.adoption_bicep)
        self.assertIn('az group show --name "$RESOURCE_GROUP"', self.executor)
        self.assertIn("pre_mutation_existing_resource_validation", self.executor)
        self.assertIn("new_account_creation_authorized == false", self.executor)
        self.assertIn("new_resource_group_creation_authorized == false", self.executor)
        self.assertEqual(self.executor.count("az deployment group create"), 1)
        self.assertNotIn("az deployment sub create", self.executor)
        self.assertIn("No duplicate resource group or Azure OpenAI account is authorized", self.handoff)

    def test_live_model_capacity_what_if_and_conflict_checks_precede_mutation(self) -> None:
        self.assertIn("existing-deployment-query.err", self.executor)
        self.assertIn("conflicting_existing_deployment", self.executor)
        self.assertIn("/models?api-version=2024-10-01", self.executor)
        self.assertIn("/modelCapacities?api-version=2024-10-01", self.executor)
        self.assertIn("az deployment group what-if", self.executor)
        self.assertLess(
            self.executor.index("az deployment group what-if"),
            self.executor.index("az deployment group create"),
        )
        self.assertIn("available_capacity < DEPLOYMENT_CAPACITY", self.executor)
        self.assertEqual(self.contract["adoption_method"]["deployment_attempt_limit"], 1)

    def test_security_boundary_is_entra_only_account_scoped_and_one_call(self) -> None:
        authority = self.request["authority"]
        self.assertFalse(authority["api_key_use_authorized"])
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["second_deployment_attempt_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])
        self.assertIn("scope: account", self.adoption_bicep)
        self.assertIn("Cognitive Services OpenAI User", self.handoff)
        self.assertIn("properties.disableLocalAuth=true", self.executor)
        self.assertIn("https://ai.azure.com/.default", self.executor)
        self.assertEqual(self.executor.count("curl --silent --show-error"), 1)
        self.assertNotIn("for propagation_attempt", self.executor)
        self.assertIn("sleep 90", self.executor)
        self.assertIn("max_output_tokens\":32", self.executor)

    def test_run5_is_consumed_and_run6_is_the_only_active_azure_ai_authority(self) -> None:
        self.assertEqual(self.run5_terminal["attempt_id"], "azure-ai-go-live-run5")
        self.assertEqual(self.run5_terminal["status"], "consumed_terminal_failure")
        self.assertFalse(self.run5_terminal["deployment_state"]["deployment_started"])
        self.assertEqual(
            self.state_index["latest_consumed_azure_ai_activation_authorization"],
            ".project/reconciliations/azure-ai-go-live-run5-terminal-20260729.json",
        )
        self.assertEqual(
            self.state_index["active_azure_ai_activation_authorization"],
            ".project/deployment-requests/azure-ai-go-live-run6.json",
        )
        self.assertEqual(
            self.state_index["latest_azure_ai_activation_request"],
            ".project/deployment-requests/azure-ai-go-live-run6.json",
        )
        self.assertEqual(
            self.state_index["azure_ai_run6_workflow"],
            ".github/workflows/azure-ai-go-live-run6.yml",
        )

    def test_static_validation_includes_run6_without_cloud_identity(self) -> None:
        self.assertIn("infra.tests.test_azure_ai_go_live_run6", self.static_workflow)
        self.assertIn("bash -n scripts/azure_ai_go_live_run6.sh", self.static_workflow)
        self.assertIn("infra/azure-ai-existing-account-adopt.bicep", self.static_workflow)
        self.assertIn("id-token: none", self.static_workflow)
        self.assertIn("  'eastus'", self.live_bicep)


if __name__ == "__main__":
    unittest.main()
