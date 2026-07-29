from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run5.yml"
STATIC_WORKFLOW = ROOT / ".github/workflows/azure-ai-plan.yml"
EXECUTOR = ROOT / "scripts/azure_ai_go_live_run5.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run5.json"
CONTRACT = ROOT / ".project/contracts/azure-ai-go-live-run5-selector-v1.json"
HANDOFF = ROOT / ".project/handoffs/azure-ai-go-live-run5.md"
RUN4_REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run4.json"
RUN4_TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run4-terminal-20260729.json"
)
STATE_INDEX = ROOT / ".project/state-index.json"
BICEP_MODULE = ROOT / "infra/modules/azure_ai_openai.bicep"


class AzureAiGoLiveRun5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.static_workflow = STATIC_WORKFLOW.read_text(encoding="utf-8")
        cls.executor = EXECUTOR.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.run4_request = json.loads(RUN4_REQUEST.read_text(encoding="utf-8"))
        cls.run4_terminal = json.loads(RUN4_TERMINAL.read_text(encoding="utf-8"))
        cls.state_index = json.loads(STATE_INDEX.read_text(encoding="utf-8"))
        cls.bicep_module = BICEP_MODULE.read_text(encoding="utf-8")

    def test_workflow_is_single_merge_trigger_without_dispatch(self) -> None:
        self.assertIn("name: Azure AI go live run 5", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run5.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.workflow)
        self.assertIn("bash scripts/azure_ai_go_live_run5.sh", self.workflow)

    def test_request_targets_only_enabled_azure_for_students(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run5")
        self.assertEqual(self.request["status"], "active_one_attempt")
        self.assertTrue(self.request["active"])
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 0)
        self.assertEqual(self.request["scope"]["subscription_name"], "Azure for Students")
        self.assertEqual(self.request["scope"]["deployment_attempt_limit"], 1)
        self.assertEqual(self.request["scope"]["model_request_count"], 1)
        self.assertEqual(self.request["scope"]["max_output_tokens"], 32)
        self.assertIn('EXPECTED_SUBSCRIPTION_NAME="Azure for Students"', self.executor)
        self.assertIn('test "$subscription_name" = "$EXPECTED_SUBSCRIPTION_NAME"', self.executor)
        self.assertIn('test "$subscription_state" = "Enabled"', self.executor)

    def test_candidate_matrix_is_exact_bounded_and_ordered(self) -> None:
        candidates = self.request["scope"]["candidate_order"]
        self.assertEqual(len(candidates), 10)
        self.assertEqual(self.request["scope"]["candidate_limit"], 10)
        expected_regions = [
            "westus3",
            "westus",
            "eastus",
            "northcentralus",
            "southcentralus",
        ]
        self.assertEqual(
            [candidate["location"] for candidate in candidates[:5]],
            expected_regions,
        )
        self.assertEqual(
            [candidate["location"] for candidate in candidates[5:]],
            expected_regions,
        )
        self.assertTrue(
            all(candidate["model"] == "gpt-4o-mini" for candidate in candidates[:5])
        )
        self.assertTrue(
            all(candidate["version"] == "2024-07-18" for candidate in candidates[:5])
        )
        self.assertTrue(
            all(candidate["model"] == "gpt-4.1-mini" for candidate in candidates[5:])
        )
        self.assertTrue(
            all(candidate["version"] == "2025-04-14" for candidate in candidates[5:])
        )
        self.assertTrue(all(candidate["sku"] == "GlobalStandard" for candidate in candidates))
        self.assertNotIn("westus2", {candidate["location"] for candidate in candidates})
        self.assertNotIn("eastus2", {candidate["location"] for candidate in candidates})
        self.assertNotIn("canadaeast", {candidate["location"] for candidate in candidates})

    def test_executor_has_read_only_selection_and_one_mutation_attempt(self) -> None:
        self.assertIn("/models?api-version=2024-10-01", self.executor)
        self.assertIn("/modelCapacities?api-version=2024-10-01", self.executor)
        self.assertIn("az deployment sub what-if", self.executor)
        self.assertEqual(self.executor.count("az deployment sub create"), 1)
        self.assertIn("After the first candidate passes What-If", self.handoff)
        self.assertIn("continue_to_another_candidate_after_deployment_failure", json.dumps(self.contract))
        self.assertFalse(
            self.contract["mutation"]["continue_to_another_candidate_after_deployment_failure"]
        )
        self.assertEqual(self.contract["mutation"]["deployment_attempt_limit"], 1)
        self.assertIn("assignInferenceRole=true", self.executor)
        self.assertIn("inferencePrincipalId=\"$principal_id\"", self.executor)

    def test_executor_makes_exactly_one_model_request(self) -> None:
        self.assertEqual(self.executor.count("curl --silent --show-error"), 1)
        self.assertNotIn("for propagation_attempt", self.executor)
        self.assertIn("sleep 90", self.executor)
        self.assertIn("model_request_count:1", self.executor)
        self.assertEqual(self.contract["verification"]["model_request_count"], 1)
        self.assertEqual(self.contract["verification"]["max_output_tokens"], 32)
        self.assertEqual(self.request["scope"]["prompt"], "Reply with exactly: AZURE AI LIVE")

    def test_security_cost_and_failure_boundaries_are_fail_closed(self) -> None:
        authority = self.request["authority"]
        self.assertTrue(authority["one_resource_group_creation_authorized"])
        self.assertTrue(authority["one_azure_openai_account_creation_authorized"])
        self.assertTrue(authority["one_model_deployment_authorized"])
        self.assertTrue(authority["one_account_scoped_rbac_mutation_authorized"])
        self.assertTrue(authority["one_bounded_model_request_authorized"])
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(authority["second_deployment_attempt_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertFalse(authority["cleanup_authorized"])
        self.assertTrue(self.request["scope"]["local_authentication_disabled"])
        self.assertEqual(self.request["scope"]["public_network_access"], "Enabled")
        self.assertEqual(self.request["cost_boundary"]["deployment_type"], "GlobalStandard pay-as-you-go")
        self.assertFalse(self.request["cost_boundary"]["provisioned_throughput_authorized"])
        self.assertIn("'GlobalStandard'", self.bicep_module)
        self.assertIn("disableLocalAuth: true", self.bicep_module)
        self.assertIn("scope: account", self.bicep_module)

    def test_run4_is_consumed_before_run5(self) -> None:
        self.assertEqual(self.run4_request["status"], "consumed_terminal_failure")
        self.assertFalse(self.run4_request["active"])
        self.assertEqual(self.run4_request["attempts_observed"], 1)
        self.assertEqual(self.run4_terminal["workflow"]["run_id"], 30423217542)
        self.assertEqual(
            self.run4_terminal["root_cause"]["classification"],
            "requested_model_version_not_listed_in_westus2",
        )
        self.assertFalse(self.run4_terminal["deployment_state"]["resource_group_created"])
        self.assertFalse(self.run4_terminal["deployment_state"]["endpoint_live"])
        self.assertTrue(self.run4_terminal["authorization"]["consumed"])

    def test_state_index_activates_run5_and_preserves_run4_terminal_truth(self) -> None:
        self.assertEqual(
            self.state_index["active_azure_ai_activation_authorization"],
            ".project/deployment-requests/azure-ai-go-live-run5.json",
        )
        self.assertEqual(
            self.state_index["latest_consumed_azure_ai_activation_authorization"],
            ".project/reconciliations/azure-ai-go-live-run4-terminal-20260729.json",
        )
        self.assertEqual(
            self.state_index["latest_azure_ai_activation_reconciliation"],
            ".project/reconciliations/azure-ai-go-live-run4-terminal-20260729.json",
        )
        self.assertEqual(
            self.state_index["azure_ai_run5_workflow"],
            ".github/workflows/azure-ai-go-live-run5.yml",
        )
        self.assertEqual(
            self.state_index["azure_ai_run5_selector_contract"],
            ".project/contracts/azure-ai-go-live-run5-selector-v1.json",
        )

    def test_static_validation_includes_run5_without_cloud_identity(self) -> None:
        self.assertIn("infra.tests.test_azure_ai_go_live_run5", self.static_workflow)
        self.assertIn("bash -n scripts/azure_ai_go_live_run5.sh", self.static_workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run5.yml'", self.static_workflow)
        self.assertIn("id-token: none", self.static_workflow)


if __name__ == "__main__":
    unittest.main()
