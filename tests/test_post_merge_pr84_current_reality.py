from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Path("scripts/validate_post_merge_pr84_current_reality.py")
STRUCTURED_FIXTURE_PATHS = (
    VALIDATOR,
    Path(".project/current-reality.json"),
    Path(".project/reconciliations/post-merge-pr84-current-reality.json"),
    Path(".project/evidence/servicetracer-demo-api-timeout-fix-deployment-blocked-20260724.json"),
)


def copy_structured_validator_fixture(destination: Path) -> None:
    for relative_path in STRUCTURED_FIXTURE_PATHS:
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative_path, target)


class PostMergePr84CurrentRealityTests(unittest.TestCase):
    def test_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validation passed", result.stdout)

    def test_validator_does_not_require_handoff_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            copy_structured_validator_fixture(fixture_root)

            self.assertFalse((fixture_root / ".project/handoffs/current-state.md").exists())
            result = subprocess.run(
                [sys.executable, str(VALIDATOR)],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validation passed", result.stdout)

    def test_validator_rejects_changed_structured_pr84_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            copy_structured_validator_fixture(fixture_root)
            current_path = fixture_root / ".project/current-reality.json"
            current = json.loads(current_path.read_text(encoding="utf-8"))
            current["evidence_anchors"]["pr84_merge_commit"] = "0" * 40
            current_path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(VALIDATOR)],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PR #84 merge mismatch", result.stderr)

    def test_pr84_anchor_survives_newer_repository_state(self) -> None:
        state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(state["repository_state"]["latest_merged_pull_request"], 84)
        anchors = state["evidence_anchors"]
        self.assertEqual(
            anchors["pr84_merge_commit"],
            "c96d9cbb765a023921fa819cf7d99c957e8ad608",
        )
        self.assertEqual(
            anchors["pr84_source_head"],
            "5c938a7e07da3a22b27bb5ac5aa52b7ccf22ba37",
        )

    def test_merged_repository_is_not_collapsed_into_deployed_runtime(self) -> None:
        state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        api = state["independent_demo_api"]
        self.assertTrue(api["repository_reconciliation"]["timeout_fix_merged_into_main"])
        self.assertFalse(api["repository_reconciliation"]["timeout_fix_deployed"])
        self.assertEqual(api["runtime"]["health_contract"], "pre_timeout_fix_contract")
        self.assertFalse(api["runtime"]["corrected_timeout_fields_observed"])

    def test_blocked_deployment_did_not_mutate_azure(self) -> None:
        state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        deployment = state["independent_demo_api"]["deployment_attempt"]
        self.assertEqual(deployment["authorization_status"], "consumed_blocked")
        self.assertEqual(
            deployment["missing_action"],
            "Microsoft.Compute/virtualMachines/extensions/write",
        )
        self.assertFalse(deployment["what_if_result_observed"])
        self.assertFalse(deployment["deployment_step_executed"])
        self.assertFalse(deployment["azure_resource_mutation_performed"])
        self.assertFalse(deployment["rollback_performed"])

    def test_newer_rbac_claim_does_not_rewrite_historical_attempt(self) -> None:
        state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        operations = state["independent_demo_api"]["security_and_operations"]
        self.assertEqual(operations["required_extension_write_effective"], "unverified")
        self.assertFalse(operations["extension_updater_role_definition_observed"])
        self.assertFalse(operations["extension_updater_role_assignment_observed"])


if __name__ == "__main__":
    unittest.main()
