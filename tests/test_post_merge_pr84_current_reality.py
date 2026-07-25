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
