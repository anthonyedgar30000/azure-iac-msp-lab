from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / ".project" / "lab-v1-completion-gate.json"
DOCUMENT_PATH = ROOT / "docs" / "lab-v1-completion-gate.md"

EXPECTED_OBJECTIVE = (
    "Complete and evidence-lock one production-shaped ServiceTracer workload "
    "from infrastructure-as-code declaration through deployment, security, "
    "runtime validation, monitoring, cost observation, and portfolio demonstration."
)

EXPECTED_P0_IDS = {
    "p0-protected-verification-evidence",
    "p0-effective-extension-permission",
    "p0-timeout-correction-deployment",
    "p0-runtime-contract",
    "p0-servicetracer-scenario",
    "p0-browser-demonstration",
    "p0-evidence-lock",
}

EXPECTED_FROZEN = {
    "zoomable hyperscaler or infrastructure-universe dashboard",
    "broader Azure Resource Graph visualization",
    "multicloud control plane",
    "additional workloads",
    "full collector replacement",
    "recovery rehearsal and disaster recovery",
    "automated cleanup execution",
    "MSP multi-customer tenancy",
    "HELIX integration",
    "new governance engines or authority abstractions",
    "additional dashboards",
    "additional AI agents",
}

FALSE_OPERATIONAL_AUTHORITY = {
    "pull_request_merge",
    "workflow_dispatch_or_rerun",
    "azure_authentication",
    "azure_query",
    "azure_mutation",
    "deployment",
    "rbac_mutation",
    "guest_command",
    "transaction_replay",
    "endpoint_publication",
    "cleanup",
}


class LabV1CompletionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
        cls.document = DOCUMENT_PATH.read_text(encoding="utf-8")

    def test_gate_identity_and_objective_are_canonical(self) -> None:
        self.assertEqual(
            self.gate["schema_version"],
            "project.lab-v1-completion-gate.v1",
        )
        self.assertEqual(
            self.gate["project"],
            "ServiceTracer — Governed Azure Operations Lab",
        )
        self.assertEqual(self.gate["governing_objective"], EXPECTED_OBJECTIVE)
        self.assertEqual(
            self.gate["decision_status"],
            "proposed_repository_authority_pending_review_and_merge",
        )

    def test_priority_order_is_p0_p1_p2(self) -> None:
        priorities = self.gate["priority_order"]
        self.assertEqual(
            [item["priority"] for item in priorities],
            ["P0", "P1", "P2"],
        )
        p0 = priorities[0]
        self.assertEqual(
            {item["criterion_id"] for item in p0["exit_criteria"]},
            EXPECTED_P0_IDS,
        )

    def test_scope_freeze_blocks_parallel_expansion(self) -> None:
        scope = self.gate["scope_control"]
        self.assertFalse(scope["parallel_feature_expansion_allowed"])
        self.assertFalse(scope["new_workload_allowed"])
        self.assertFalse(scope["new_governance_abstraction_allowed"])
        self.assertEqual(
            scope["non_admitted_disposition"],
            "design_for_or_future_vision",
        )
        self.assertEqual(
            set(self.gate["frozen_until_p0_p2_complete"]),
            EXPECTED_FROZEN,
        )

    def test_backup_is_explicitly_out_of_scope_for_lab_v1(self) -> None:
        p1 = self.gate["priority_order"][1]
        exclusion = p1["explicit_exclusion"]
        self.assertEqual(
            exclusion["backup_and_recovery_services"],
            "intentionally_out_of_scope_for_lab_v1",
        )
        self.assertEqual(
            exclusion["disaster_recovery_rehearsal"],
            "future_revision",
        )

    def test_operational_authority_remains_false(self) -> None:
        authority = self.gate["authority"]
        self.assertTrue(authority["repository_gate_documentation"])
        self.assertTrue(authority["repository_gate_test"])
        self.assertTrue(authority["branch_creation"])
        self.assertTrue(authority["draft_pull_request_creation"])
        for field in FALSE_OPERATIONAL_AUTHORITY:
            with self.subTest(field=field):
                self.assertFalse(authority[field])

    def test_creation_baseline_preserves_parallel_pr_boundary(self) -> None:
        baseline = self.gate["creation_baseline"]
        self.assertEqual(
            baseline["base_commit"],
            "630bbd8c9c37a3985a70dbe6bffe10437672a59d",
        )
        self.assertEqual(
            baseline["open_pull_requests_observed"],
            [
                {
                    "pull_request": 95,
                    "title": "Adopt the Synchronization Termination Principle",
                    "relationship": "separate_non_overlapping_constitutional_increment",
                }
            ],
        )
        self.assertFalse(baseline["azure_query_performed_for_this_increment"])

    def test_completion_boundaries_remain_visible(self) -> None:
        boundaries = set(self.gate["completion_definition"]["boundaries"])
        for marker in {
            "merged_into_main != deployed_to_Azure",
            "deployment_succeeded != service_validated",
            "RBAC_assignment != effective_least_privilege",
            "monitoring_enabled != alerts_verified",
            "estimated_cost != actual_cost",
            "backup_intentionally_out_of_scope != backup_verified",
        }:
            with self.subTest(marker=marker):
                self.assertIn(marker, boundaries)

    def test_human_document_contains_required_decisions(self) -> None:
        for marker in (
            "P0 — Complete the golden path",
            "P1 — Make the workload credibly operable",
            "P2 — Package the portfolio proof",
            "interesting != priority",
            "architecturally_valid != build_now",
            "backup_scope = intentionally_out_of_scope_for_lab_v1",
            "priority_decision != operational_authorization",
            "Inspect and promote the exact existing PR #92 protected verify-only run and artifact.",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.document)


if __name__ == "__main__":
    unittest.main()
