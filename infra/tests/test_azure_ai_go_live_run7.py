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
HANDOFF = ROOT / ".project/handoffs/azure-ai-go-live-run7.md"
TEMPLATE = ROOT / "infra/azure-ai-existing-account-model-only.bicep"
RUN6_TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run6-terminal-and-runtime-wire-20260729.json"
)
SELECTOR = ROOT / ".project/CURRENT.json"


class AzureAiGoLiveRun7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.static_workflow = STATIC_WORKFLOW.read_text(encoding="utf-8")
        cls.executor = EXECUTOR.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.template = TEMPLATE.read_text(encoding="utf-8")
        cls.run6 = json.loads(RUN6_TERMINAL.read_text(encoding="utf-8"))
        cls.selector = json.loads(SELECTOR.read_text(encoding="utf-8"))

    def test_request_is_one_fresh_attempt_with_existing_role(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run7")
        self.assertEqual(
            self.request["source_instruction"],
            "Proceed with Azure AI run 7 using the existing account and existing account-scoped inference role.",
        )
        self.assertEqual(self.request["status"], "active_one_attempt")
        self.assertTrue(self.request["active"])
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 0)
        scope = self.request["scope"]
        self.assertEqual(scope["subscription_name"], "Azure for Students")
        self.assertEqual(scope["resource_group_name"], "rg-ai-msp-dev-eastus")
        self.assertEqual(scope["account_name"], "oai-msp-anthony-dev-eastus")
        self.assertTrue(scope["direct_account_scoped_role_preexisting_required"])
        self.assertFalse(scope["role_assignment_creation_authorized"])
        self.assertEqual(scope["inference_role_name"], "Cognitive Services OpenAI User")
        self.assertEqual(scope["inference_role_definition_id"], "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd")
        self.assertEqual(scope["model_request_count"], 1)
        self.assertEqual(scope["max_output_tokens"], 32)

    def test_run6_is_consumed_and_not_reused(self) -> None:
        self.assertEqual(self.run6["run6_terminal"]["attempt_id"], "azure-ai-go-live-run6")
        self.assertTrue(self.run6["run6_terminal"]["authorization_consumed"])
        self.assertFalse(self.run6["run6_terminal"]["manual_rerun_authorized"])
        self.assertFalse(self.run6["run6_terminal"]["deployment_started"])
        self.assertEqual(
            self.run6["run6_terminal"]["failure_classification"],
            "workflow_principal_lacked_role_assignments_write",
        )
        self.assertIn("fresh one-attempt authority", self.handoff)
        self.assertIn("It is not a rerun of run 6", self.handoff)

    def test_workflow_is_single_merge_trigger_and_exact_commit(self) -> None:
        self.assertIn("name: Azure AI go live run 7", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run7.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.workflow)
        self.assertIn("bash scripts/azure_ai_go_live_run7.sh", self.workflow)

    def test_template_cannot_create_account_group_or_role(self) -> None:
        self.assertIn("targetScope = 'resourceGroup'", self.template)
        self.assertIn("Microsoft.CognitiveServices/accounts@2024-10-01' existing", self.template)
        self.assertIn("Microsoft.CognitiveServices/accounts/deployments@2024-10-01", self.template)
        self.assertNotIn("Microsoft.Resources/resourceGroups", self.template)
        self.assertNotIn("Microsoft.Authorization/roleAssignments", self.template)
        self.assertNotIn("kind: 'OpenAI'", self.template)

    def test_executor_verifies_role_then_has_one_mutation_path(self) -> None:
        self.assertIn('ROLE_NAME="Cognitive Services OpenAI User"', self.executor)
        self.assertIn('ROLE_DEFINITION_GUID="5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"', self.executor)
        self.assertIn("required_direct_role_missing", self.executor)
        self.assertIn("required_direct_role_disappeared", self.executor)
        self.assertEqual(self.executor.count("az deployment group create"), 1)
        self.assertEqual(self.executor.count("az resource update"), 1)
        self.assertEqual(self.executor.count("curl --silent --show-error"), 1)
        self.assertNotIn("az role assignment create", self.executor)
        self.assertNotIn("for propagation", self.executor)
        self.assertNotIn("while true", self.executor)
        self.assertIn("https://cognitiveservices.azure.com/.default", self.executor)
        self.assertIn("AZURE AI RUN 7 LIVE", self.executor)

    def test_model_and_separate_runtime_boundaries_are_exact(self) -> None:
        scope = self.request["scope"]
        self.assertEqual(scope["model_name"], "gpt-4.1-mini")
        self.assertEqual(scope["model_version"], "2025-04-14")
        self.assertEqual(scope["deployment_name"], "gpt-41-mini-msp-dev")
        self.assertEqual(scope["deployment_sku"], "GlobalStandard")
        self.assertEqual(scope["deployment_capacity"], 1)
        separate = scope["separate_verified_runtime_untouched"]
        self.assertEqual(separate["deployment"], "gpt-5-mini")
        self.assertIn("separate_verified_gpt5_runtime_modified:false", self.executor)
        self.assertIn("Run 7 does not modify, replace, or claim ownership", self.handoff)

    def test_failure_cost_and_cleanup_are_bounded(self) -> None:
        authority = self.request["authority"]
        self.assertFalse(authority["role_assignment_creation_authorized"])
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["second_deployment_attempt_authorized"])
        self.assertFalse(authority["regional_fallback_authorized"])
        self.assertFalse(authority["model_fallback_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])
        self.assertFalse(self.request["cost_and_quota"]["actual_cost_freshly_observed"])
        self.assertIn("No automatic retry, rollback", self.handoff)

    def test_static_validation_covers_run7_without_azure_identity(self) -> None:
        self.assertIn("infra.tests.test_azure_ai_go_live_run7", self.static_workflow)
        self.assertIn("bash -n scripts/azure_ai_go_live_run7.sh", self.static_workflow)
        self.assertIn("infra/azure-ai-existing-account-model-only.bicep", self.static_workflow)
        self.assertIn("id-token: none", self.static_workflow)

    def test_run7_selector_boundary_remains_historical_after_later_authority(self) -> None:
        compatibility = {
            item["path"]: item["status"]
            for item in self.selector["compatibility_records"]
        }
        self.assertIn(".project/current-reality-v3.json", compatibility)
        self.assertIn(".project/state-index-v12.json", compatibility)
        self.assertTrue("historical" in compatibility[".project/current-reality-v3.json"])
        self.assertTrue("historical" in compatibility[".project/state-index-v12.json"])
        self.assertIn("terminal reconciliation must supersede", self.handoff)

    def test_contract_matches_existing_only_architecture(self) -> None:
        architecture = self.contract["architecture"]
        self.assertFalse(architecture["resource_group_creation_available"])
        self.assertFalse(architecture["account_creation_available"])
        self.assertFalse(architecture["role_assignment_creation_available"])
        self.assertEqual(self.contract["identity_and_permissions"]["required_role_scope"], "exact Azure OpenAI account")
        self.assertEqual(self.contract["security"]["model_request_limit"], 1)


if __name__ == "__main__":
    unittest.main()
