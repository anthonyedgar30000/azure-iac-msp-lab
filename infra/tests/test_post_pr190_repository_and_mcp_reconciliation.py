from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / ".project/state-index.json"
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr190-repository-and-mcp-reconciliation-20260728.json"
)
HANDOFF = ROOT / ".project/handoffs/post-pr190-current-state.md"
CONTRACT = ROOT / ".project/contracts/durable-single-use-authorization-ledger-v1.json"
MCP_WORKFLOW = ROOT / ".github/workflows/azure-mcp-read-only-preflight.yml"
COLLECTOR_WORKFLOW = ROOT / ".github/workflows/collector-demo-api.yml"

MAIN = "bae07d24c59f7bc02001a168c7c6aac188ff2747"
PR190_SOURCE = "e7e4fc3e169a054789250062bcee8b3293561aa7"
RECONCILIATION_PATH = (
    ".project/reconciliations/post-pr190-repository-and-mcp-reconciliation-20260728.json"
)
HANDOFF_PATH = ".project/handoffs/post-pr190-current-state.md"


class PostPr190RepositoryAndMcpReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.mcp_workflow = MCP_WORKFLOW.read_text(encoding="utf-8")
        cls.collector_workflow = COLLECTOR_WORKFLOW.read_text(encoding="utf-8")

    def test_state_index_preserves_post_pr190_as_the_previous_boundary(self) -> None:
        self.assertEqual(
            self.index["previous_repository_and_mcp_reconciliation"],
            RECONCILIATION_PATH,
        )
        self.assertNotEqual(
            self.index["latest_repository_and_mcp_reconciliation"],
            RECONCILIATION_PATH,
        )
        self.assertNotEqual(self.index["latest_repository_handoff"], HANDOFF_PATH)
        self.assertEqual(self.index["superseded_open_pull_request"], 189)
        self.assertIn(
            "workflow_on_main != workflow_dispatched",
            self.index["claim_boundaries"],
        )
        self.assertIn(
            "endpoint_deployed != OpenAI_client_connected",
            self.index["claim_boundaries"],
        )

    def test_live_repository_state_advances_through_pr190(self) -> None:
        github = self.reconciliation["github_state"]
        self.assertEqual(github["observed_main"], MAIN)
        self.assertEqual(github["latest_merged_pull_request"], 190)
        self.assertEqual(github["latest_merged_source_head"], PR190_SOURCE)
        self.assertEqual(github["latest_merge_commit"], MAIN)
        self.assertEqual(github["open_pull_requests_observed"], [189])
        self.assertEqual(github["merge_commit_pr_triggered_ci"], "not_observed")
        self.assertTrue(github["pull_request_188"]["merged"])
        self.assertTrue(github["pull_request_190"]["merged"])
        self.assertEqual(
            github["pull_request_190"]["exact_head_ci_runs"]["ci"]["run_id"],
            30409464240,
        )
        self.assertEqual(
            github["pull_request_190"]["exact_head_ci_runs"][
                "azure_mcp_architecture_and_cloud_shell_plan"
            ]["run_id"],
            30409464252,
        )

    def test_stale_pr189_is_not_promoted_as_current_truth(self) -> None:
        stale = self.reconciliation["github_state"]["pull_request_189"]
        self.assertEqual(stale["state"], "open_stale_nonmergeable")
        self.assertEqual(stale["ahead_of_current_main_by_commits"], 9)
        self.assertEqual(stale["behind_current_main_by_commits"], 13)
        self.assertIn("PR #189", self.handoff)
        self.assertIn("must not be merged unchanged", self.handoff)

    def test_durable_authorization_is_merged_but_not_activated(self) -> None:
        control = self.reconciliation["authorization_control_state"]
        self.assertEqual(
            control["classification"],
            "implemented_on_main_inactive_not_operationally_verified",
        )
        self.assertEqual(control["post_merge_reconciliation_pull_request"], 188)
        self.assertEqual(control["protected_consumption_ruleset"], "not_observed")
        self.assertFalse(control["collector_workflow_restored"])
        self.assertFalse(control["azure_execution_enabled"])
        self.assertFalse(control["operationally_verified"])

        self.assertEqual(
            self.contract["status"],
            "implementation_merged_not_activated",
        )
        self.assertTrue(self.contract["activation"]["merged_to_main"])
        self.assertFalse(self.contract["activation"]["ruleset_configured"])
        self.assertFalse(self.contract["activation"]["live_claim_test_performed"])

    def test_mcp_preflight_is_on_main_but_not_executed_at_this_boundary(self) -> None:
        mcp = self.reconciliation["azure_mcp_preflight_state"]
        self.assertEqual(mcp["classification"], "implemented_on_main_not_dispatched")
        self.assertTrue(mcp["manual_dispatch_only"])
        self.assertTrue(mcp["exact_reviewed_commit_required"])
        self.assertTrue(mcp["explicit_confirmation_required"])
        self.assertFalse(mcp["azure_mutation_entry_point_present"])
        self.assertFalse(mcp["openai_api_entry_point_present"])
        self.assertFalse(mcp["workflow_dispatch_observed"])
        self.assertFalse(mcp["azure_authentication_observed"])
        self.assertFalse(mcp["fresh_azure_query_observed"])
        self.assertFalse(mcp["template_source_pinned"])
        self.assertFalse(mcp["endpoint_deployed"])
        self.assertFalse(mcp["openai_client_connected"])

        self.assertIn("workflow_dispatch:", self.mcp_workflow)
        self.assertIn("uses: azure/login@v2", self.mcp_workflow)
        self.assertNotIn("azd up", self.mcp_workflow)
        self.assertNotIn("OPENAI_API_KEY", self.mcp_workflow)

    def test_collector_and_cloud_authority_remain_fail_closed(self) -> None:
        self.assertIn("Collector-hosted demo API — quarantined", self.collector_workflow)
        self.assertNotIn("id-token: write", self.collector_workflow)
        self.assertNotIn("uses: azure/login", self.collector_workflow)

        authority = self.reconciliation["authority"]
        self.assertTrue(authority["repository_reconciliation_authorized"])
        self.assertTrue(authority["supersede_stale_pull_request_authorized"])
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_or_rerun_authorized",
            "live_authorization_claim_authorized",
            "repository_ruleset_mutation_authorized",
            "azure_authentication_authorized",
            "azure_query_authorized",
            "azure_mutation_authorized",
            "deployment_authorized",
            "openai_api_execution_authorized",
            "rollback_authorized",
            "cleanup_authorized",
            "rbac_mutation_authorized",
        ):
            self.assertFalse(authority[key], key)

        azure = self.reconciliation["azure_boundary"]
        self.assertFalse(azure["fresh_live_query_performed"])
        self.assertFalse(azure["runtime_truth_changed_by_this_reconciliation"])
        self.assertEqual(azure["expected_recurring_cost_delta_CAD"], 0)


if __name__ == "__main__":
    unittest.main()
