from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Path("scripts/validate_post_merge_pr82_shared_state.py")
STRUCTURED_FIXTURE_PATHS = (
    VALIDATOR,
    Path(".project/current-reality.json"),
    Path(".project/reconciliations/post-merge-pr82-shared-state.json"),
    Path(".project/deployment-history.jsonl"),
    Path(".project/evidence/servicetracer-demo-api-post-deployment-inventory-20260724T163938Z.json"),
    Path(".project/evidence/servicetracer-demo-api-live-verification-30086152352.json"),
)


def copy_structured_validator_fixture(destination: Path) -> None:
    for relative_path in STRUCTURED_FIXTURE_PATHS:
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative_path, target)


class PostMergePr82SharedStateTests(unittest.TestCase):
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

            # The human-facing handoff is deliberately absent. Equivalent wording or
            # punctuation must not determine machine verification.
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

    def test_validator_rejects_structured_backend_boundary_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            copy_structured_validator_fixture(fixture_root)
            current_path = fixture_root / ".project/current-reality.json"
            current = json.loads(current_path.read_text(encoding="utf-8"))
            current["independent_demo_api"]["resolved_state"]["backend_transaction_success_verified"] = True
            current_path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(VALIDATOR)],
                cwd=fixture_root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("backend boundary collapsed", result.stderr)

    def test_current_view_preserves_typed_boundaries(self) -> None:
        state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        api = state["independent_demo_api"]
        self.assertTrue(api["resolved_state"]["deployed"])
        self.assertTrue(api["resolved_state"]["public_api_verified"])
        self.assertFalse(api["resolved_state"]["corrected_runtime_deployed"])
        self.assertFalse(api["resolved_state"]["backend_transaction_success_verified"])
        self.assertFalse(api["resolved_state"]["operationally_verified"])
        self.assertFalse(api["security_and_operations"]["effective_least_privilege_verified"])
        self.assertFalse(api["security_and_operations"]["recovery_tested"])

    def test_historical_pr82_and_planner_records_are_not_erased(self) -> None:
        state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state["evidence_anchors"]["pr82_merge_commit"],
            "5dfa3b76a9fb975002d9cd702a892a0f678c88c5",
        )
        historical = state["historical_planner_evidence"]
        self.assertEqual(historical["run_id"], 30064289707)
        self.assertTrue(historical["preserved"])
        self.assertFalse(historical["current_deployment_view"])

    def test_authority_remains_fail_closed(self) -> None:
        state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        authority = state["authority"]
        self.assertTrue(authority["repository_reconciliation_authorized"])
        self.assertTrue(authority["pull_request_creation_authorized"])
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_authorized",
            "azure_authentication_authorized",
            "azure_mutations_authorized",
            "azure_rbac_mutations_authorized",
            "guest_commands_authorized",
            "transaction_replay_authorized",
            "github_pages_publication_authorized",
            "cleanup_authorized",
        ):
            self.assertFalse(authority[key], key)


if __name__ == "__main__":
    unittest.main()
