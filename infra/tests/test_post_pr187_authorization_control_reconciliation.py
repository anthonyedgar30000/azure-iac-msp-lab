from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / ".project/state-index.json"
CURRENT = ROOT / ".project/current-reality-v2.json"
GATE = ROOT / ".project/lab-v1-completion-gate-v2.json"
HANDOFF = ROOT / ".project/handoffs/current-state.md"
RECONCILIATION = ROOT / ".project/reconciliations/post-pr187-authorization-control-reconciliation-20260728.json"
DURABLE_WORKFLOW = ROOT / ".github/workflows/durable-authorization-claim-v1.yml"
COLLECTOR_WORKFLOW = ROOT / ".github/workflows/collector-demo-api.yml"

MAIN = "07f32b59eda11b5a3627d398f1ffca00c8c88e69"
PR186_SOURCE = "138659609b15ef80f6cce12d916e26382ab71205"
PR186_MERGE = "30e312ef5122831a8233835db2f541437a97b125"
PR187_SOURCE = "44bc3ab202c2e3d709aa2d9906ef9aba365acfb2"
RECONCILIATION_PATH = ".project/reconciliations/post-pr187-authorization-control-reconciliation-20260728.json"
PREVIOUS_RECONCILIATION_PATH = ".project/reconciliations/post-pr185-repository-watermark-20260728.json"


