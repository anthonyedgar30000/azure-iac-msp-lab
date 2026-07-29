from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run3.yml"
ADAPTER = ROOT / "scripts/azure_ai_go_live_run3.sh"
SOURCE = ROOT / "scripts/azure_ai_go_live_run2.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run3.json"
BICEP = ROOT / "infra/azure-ai-live.bicep"


class AzureAiGoLiveRun3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.adapter = ADAPTER.read_text(encoding="utf-8")
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.bicep = BICEP.read_text(encoding="utf-8")

    def test_workflow_is_one_merge_trigger_without_manual_dispatch(self) -> None:
        self.assertIn("name: Azure AI go live run 3", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run3.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.workflow)
        self.assertIn("bash scripts/azure_ai_go_live_run3.sh", self.workflow)

    def test_adapter_reuses_exact_repaired_executor(self) -> None:
        self.assertIn(
            'EXPECTED_SOURCE_BLOB="33b5ef111cb4f7b73e2978e9371e59fe9295274b"',
            self.adapter,
        )
        self.assertIn('git hash-object "$SOURCE_SCRIPT"', self.adapter)
        self.assertIn(
            "s/azure-ai-go-live-run2/azure-ai-go-live-run3/g",
            self.adapter,
        )
        self.assertIn(
            "s/azure-ai-live-run2/azure-ai-live-run3/g",
            self.adapter,
        )
        self.assertIn(".authority.automatic_retry_authorized == false", self.source)
        self.assertIn(".authority.manual_rerun_authorized == false", self.source)

    def test_authorization_is_fresh_bounded_and_single_use(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run3")
        self.assertEqual(self.request["status"], "active_one_attempt")
        self.assertEqual(self.request["source_instruction"], "Proceed")
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 0)
        self.assertEqual(
            self.request["repository_boundary"]["base_main"],
            "5c34b17eb7ccd3098d3c723261fa0f8a4d6e0c95",
        )
        self.assertEqual(
            self.request["scope"]["candidate_locations"],
            ["canadaeast", "eastus2"],
        )
        self.assertEqual(self.request["scope"]["model_name"], "gpt-4.1-mini")
        self.assertEqual(self.request["scope"]["model_version"], "2025-04-14")
        self.assertEqual(self.request["scope"]["deployment_capacity"], 1)
        self.assertEqual(self.request["scope"]["model_request_count"], 1)
        self.assertEqual(self.request["scope"]["max_output_tokens"], 32)

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

    def test_destination_and_security_boundary_are_explicit(self) -> None:
        self.assertEqual(
            self.request["scope"]["resource_group_pattern"],
            "rg-ai-msp-dev-<location>",
        )
        self.assertEqual(
            self.request["scope"]["account_pattern"],
            "oai-msp-<subscription-hash>-<location>",
        )
        self.assertTrue(self.request["scope"]["local_authentication_disabled"])
        self.assertEqual(self.request["scope"]["public_network_access"], "Enabled")
        self.assertIn("scope: resourceGroup(resourceGroupName)", self.bicep)
        self.assertIn("deployAzureAi bool = false", self.bicep)


if __name__ == "__main__":
    unittest.main()
