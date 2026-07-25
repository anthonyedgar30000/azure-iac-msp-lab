from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PostMergePr86Pr88CurrentRealityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))

    def test_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_post_merge_pr86_pr88_current_reality.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validation passed", result.stdout)

    def test_rbac_conflict_is_preserved(self) -> None:
        resolved = self.state["rbac_reconciliation"]["resolved_state"]
        self.assertEqual(resolved["execution_truth"], "conflicting")
        self.assertTrue(resolved["apply_attempt_asserted"])
        self.assertEqual(resolved["apply_success"], "assumed_not_evidenced")
        self.assertFalse(resolved["role_definition_observed"])
        self.assertFalse(resolved["role_assignment_observed"])
        self.assertEqual(resolved["effective_target_identity_permission"], "unverified")
        self.assertEqual(resolved["protected_verify_only_outcome"], "not_observed")

    def test_cleanup_plan_does_not_become_cleanup_fact(self) -> None:
        cleanup = self.state["resource_group_cleanup"]
        self.assertTrue(cleanup["repository_plan_merged"])
        self.assertTrue(cleanup["independent_demo_api_protected"])
        self.assertFalse(cleanup["dependency_collection_executed"])
        self.assertEqual(cleanup["candidate_current_presence"], "not_freshly_observed")
        self.assertEqual(cleanup["candidate_orphan_status"], "not_established")
        self.assertFalse(cleanup["azure_cleanup_authorized"])
        self.assertFalse(cleanup["azure_cleanup_performed"])

    def test_backup_is_explicitly_out_of_scope_without_erasing_observation(self) -> None:
        operations = self.state["independent_demo_api"]["security_and_operations"]
        self.assertEqual(operations["backup_scope"], "intentionally_out_of_scope_for_lab_v1")
        self.assertEqual(operations["recovery_services_vault_count"], 0)
        self.assertEqual(operations["other_backup_methods"], "not_observed")
        self.assertFalse(operations["recovery_tested"])

    def test_repository_and_runtime_remain_separate(self) -> None:
        api = self.state["independent_demo_api"]
        self.assertTrue(api["repository_reconciliation"]["rbac_package_merged_into_main"])
        self.assertTrue(api["repository_reconciliation"]["cleanup_plan_merged_into_main"])
        self.assertFalse(api["repository_reconciliation"]["timeout_fix_deployed"])
        self.assertFalse(api["resolved_state"]["extension_write_permission_verified"])
        self.assertFalse(api["resolved_state"]["cleanup_dependency_collection_executed"])
        self.assertFalse(api["resolved_state"]["operationally_verified"])

    def test_no_execution_authority_was_manufactured(self) -> None:
        authority = self.state["authority"]
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_authorized",
            "azure_authentication_authorized",
            "azure_mutations_authorized",
            "azure_rbac_mutations_authorized",
            "resource_graph_query_authorized",
            "guest_commands_authorized",
            "transaction_replay_authorized",
            "github_pages_publication_authorized",
            "cleanup_authorized",
        ):
            self.assertFalse(authority[key], key)


if __name__ == "__main__":
    unittest.main()
