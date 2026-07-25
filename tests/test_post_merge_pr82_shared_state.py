from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PostMergePr82SharedStateTests(unittest.TestCase):
    def test_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_post_merge_pr82_shared_state.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validation passed", result.stdout)

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
