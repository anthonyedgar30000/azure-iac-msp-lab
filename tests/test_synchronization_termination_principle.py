from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = ROOT / ".project" / "constitution.md"
PROJECT_README = ROOT / ".project" / "README.md"
DECISIONS = ROOT / ".project" / "decisions.md"


class SynchronizationTerminationPrincipleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.constitution = CONSTITUTION.read_text(encoding="utf-8")
        self.project_readme = PROJECT_README.read_text(encoding="utf-8")
        self.decisions = DECISIONS.read_text(encoding="utf-8")

    def test_exact_canonical_name_is_adopted(self) -> None:
        for document in (self.constitution, self.project_readme, self.decisions):
            self.assertIn("Synchronization Termination Principle", document)

    def test_snapshot_is_not_a_live_dashboard(self) -> None:
        for marker in (
            "snapshot != live_dashboard",
            "snapshot_not_self_referential != stale_defect",
            "repository_merge != automatic_reconciliation_trigger",
        ):
            self.assertIn(marker, self.constitution)
            self.assertIn(marker, self.project_readme)
            self.assertIn(marker, self.decisions)

    def test_recursive_reconciliation_is_rejected(self) -> None:
        self.assertIn("reconciliation_merged", self.constitution)
        self.assertIn("reconcile_the_reconciliation", self.constitution)
        self.assertIn("no_reality_sync_churn", self.constitution)
        self.assertIn("status-only pull request", self.constitution)
        self.assertIn("status-only pull request", self.project_readme)

    def test_material_uncertainty_remains_the_trigger(self) -> None:
        self.assertIn("Material Uncertainty Synchronization Rule", self.constitution)
        self.assertIn("Material Uncertainty Synchronization Rule", self.project_readme)
        self.assertIn("Material Uncertainty Synchronization Rule", self.decisions)
        self.assertIn("no_material_uncertainty", self.constitution)
        self.assertIn("no_consequential_operation", self.constitution)

    def test_termination_does_not_grant_execution_authority(self) -> None:
        for marker in (
            "verification_authorized != deployment_authorized",
            "accepted_WhatIf != Azure_mutation_authorized",
            "failed_attempt != retry_authorized",
        ):
            self.assertIn(marker, self.constitution)


if __name__ == "__main__":
    unittest.main()
