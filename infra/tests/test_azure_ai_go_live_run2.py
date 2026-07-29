from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run2.yml"
SCRIPT = ROOT / "scripts/azure_ai_go_live_run2.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run2.json"
BICEP = ROOT / "infra/azure-ai-live.bicep"


class AzureAiGoLiveRun2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.bicep = BICEP.read_text(encoding="utf-8")

    def test_workflow_is_one_merge_trigger_without_manual_dispatch(self) -> None:
        self.assertIn("name: Azure AI go live run 2", self.workflow)
        self.assertIn("push:", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run2.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.workflow)

    def test_executor_is_bounded_and_preserves_failure_evidence(self) -> None:
        required = (
            'ATTEMPT_ID="azure-ai-go-live-run2"',
            'MODEL_NAME="gpt-4.1-mini"',
            'MODEL_VERSION="2025-04-14"',
            'DEPLOYMENT_SKU="Standard"',
            'DEPLOYMENT_CAPACITY="1"',
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

    def test_authorization_is_fresh_single_use_and_not_rerunnable(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run2")
        self.assertEqual(self.request["status"], "active_one_attempt")
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 0)
        authority = self.request["authority"]
        self.assertTrue(authority["pull_request_merge_authorized"])
        self.assertTrue(authority["merge_triggered_workflow_authorized"])
        self.assertTrue(authority["azure_authentication_authorized"])
        self.assertTrue(authority["what_if_authorized"])
        self.assertTrue(authority["azure_openai_account_creation_authorized"])
        self.assertTrue(authority["model_deployment_authorized"])
        self.assertTrue(authority["rbac_mutation_authorized"])
        self.assertTrue(authority["one_bounded_model_request_authorized"])
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_repaired_bicep_targets_resource_group_scope(self) -> None:
        self.assertIn("scope: resourceGroup(resourceGroupName)", self.bicep)
        self.assertIn("dependsOn:", self.bicep)
        self.assertIn("azureAiResourceGroup", self.bicep)
        self.assertNotIn("scope: resourceGroup!", self.bicep)


if __name__ == "__main__":
    unittest.main()
