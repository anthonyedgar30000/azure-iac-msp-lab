from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PostMergePr84CurrentRealityTests(unittest.TestCase):
    def test_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_post_merge_pr84_current_reality.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validation passed", result.stdout)

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

    def test_publication_and_replay_remain_unverified_or_unauthorized(self) -> None:
        state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        api = state["independent_demo_api"]
        self.assertFalse(api["frontend"]["github_pages_publication_verified_after_merge"])
        self.assertFalse(api["frontend"]["live_browser_rendering_of_corrected_api_verified"])
        self.assertFalse(api["runtime"]["live_twenty_attempt_replay_performed"])
        authority = state["authority"]
        self.assertFalse(authority["transaction_replay_authorized"])
        self.assertFalse(authority["github_pages_publication_authorized"])
        self.assertFalse(authority["azure_rbac_mutations_authorized"])


if __name__ == "__main__":
    unittest.main()