class PostPr187AuthorizationControlReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.current = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.gate = json.loads(GATE.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.durable_workflow = DURABLE_WORKFLOW.read_text(encoding="utf-8")
        cls.collector_workflow = COLLECTOR_WORKFLOW.read_text(encoding="utf-8")

    def test_state_index_selects_the_post_pr187_reconciliation(self) -> None:
        self.assertEqual(
            self.index["latest_repository_reconciliation"],
            PREVIOUS_RECONCILIATION_PATH,
        )
        self.assertEqual(
            self.index["latest_repository_watermark_reconciliation"],
            PREVIOUS_RECONCILIATION_PATH,
        )
        self.assertEqual(
            self.index["latest_lifecycle_reconciliation"],
            RECONCILIATION_PATH,
        )
        self.assertEqual(
            self.index["latest_authorization_control_reconciliation"],
            RECONCILIATION_PATH,
        )
        self.assertIn(
            "control_implemented_on_main != control_activated",
            self.index["claim_boundaries"],
        )
        self.assertIn(
            "stale_snapshot_lifecycle != live_repository_state",
            self.index["claim_boundaries"],
        )

    def test_live_repository_lifecycle_is_recorded_without_rewriting_history(self) -> None:
        github = self.reconciliation["github_state"]
        self.assertEqual(github["observed_main"], MAIN)
        self.assertEqual(github["latest_merged_pull_request"], 187)
        self.assertEqual(github["latest_merged_source_head"], PR187_SOURCE)
        self.assertEqual(github["latest_merge_commit"], MAIN)
        self.assertEqual(github["open_pull_requests_observed"], [])
        self.assertEqual(github["merge_commit_pr_triggered_ci"], "not_observed")

        pr186 = github["pull_request_186"]
        self.assertTrue(pr186["merged"])
        self.assertEqual(pr186["source_head"], PR186_SOURCE)
        self.assertEqual(pr186["merge_commit"], PR186_MERGE)

        self.assertEqual(
            self.current["repository_state"]["latest_merged_pull_request"],
            185,
        )
        self.assertEqual(
            self.current["repository_state"]["open_pull_requests_after_frontend_architecture_merge"],
            [186],
        )
        self.assertIn("Draft PR #186", self.handoff)
        self.assertEqual(
            self.gate["evidence_inputs"]["open_authorization_ledger_candidate_pull_request"],
            186,
        )
        self.assertEqual(len(self.reconciliation["stale_lifecycle_conflicts"]), 3)

    def test_exact_head_ci_is_preserved_without_inventing_merge_commit_ci(self) -> None:
        ci = self.reconciliation["exact_head_ci"]
        self.assertEqual(
            ci["pull_request_186"]["runs"]["ci"]["run_id"],
            30389249099,
        )
        self.assertEqual(
            ci["pull_request_186"]["runs"]["ci"]["conclusion"],
            "success",
        )

        pr187_runs = ci["pull_request_187"]["runs"]
        self.assertEqual(
            {run["run_id"] for run in pr187_runs.values()},
            {30390614963, 30390618165, 30390616682, 30390616307},
        )
        self.assertTrue(
            all(run["conclusion"] == "success" for run in pr187_runs.values())
        )
        self.assertEqual(
            self.reconciliation["github_state"]["merge_commit_pr_triggered_ci"],
            "not_observed",
        )

    def test_authorization_control_is_implemented_but_not_activated(self) -> None:
        control = self.reconciliation["authorization_control_state"]
        self.assertEqual(
            control["classification"],
            "implemented_on_main_inactive_not_operationally_verified",
        )
        self.assertEqual(control["implementation_pull_request"], 186)
        self.assertEqual(control["implementation_source_head"], PR186_SOURCE)
        self.assertEqual(control["implementation_merge_commit"], PR186_MERGE)
        self.assertEqual(control["implementation_exact_head_ci_run"], 30389249099)
        self.assertEqual(control["claim_job_id_token_permission"], "none")
        self.assertFalse(control["azure_login_or_cli_present"])
        self.assertEqual(control["protected_consumption_ruleset"], "not_observed")
        self.assertEqual(control["live_first_claim"], "not_observed")
        self.assertEqual(control["live_replay_rejection"], "not_observed")
        self.assertEqual(control["concurrent_duplicate_claim_proof"], "not_observed")
        self.assertFalse(control["operationally_verified"])
        self.assertFalse(control["collector_workflow_restored"])

    def test_static_workflow_boundaries_remain_fail_closed(self) -> None:
        self.assertIn("workflow_call:", self.durable_workflow)
        self.assertIn("id-token: none", self.durable_workflow)
        self.assertIn(
            "refs/tags/authority-consumed/$REQUEST_ID",
            self.durable_workflow,
        )
        self.assertNotIn("azure/login", self.durable_workflow)
        self.assertNotIn("az login", self.durable_workflow)

        self.assertIn(
            "Collector-hosted demo API — quarantined",
            self.collector_workflow,
        )
        self.assertIn(
            "Reject quarantined collector operation",
            self.collector_workflow,
        )
        self.assertIn("exit 1", self.collector_workflow)
        self.assertNotIn("id-token: write", self.collector_workflow)
        self.assertNotIn("uses: azure/login", self.collector_workflow)

    def test_authority_and_azure_boundaries_remain_closed(self) -> None:
        authority = self.reconciliation["authority"]
        self.assertTrue(authority["repository_reconciliation_authorized"])
        self.assertTrue(authority["draft_pull_request_creation_authorized"])
        self.assertTrue(authority["ordinary_pull_request_ci_authorized"])

        for key in (
            "pull_request_merge_authorized",
            "ready_for_review_transition_authorized",
            "workflow_dispatch_or_rerun_authorized",
            "live_authorization_claim_authorized",
            "repository_ruleset_mutation_authorized",
            "azure_authentication_authorized",
            "azure_query_authorized",
            "azure_mutation_authorized",
            "deployment_authorized",
            "rollback_authorized",
            "cleanup_authorized",
            "rbac_mutation_authorized",
        ):
            self.assertFalse(authority[key], key)

        azure = self.reconciliation["azure_boundary"]
        self.assertFalse(azure["fresh_live_query_performed"])
        self.assertFalse(azure["runtime_truth_changed_by_this_reconciliation"])
        self.assertFalse(azure["Azure_resource_change_claimed"])
        self.assertFalse(azure["Azure_quota_change_claimed"])
        self.assertEqual(azure["expected_recurring_cost_delta_CAD"], 0)


if __name__ == "__main__":
    unittest.main()
