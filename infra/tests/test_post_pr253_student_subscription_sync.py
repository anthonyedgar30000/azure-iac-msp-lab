from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SELECTOR = ROOT / ".project/CURRENT.json"
REALITY = ROOT / ".project/current-reality-v5.json"
INDEX = ROOT / ".project/state-index-v14.json"
HANDOFF = ROOT / ".project/handoffs/current-state-v4.md"
SYNC = ROOT / ".project/reconciliations/post-pr253-student-subscription-sync-20260730.json"
WORKFLOW = ROOT / ".github/workflows/servicetracer-demo-api-subproject-plan.yml"

MAIN = "af4b050ab18110882e3551f66c69eb2b73a73f7b"
PR253_SOURCE = "161c447a445d86364719d3d414ac6c7f6628e7b8"


class PostPr253StudentSubscriptionSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector = json.loads(SELECTOR.read_text(encoding="utf-8"))
        cls.reality = json.loads(REALITY.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.sync = json.loads(SYNC.read_text(encoding="utf-8"))
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_selector_promotes_post_pr253_state(self) -> None:
        self.assertEqual(
            self.selector["authoritative_current_reality"],
            ".project/current-reality-v5.json",
        )
        self.assertEqual(
            self.selector["authoritative_state_index"],
            ".project/state-index-v14.json",
        )
        self.assertEqual(
            self.selector["authoritative_handoff"],
            ".project/handoffs/current-state-v4.md",
        )
        self.assertEqual(
            self.selector["latest_repository_sync_reconciliation"],
            ".project/reconciliations/post-pr253-student-subscription-sync-20260730.json",
        )
        self.assertIsNone(self.selector["active_servicetracer_planning_authorization"])
        self.assertIsNone(self.selector["active_deployment_authorization"])

    def test_repository_watermark_records_pr253(self) -> None:
        repo = self.reality["repository_state"]
        self.assertEqual(repo["observed_main"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 253)
        self.assertEqual(repo["latest_merged_source_head"], PR253_SOURCE)
        self.assertEqual(repo["latest_exact_head_ci"]["ci_run_id"], 30516607869)
        self.assertEqual(repo["latest_exact_head_ci"]["ci_conclusion"], "success")
        self.assertEqual(repo["open_pull_requests_observed"], [])
        self.assertFalse(repo["merge_commit_ci_observed"])

    def test_planner_is_single_student_subscription_and_non_deploying(self) -> None:
        state = self.reality["domain_state"]["azure_lab_factory_lite"]
        self.assertEqual(state["planner_binding_pull_request"], 253)
        self.assertEqual(state["github_environment"], "azure-lab")
        self.assertEqual(state["subscription_boundary"], "single_subscription")
        self.assertEqual(state["subscription_intent"], "Azure for Students only")
        self.assertEqual(state["azure_login_count"], 1)
        self.assertFalse(state["corrected_planner_dispatch_verified"])
        self.assertFalse(state["deployment_capability"])

        for marker in (
            "environment: azure-lab",
            "AZURE_CLIENT_ID",
            "AZURE_TENANT_ID",
            "AZURE_SUBSCRIPTION_ID",
            'subscription_boundary:"single_subscription"',
            "ProviderNoRbac",
            "az deployment sub validate",
            "az deployment sub what-if",
        ):
            self.assertIn(marker, self.workflow)
        for obsolete in (
            "environment: azure-api-payg",
            "AZURE_DEPENDENCY_CLIENT_ID",
            "AZURE_TARGET_CLIENT_ID",
            "AZURE_DEPENDENCY_SUBSCRIPTION_ID",
            "AZURE_TARGET_SUBSCRIPTION_ID",
            "az deployment sub create",
            "az role assignment create",
        ):
            self.assertNotIn(obsolete, self.workflow)
        self.assertEqual(self.workflow.count("uses: azure/login@v2"), 1)

    def test_recent_azure_lab_evidence_is_bounded(self) -> None:
        evidence = self.reality["domain_state"]["azure_lab_protected_environment_evidence"]
        self.assertEqual(evidence["workflow_environment"], "azure-lab")
        self.assertEqual(evidence["observed_run_id"], 30510660758)
        self.assertEqual(evidence["subscription_name"], "Azure for Students")
        self.assertEqual(evidence["subscription_state"], "Enabled")
        self.assertFalse(evidence["fresh_administrative_secret_inspection_performed"])
        self.assertIn("does not authorize", evidence["claim_boundary"])

    def test_historical_plan_is_not_reclassified_as_current(self) -> None:
        historical = self.reality["domain_state"]["servicetracer_planning_run1_historical"]
        self.assertEqual(historical["old_subscription_boundary"], "dual_subscription")
        self.assertEqual(historical["failure_classification"], "confirmation_input_mismatch")
        self.assertTrue(historical["authority_consumed"])
        self.assertFalse(historical["rerun_authorized"])
        self.assertFalse(historical["azure_login_started"])
        self.assertTrue(historical["preserved_as_historical_evidence"])

    def test_no_operational_authority_remains(self) -> None:
        self.assertTrue(all(value is None for value in self.index["active_authorizations"].values()))
        authority = self.sync["authority"]
        self.assertTrue(authority["repository_branch_and_declared_writes"])
        self.assertTrue(authority["pull_request_creation"])
        self.assertTrue(authority["ordinary_exact_head_ci"])
        for denied in (
            "workflow_dispatch_or_rerun_by_this_sync",
            "azure_authentication_or_query_by_this_sync",
            "arm_what_if_by_this_sync",
            "azure_mutation_by_this_sync",
            "github_environment_or_secret_mutation",
            "entra_identity_mutation",
            "rbac_mutation",
            "deployment",
            "cleanup",
            "rollback",
        ):
            self.assertFalse(authority[denied], denied)

    def test_handoff_names_next_gate_and_unknowns(self) -> None:
        self.assertIn(f"observed main: {MAIN}", self.handoff)
        self.assertIn("latest merged PR: #253", self.handoff)
        self.assertIn("subscription boundary: single_subscription", self.handoff)
        self.assertIn("subscription name: Azure for Students", self.handoff)
        self.assertIn("corrected planner has not been dispatched", self.handoff)
        self.assertIn("active ServiceTracer planning authority: none", self.handoff)
        self.assertIn("current student credit", self.handoff)
        self.assertIn("fresh explicit one-attempt read-only authority", self.handoff)


if __name__ == "__main__":
    unittest.main()
