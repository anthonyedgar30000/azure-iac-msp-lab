from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RECORD = (
    ROOT
    / ".project"
    / "reconciliations"
    / "collector-demo-api-what-if-run16-accepted-20260726.json"
)
REVIEW = ROOT / "docs" / "reviews" / "collector-demo-api-what-if-run16.md"


class CollectorDemoApiWhatIfRun16ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(RECORD.read_text(encoding="utf-8"))
        cls.review = REVIEW.read_text(encoding="utf-8")

    def test_record_binds_success_to_exact_reviewed_commit(self):
        attempt = self.record["observed_workflow_attempt"]
        self.assertEqual(attempt["workflow_run_number"], 16)
        self.assertEqual(attempt["event"], "workflow_dispatch")
        self.assertEqual(attempt["operation"], "what-if")
        self.assertEqual(
            attempt["reviewed_commit"],
            "8de1f61f8a0ea06dcf94b94c798edde2aace357d",
        )
        self.assertEqual(attempt["conclusion"], "success")

    def test_record_preserves_unobserved_artifact_identity_and_plan(self):
        attempt = self.record["observed_workflow_attempt"]
        plan = self.record["accepted_plan_state"]
        self.assertEqual(
            attempt["workflow_run_id"],
            "not_observed_from_available_connector_or_user_screenshot",
        )
        self.assertEqual(plan["exact_resource_change_set"], "not_observed_without_run_artifact")
        self.assertEqual(plan["artifact_id"], "not_observed")
        self.assertEqual(plan["artifact_digest"], "not_observed")
        self.assertTrue(plan["deterministic_classifier_accepted"])

    def test_no_deployment_or_replay_authority_is_created(self):
        boundary = self.record["proven_execution_boundary"]
        authority = self.record["authority"]
        next_gate = self.record["next_gate"]

        self.assertFalse(boundary["azure_mutation_performed"])
        self.assertEqual(boundary["deployment_step"], "skipped_because_operation_was_what-if")
        self.assertEqual(boundary["transaction_replay"], "not_performed")
        self.assertTrue(authority["what_if_authority_consumed"])
        self.assertFalse(authority["deployment_authorized"])
        self.assertFalse(authority["verify_operation_authorized"])
        self.assertFalse(authority["transaction_replay_authorized"])
        self.assertFalse(authority["pull_request_merge_authorized"])
        self.assertEqual(
            next_gate["deployment_decision"],
            "blocked_pending_exact_artifact_review_and_separate_explicit_authorization",
        )

    def test_review_states_canonical_claim_boundaries(self):
        for statement in (
            "workflow_success != deployment",
            "WhatIf_accepted != deployment_authorized",
            "artifact_expected != artifact_inspected",
            "not_observed != false",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, self.review)


if __name__ == "__main__":
    unittest.main()
