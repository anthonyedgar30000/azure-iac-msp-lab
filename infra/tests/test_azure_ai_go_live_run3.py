from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run3.yml"
ADAPTER = ROOT / "scripts/azure_ai_go_live_run3.sh"
SOURCE = ROOT / "scripts/azure_ai_go_live_run2.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run3.json"
TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run3-terminal-20260729.json"
)
BICEP = ROOT / "infra/azure-ai-live.bicep"


class AzureAiGoLiveRun3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.adapter = ADAPTER.read_text(encoding="utf-8")
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.terminal = json.loads(TERMINAL.read_text(encoding="utf-8"))
        cls.bicep = BICEP.read_text(encoding="utf-8")

    def test_workflow_remains_historical_one_merge_trigger(self) -> None:
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

    def test_authorization_is_consumed_and_not_rerunnable(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run3")
        self.assertEqual(self.request["status"], "consumed_terminal_failure")
        self.assertFalse(self.request["active"])
        self.assertEqual(self.request["source_instruction"], "Proceed")
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 1)
        self.assertEqual(
            self.request["repository_boundary"]["exact_merge_commit"],
            "0749e1e1f99e57576726c1aaa9f25b1a6092e0d9",
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
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_terminal_evidence_preserves_policy_failure_and_no_resources(self) -> None:
        self.assertEqual(self.terminal["attempt_id"], "azure-ai-go-live-run3")
        self.assertEqual(self.terminal["status"], "consumed_terminal_failure")
        self.assertEqual(self.terminal["workflow"]["run_id"], 30422253001)
        self.assertEqual(self.terminal["artifact"]["artifact_id"], 8712343242)
        self.assertEqual(
            self.terminal["root_cause"]["classification"],
            "candidate_regions_disallowed_by_subscription_policy",
        )
        self.assertTrue(
            all(
                item["model_listed"]
                and not item["what_if_succeeded"]
                and item["error_code"] == "RequestDisallowedByAzure"
                for item in self.terminal["regional_observations"]
            )
        )
        deployment = self.terminal["deployment_state"]
        self.assertFalse(deployment["resource_group_created"])
        self.assertFalse(deployment["azure_openai_account_created"])
        self.assertFalse(deployment["model_deployment_created"])
        self.assertFalse(deployment["inference_role_assignment_created"])
        self.assertFalse(deployment["model_request_performed"])
        self.assertFalse(deployment["endpoint_live"])
        self.assertFalse(deployment["cleanup_required"])
        self.assertTrue(self.terminal["authorization"]["consumed"])

    def test_destination_and_security_boundary_remain_historical(self) -> None:
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
