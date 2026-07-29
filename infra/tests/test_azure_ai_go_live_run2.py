from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run2.yml"
SCRIPT = ROOT / "scripts/azure_ai_go_live_run2.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run2.json"
RECONCILIATION = (
    ROOT
    / ".project/reconciliations/azure-ai-go-live-run2-terminal-20260729.json"
)
BICEP = ROOT / "infra/azure-ai-live.bicep"


class AzureAiGoLiveRun2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(
            RECONCILIATION.read_text(encoding="utf-8")
        )
        cls.bicep = BICEP.read_text(encoding="utf-8")

    def test_workflow_remains_non_manual_and_exact_commit_bound(self) -> None:
        self.assertIn("name: Azure AI go live run 2", self.workflow)
        self.assertIn("push:", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run2.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.workflow)

    def test_executor_is_bounded_and_json_path_repair_is_present(self) -> None:
        required = (
            'ATTEMPT_ID="azure-ai-go-live-run2"',
            'MODEL_NAME="gpt-4.1-mini"',
            'MODEL_VERSION="2025-04-14"',
            'DEPLOYMENT_SKU="Standard"',
            'DEPLOYMENT_CAPACITY="1"',
            ".authority.automatic_retry_authorized == false",
            ".authority.manual_rerun_authorized == false",
            "for location in canadaeast eastus2",
            "az deployment sub what-if",
            "az deployment sub create",
            "Cognitive Services OpenAI User",
            "max_output_tokens\":32",
            "AZURE AI LIVE",
            'status:"live_verified"',
            'endpoint_live:true',
        )
        for marker in required:
            self.assertIn(marker, self.script)

        self.assertLess(
            self.script.index("az deployment sub what-if"),
            self.script.index("az deployment sub create"),
        )
        self.assertLess(
            self.script.index("az deployment sub create"),
            self.script.index("az role assignment create"),
        )

    def test_run2_authorization_is_consumed_and_not_rerunnable(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run2")
        self.assertEqual(
            self.request["status"],
            "consumed_failed_terminal_before_first_azure_query",
        )
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 1)
        execution = self.request["execution"]
        self.assertTrue(execution["repository_validation_succeeded"])
        self.assertTrue(execution["azure_oidc_login_succeeded"])
        self.assertFalse(execution["authorization_guard_succeeded"])
        self.assertFalse(execution["first_azure_query_after_login_performed"])
        self.assertFalse(execution["what_if_performed"])
        self.assertFalse(execution["resource_group_created"])
        self.assertFalse(execution["azure_openai_account_created"])
        self.assertFalse(execution["model_deployment_created"])
        self.assertFalse(execution["rbac_mutation_performed"])
        self.assertFalse(execution["model_request_performed"])
        self.assertFalse(execution["endpoint_live"])
        authority = self.request["authority"]
        self.assertEqual(authority["status"], "consumed_failed_terminal")
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["new_deployment_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_terminal_reconciliation_preserves_no_resource_impact(self) -> None:
        self.assertEqual(self.reconciliation["workflow_run"]["run_id"], 30421206722)
        self.assertEqual(self.reconciliation["workflow_run"]["conclusion"], "failure")
        sequence = self.reconciliation["attempt_sequence"]
        self.assertEqual(sequence["azure_oidc_login"], "passed")
        self.assertEqual(sequence["authorization_guard"], "failed")
        self.assertEqual(sequence["subscription_context_query"], "not_started")
        self.assertEqual(sequence["what_if"], "not_started")
        self.assertEqual(sequence["deployment"], "not_started")
        deployed = self.reconciliation["deployed_reality"]
        self.assertFalse(deployed["resource_group_created_by_run"])
        self.assertFalse(deployed["azure_openai_account_created_by_run"])
        self.assertFalse(deployed["model_deployment_created_by_run"])
        self.assertFalse(deployed["model_request_performed"])
        self.assertFalse(deployed["endpoint_live"])
        self.assertFalse(deployed["partial_resource_cleanup_required"])

    def test_repaired_bicep_targets_resource_group_scope(self) -> None:
        self.assertIn("scope: resourceGroup(resourceGroupName)", self.bicep)
        self.assertIn("dependsOn:", self.bicep)
        self.assertIn("azureAiResourceGroup", self.bicep)
        self.assertNotIn("scope: resourceGroup!", self.bicep)


if __name__ == "__main__":
    unittest.main()
