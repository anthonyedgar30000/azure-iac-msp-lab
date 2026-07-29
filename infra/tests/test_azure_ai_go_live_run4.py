from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run4.yml"
ADAPTER = ROOT / "scripts/azure_ai_go_live_run4.sh"
SOURCE = ROOT / "scripts/azure_ai_go_live_run2.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run4.json"
RUN3_REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run3.json"
RUN3_TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run3-terminal-20260729.json"
)
RUN4_TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run4-terminal-20260729.json"
)
STATE_INDEX = ROOT / ".project/state-index.json"
BICEP = ROOT / "infra/azure-ai-live.bicep"


class AzureAiGoLiveRun4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.adapter = ADAPTER.read_text(encoding="utf-8")
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.run3_request = json.loads(RUN3_REQUEST.read_text(encoding="utf-8"))
        cls.run3_terminal = json.loads(RUN3_TERMINAL.read_text(encoding="utf-8"))
        cls.run4_terminal = json.loads(RUN4_TERMINAL.read_text(encoding="utf-8"))
        cls.state_index = json.loads(STATE_INDEX.read_text(encoding="utf-8"))
        cls.bicep = BICEP.read_text(encoding="utf-8")

    def test_workflow_remains_historical_one_merge_trigger(self) -> None:
        self.assertIn("name: Azure AI go live run 4", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run4.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.workflow)
        self.assertIn("bash scripts/azure_ai_go_live_run4.sh", self.workflow)

    def test_adapter_reuses_exact_repaired_executor_and_narrows_region(self) -> None:
        self.assertIn(
            'EXPECTED_SOURCE_BLOB="33b5ef111cb4f7b73e2978e9371e59fe9295274b"',
            self.adapter,
        )
        self.assertIn('git hash-object "$SOURCE_SCRIPT"', self.adapter)
        self.assertIn(
            "s/azure-ai-go-live-run2/azure-ai-go-live-run4/g",
            self.adapter,
        )
        self.assertIn(
            "s/azure-ai-live-run2/azure-ai-live-run4/g",
            self.adapter,
        )
        self.assertIn(
            "s/for location in canadaeast eastus2; do/for location in westus2; do/",
            self.adapter,
        )
        self.assertIn("for location in westus2; do", self.adapter)
        self.assertIn("unauthorized regional candidate", self.adapter)
        self.assertIn(".authority.automatic_retry_authorized == false", self.source)
        self.assertIn(".authority.manual_rerun_authorized == false", self.source)

    def test_run3_is_terminal_and_consumed_before_run4(self) -> None:
        self.assertEqual(self.run3_request["status"], "consumed_terminal_failure")
        self.assertFalse(self.run3_request["active"])
        self.assertEqual(self.run3_request["attempts_observed"], 1)
        self.assertEqual(
            self.run3_request["terminal_execution"]["workflow_run"],
            30422253001,
        )
        self.assertEqual(
            self.run3_terminal["root_cause"]["classification"],
            "candidate_regions_disallowed_by_subscription_policy",
        )
        self.assertFalse(
            self.run3_terminal["deployment_state"]["resource_group_created"]
        )
        self.assertFalse(self.run3_terminal["deployment_state"]["endpoint_live"])
        self.assertTrue(self.run3_terminal["authorization"]["consumed"])

    def test_run4_authorization_is_consumed_and_not_rerunnable(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run4")
        self.assertEqual(self.request["status"], "consumed_terminal_failure")
        self.assertFalse(self.request["active"])
        self.assertEqual(
            self.request["source_instruction"],
            "Proceed with Azure AI go-live run 4 in westus2 only.",
        )
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 1)
        self.assertEqual(
            self.request["repository_boundary"]["exact_merge_commit"],
            "697ef172c47e401865a4946a3acbe0df59e24c99",
        )
        self.assertEqual(self.request["scope"]["candidate_locations"], ["westus2"])
        self.assertFalse(self.request["scope"]["regional_fallback_authorized"])
        self.assertEqual(
            self.request["scope"]["resource_group_name"],
            "rg-ai-msp-dev-westus2",
        )
        self.assertEqual(self.request["scope"]["model_name"], "gpt-4.1-mini")
        self.assertEqual(self.request["scope"]["model_version"], "2025-04-14")
        self.assertEqual(self.request["scope"]["deployment_capacity"], 1)
        self.assertEqual(self.request["scope"]["model_request_count"], 1)
        self.assertEqual(self.request["scope"]["max_output_tokens"], 32)

        authority = self.request["authority"]
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["regional_fallback_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_terminal_evidence_preserves_model_listing_failure_and_no_resources(self) -> None:
        self.assertEqual(self.run4_terminal["attempt_id"], "azure-ai-go-live-run4")
        self.assertEqual(self.run4_terminal["status"], "consumed_terminal_failure")
        self.assertEqual(self.run4_terminal["workflow"]["run_id"], 30423217542)
        self.assertEqual(self.run4_terminal["artifact"]["artifact_id"], 8712644748)
        self.assertEqual(
            self.run4_terminal["root_cause"]["classification"],
            "requested_model_version_not_listed_in_westus2",
        )
        regional = self.run4_terminal["regional_observation"]
        self.assertEqual(regional["location"], "westus2")
        self.assertTrue(regional["model_listing_query_succeeded"])
        self.assertFalse(regional["model_listed"])
        self.assertFalse(regional["what_if_started"])
        self.assertFalse(regional["deployment_started"])

        deployment = self.run4_terminal["deployment_state"]
        self.assertFalse(deployment["resource_group_created"])
        self.assertFalse(deployment["azure_openai_account_created"])
        self.assertFalse(deployment["model_deployment_created"])
        self.assertFalse(deployment["inference_role_assignment_created"])
        self.assertFalse(deployment["model_request_performed"])
        self.assertFalse(deployment["endpoint_live"])
        self.assertFalse(deployment["cleanup_required"])
        self.assertTrue(self.run4_terminal["authorization"]["consumed"])

    def test_state_index_preserves_run4_history_after_run6_consumption(self) -> None:
        self.assertIsNone(self.state_index["active_azure_ai_activation_authorization"])
        self.assertEqual(
            self.state_index["previous_azure_ai_activation_reconciliation"],
            ".project/reconciliations/azure-ai-go-live-run5-terminal-20260729.json",
        )
        self.assertEqual(
            self.state_index["latest_azure_ai_activation_reconciliation"],
            ".project/reconciliations/azure-ai-go-live-run6-terminal-and-runtime-wire-20260729.json",
        )
        self.assertEqual(
            self.state_index["azure_ai_run4_workflow"],
            ".github/workflows/azure-ai-go-live-run4.yml",
        )
        self.assertTrue(self.request["scope"]["local_authentication_disabled"])
        self.assertEqual(self.request["scope"]["public_network_access"], "Enabled")
        self.assertEqual(
            self.request["scope"]["inference_role_scope"],
            "selected Azure OpenAI account only",
        )
        self.assertIn("scope: resourceGroup(resourceGroupName)", self.bicep)
        self.assertIn("deployAzureAi bool = false", self.bicep)


if __name__ == "__main__":
    unittest.main()
