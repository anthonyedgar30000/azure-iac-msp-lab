from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION = ROOT / ".project" / "reconciliations" / "post-pr100-normalization-20260725.json"


class PostPr100NormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(RECONCILIATION.read_text(encoding="utf-8"))

    def test_temporary_write_machinery_is_absent(self) -> None:
        for path in (
            ROOT / ".github" / "workflows" / "apply-post-pr99-evidence-promotion.yml",
            ROOT / "scripts" / "apply_post_pr99_evidence_promotion.py",
        ):
            with self.subTest(path=path):
                self.assertFalse(path.exists(), f"temporary write path must remain absent: {path}")

    def test_historical_evidence_and_authority_records_are_preserved(self) -> None:
        for relative in self.record["preserved_paths"]:
            path = ROOT / relative
            with self.subTest(path=relative):
                self.assertTrue(path.exists(), f"historical record missing: {relative}")

        evidence = self.record["preserved_evidence"]
        self.assertEqual(evidence["historical_protected_run_id"], 30160680313)
        self.assertEqual(evidence["historical_protected_artifact_id"], 8620163872)
        self.assertTrue(evidence["effective_extension_write_permission_verified"])
        self.assertFalse(evidence["azure_mutation_performed"])
        self.assertFalse(evidence["deployment_authorized"])

    def test_normalization_does_not_claim_canonical_promotion(self) -> None:
        normalization = self.record["normalization"]
        self.assertTrue(normalization["temporary_write_workflow_removed"])
        self.assertTrue(normalization["temporary_promotion_script_removed"])
        self.assertEqual(
            normalization["canonical_state_promotion_status"],
            "pending_separate_repository_increment",
        )

    def test_operational_authority_remains_false(self) -> None:
        authority = self.record["authority"]
        for field in (
            "pull_request_merge",
            "workflow_dispatch_or_rerun",
            "azure_authentication",
            "azure_query",
            "azure_mutation",
            "deployment",
            "rbac_mutation",
            "guest_command",
            "transaction_replay",
            "cleanup",
        ):
            with self.subTest(field=field):
                self.assertFalse(authority[field])

        self.assertFalse(self.record["next_gate"]["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
