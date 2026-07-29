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
        self.assertIn("python -m unittest infra.tests.test_azure_ai_live_activation -v", self.static_workflow)

    def test_iac_is_entra_only_and_still_fail_closed_outside_live_workflow(self) -> None:
        self.assertIn("param deployAzureAi bool = false", self.root_bicep)
        self.assertIn("param assignInferenceRole bool = false", self.root_bicep)
        self.assertIn("param deployAzureAi = false", self.parameters)
        self.assertIn("param assignInferenceRole = false", self.parameters)
        self.assertIn("disableLocalAuth: true", self.module_bicep)
        self.assertIn("customSubDomainName: accountName", self.module_bicep)
        self.assertIn("publicNetworkAccess: 'Enabled'", self.module_bicep)
        self.assertIn("versionUpgradeOption: 'NoAutoUpgrade'", self.module_bicep)
        self.assertIn("raiPolicyName: 'Microsoft.Default'", self.module_bicep)

    def test_contract_records_direct_activation_authority_without_claiming_success(self) -> None:
        self.assertEqual(
            self.contract["status"],
            "direct_go_live_candidate_merge_trigger_not_executed",
        )
        execution = self.contract["execution"]
        self.assertFalse(execution["azure_authentication_performed"])
        self.assertFalse(execution["azure_mutation_performed"])
        self.assertFalse(execution["model_request_performed"])
        authority = self.contract["authority"]
        self.assertTrue(authority["pull_request_merge_authorized"])
        self.assertTrue(authority["merge_triggered_workflow_authorized"])
        self.assertTrue(authority["azure_authentication_authorized"])
        self.assertTrue(authority["azure_query_authorized"])
        self.assertTrue(authority["azure_mutation_authorized"])
        self.assertTrue(authority["rbac_mutation_authorized"])
        self.assertTrue(authority["model_deployment_authorized"])
        self.assertTrue(authority["one_bounded_model_request_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_reconciliation_preserves_post_pr194_boundary(self) -> None:
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
