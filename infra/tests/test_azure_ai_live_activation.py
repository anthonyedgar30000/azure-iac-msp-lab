from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
LIVE_WORKFLOW = ROOT / ".github/workflows/azure-ai-live-deploy.yml"
STATIC_WORKFLOW = ROOT / ".github/workflows/azure-ai-plan.yml"
ROOT_BICEP = ROOT / "infra/azure-ai-live.bicep"
MODULE_BICEP = ROOT / "infra/modules/azure_ai_openai.bicep"
PARAMETERS = ROOT / "infra/azure-ai-live.dev.bicepparam"
CONTRACT = ROOT / ".project/contracts/azure-ai-live-activation-v1.json"
HANDOFF = ROOT / ".project/handoffs/post-pr193-azure-ai-live-activation-plan.md"
RECONCILIATION = (
    ROOT
    / ".project/reconciliations/post-pr193-azure-ai-live-activation-plan-20260729.json"
)
TERMINAL = (
    ROOT
    / ".project/reconciliations/azure-ai-go-live-run1-terminal-20260729.json"
)
TERMINAL_HANDOFF = ROOT / ".project/handoffs/azure-ai-go-live-run1-terminal.md"


class AzureAiLiveActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.live_workflow = LIVE_WORKFLOW.read_text(encoding="utf-8")
        cls.static_workflow = STATIC_WORKFLOW.read_text(encoding="utf-8")
        cls.root_bicep = ROOT_BICEP.read_text(encoding="utf-8")
        cls.module_bicep = MODULE_BICEP.read_text(encoding="utf-8")
        cls.parameters = PARAMETERS.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.terminal = json.loads(TERMINAL.read_text(encoding="utf-8"))
        cls.terminal_handoff = TERMINAL_HANDOFF.read_text(encoding="utf-8")

    def test_separate_read_only_preflight_is_removed(self) -> None:
        self.assertFalse(
            (ROOT / ".github/workflows/azure-ai-read-only-preflight.yml").exists()
        )
        self.assertFalse((ROOT / "scripts/azure_ai_read_only_preflight.sh").exists())
        self.assertFalse(
            (ROOT / "docs/runbooks/azure-ai-read-only-preflight.md").exists()
        )

    def test_live_workflow_is_merge_triggered_and_exact_commit_bound(self) -> None:
        self.assertIn("push:", self.live_workflow)
        self.assertIn("branches:\n      - main", self.live_workflow)
        self.assertNotIn("workflow_dispatch:", self.live_workflow)
        self.assertIn("id-token: write", self.live_workflow)
        self.assertIn("environment: azure-lab", self.live_workflow)
        self.assertIn("ref: ${{ github.sha }}", self.live_workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.live_workflow)

    def test_live_workflow_deploys_and_verifies_without_a_separate_run(self) -> None:
        required = (
            "az provider register --namespace Microsoft.CognitiveServices --wait",
            "az deployment sub what-if",
            "az deployment sub create",
            "az role assignment create",
            "Cognitive Services OpenAI User",
            "az account get-access-token",
            '"max_output_tokens":32',
            "AZURE AI LIVE",
            "go-live-summary.json",
        )
        for marker in required:
            self.assertIn(marker, self.live_workflow)

        self.assertLess(
            self.live_workflow.index("az deployment sub what-if"),
            self.live_workflow.index("az deployment sub create"),
        )
        self.assertLess(
            self.live_workflow.index("az deployment sub create"),
            self.live_workflow.index("az role assignment create"),
        )

    def test_candidate_is_bounded_to_two_regions_and_one_model(self) -> None:
        self.assertIn("for location in canadaeast eastus2", self.live_workflow)
        self.assertIn("MODEL_NAME: gpt-4.1-mini", self.live_workflow)
        self.assertIn("MODEL_VERSION: '2025-04-14'", self.live_workflow)
        self.assertIn("DEPLOYMENT_SKU: Standard", self.live_workflow)
        self.assertIn("DEPLOYMENT_CAPACITY: '1'", self.live_workflow)
        self.assertIn("timeout-minutes: 60", self.live_workflow)

    def test_static_ci_cannot_authenticate_to_azure(self) -> None:
        self.assertIn("id-token: none", self.static_workflow)
        self.assertNotIn("uses: azure/login", self.static_workflow)
        self.assertIn(
            "python -m unittest infra.tests.test_azure_ai_live_activation -v",
            self.static_workflow,
        )

    def test_iac_is_entra_only_and_fail_closed_outside_live_workflow(self) -> None:
        self.assertIn("param deployAzureAi bool = false", self.root_bicep)
        self.assertIn("param assignInferenceRole bool = false", self.root_bicep)
        self.assertIn("param deployAzureAi = false", self.parameters)
        self.assertIn("param assignInferenceRole = false", self.parameters)
        self.assertIn("disableLocalAuth: true", self.module_bicep)
        self.assertIn("customSubDomainName: accountName", self.module_bicep)
        self.assertIn("publicNetworkAccess: 'Enabled'", self.module_bicep)
        self.assertIn("versionUpgradeOption: 'NoAutoUpgrade'", self.module_bicep)
        self.assertIn("raiPolicyName: 'Microsoft.Default'", self.module_bicep)

    def test_subscription_root_targets_the_new_resource_group_explicitly(self) -> None:
        self.assertIn(
            "resource azureAiResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01'",
            self.root_bicep,
        )
        self.assertIn("scope: resourceGroup(resourceGroupName)", self.root_bicep)
        self.assertIn("dependsOn:", self.root_bicep)
        self.assertIn("azureAiResourceGroup", self.root_bicep)
        self.assertNotIn("scope: resourceGroup!", self.root_bicep)

    def test_contract_records_consumed_run1_without_claiming_live_service(self) -> None:
        self.assertEqual(
            self.contract["status"],
            "go_live_run1_consumed_failed_before_resource_creation",
        )
        execution = self.contract["execution"]
        self.assertTrue(execution["azure_authentication_performed"])
        self.assertTrue(execution["azure_query_performed"])
        self.assertEqual(execution["provider_final_registration_state"], "Registered")
        self.assertFalse(execution["resource_mutation_performed"])
        self.assertFalse(execution["resource_group_created"])
        self.assertFalse(execution["openai_account_created"])
        self.assertFalse(execution["model_deployment_created"])
        self.assertFalse(execution["role_assignment_created"])
        self.assertFalse(execution["model_request_performed"])
        self.assertFalse(execution["service_verified_live"])

        authority = self.contract["authority"]
        self.assertEqual(
            authority["original_live_attempt_status"],
            "consumed_failed_terminal",
        )
        self.assertTrue(authority["repair_repository_changes_authorized"])
        self.assertTrue(authority["repair_exact_head_ci_authorized"])
        self.assertFalse(authority["repair_pull_request_merge_authorized"])
        self.assertFalse(authority["new_workflow_run_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_terminal_reconciliation_preserves_exact_failure_boundary(self) -> None:
        self.assertEqual(self.terminal["workflow_run"]["run_id"], 30419992872)
        self.assertEqual(self.terminal["workflow_run"]["conclusion"], "failure")
        self.assertEqual(
            self.terminal["terminal_failure"]["azure_error_code"],
            "InvalidScope",
        )
        sequence = self.terminal["attempt_sequence"]
        self.assertEqual(sequence["canadaeast_what_if"], "failed_invalid_scope")
        self.assertEqual(sequence["eastus2_what_if"], "failed_invalid_scope")
        self.assertEqual(sequence["subscription_deployment"], "not_started")
        deployed = self.terminal["deployed_reality"]
        self.assertFalse(deployed["resource_group_created_by_run"])
        self.assertFalse(deployed["azure_openai_account_created_by_run"])
        self.assertFalse(deployed["model_deployment_created_by_run"])
        self.assertFalse(deployed["model_request_performed"])
        self.assertFalse(deployed["endpoint_live"])
        self.assertEqual(
            self.terminal["authorization"]["status"],
            "consumed_failed_terminal",
        )
        self.assertFalse(
            self.terminal["authorization"]["manual_rerun_authorized"]
        )
        self.assertIn("failed_run != authorization_to_rerun", self.terminal_handoff)

    def test_historical_plan_reconciliation_remains_time_bounded(self) -> None:
        github = self.reconciliation["github_state"]
        self.assertEqual(
            github["observed_main"],
            "375255c6bca57f672a326915e5a18708de3eaaad",
        )
        self.assertEqual(github["latest_merged_pull_request"], 194)
        self.assertFalse(self.reconciliation["azure_state"]["fresh_query_performed"])
        self.assertFalse(self.reconciliation["activation_state"]["endpoint_live"])
        self.assertIn("deployment_succeeded != model_request_verified", self.handoff)


if __name__ == "__main__":
    unittest.main()
