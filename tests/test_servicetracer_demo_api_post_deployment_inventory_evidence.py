from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".project/evidence/servicetracer-demo-api-post-deployment-inventory-20260724T163938Z.json"
FOLLOW_UP = ROOT / ".project/reconciliations/servicetracer-demo-api-post-deployment-follow-up.json"
RUNNER = ROOT / "scripts/servicetracer_demo_api_readonly_follow_up.py"


class PostDeploymentEvidenceTests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_validator_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_servicetracer_demo_api_post_deployment_inventory_evidence.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_manifest_and_archive_are_anchored(self) -> None:
        source = self.load(EVIDENCE)["evidence_source"]
        self.assertEqual(source["manifest_entry_count"], 21)
        self.assertEqual(len(source["manifest_entries"]), 21)
        self.assertTrue(source["manifest_hashes_verified"])
        self.assertFalse(source["raw_archive_committed"])

    def test_observed_and_unobserved_states_are_separate(self) -> None:
        evidence = self.load(EVIDENCE)
        self.assertTrue(evidence["combined_verification"]["deployment_provenance_verified"])
        self.assertTrue(evidence["combined_verification"]["public_endpoint_identity_verified"])
        self.assertFalse(evidence["combined_verification"]["effective_rbac_observed"])
        self.assertFalse(evidence["combined_verification"]["backup_observed"])
        self.assertFalse(evidence["combined_verification"]["actual_cost_observed"])

    def test_corrected_runner_repairs_known_defects(self) -> None:
        runner = RUNNER.read_text(encoding="utf-8")
        cost = runner[runner.index("def collect_cost"):runner.index("def collect_backup")]
        backup = runner[runner.index("def collect_backup"):runner.index("def main")]
        rbac_start = runner.index("def collect_rbac")
        rbac = runner[rbac_start:runner.index("def collect_cost", rbac_start)]
        self.assertNotIn('"Currency"', cost)
        self.assertIn('"ResourceId"', cost)
        self.assertIn('"backup", "item", "list"', backup)
        self.assertNotIn('"extension", "show"', backup)
        self.assertNotIn('"--all"', rbac)

    def test_follow_up_is_not_authorized(self) -> None:
        plan = self.load(FOLLOW_UP)
        self.assertEqual(plan["status"], "repository_plan_only")
        self.assertFalse(plan["execution_boundary"]["execution_authorized"])
        self.assertFalse(plan["execution_boundary"]["azure_mutations_authorized"])


if __name__ == "__main__":
    unittest.main()
