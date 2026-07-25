from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PostMergeCurrentRealityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        self.reconciliation = json.loads(
            (ROOT / ".project/reconciliations/post-merge-pr92-pr93-current-reality.json").read_text(
                encoding="utf-8"
            )
        )

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

    def test_repository_watermark_contains_both_merges(self) -> None:
        repo = self.state["repository_state"]
        self.assertEqual(repo["observed_head"], "665e051375594d11e58e434231bd06775dbdc560")
        self.assertEqual(repo["latest_merged_pull_request"], 92)
        self.assertEqual(repo["also_merged_pull_requests"], [93])
        self.assertEqual(repo["merge_order"], [93, 92])
        self.assertEqual(repo["open_pull_requests_observed"], [])

    def test_operator_merges_do_not_rewrite_prior_authority(self) -> None:
        operator = self.state["repository_state"]["operator_merge_reconciliation"]
        self.assertFalse(operator["pr92_recorded_agent_merge_authority"])
        self.assertFalse(operator["pr93_recorded_agent_merge_authority"])
        self.assertTrue(operator["pr92_human_operator_merge_observed"])
        self.assertTrue(operator["pr93_human_operator_merge_observed"])

    def test_green_checks_do_not_become_effective_permission(self) -> None:
        resolved = self.state["independent_demo_api"]["resolved_state"]
        self.assertTrue(resolved["protected_verify_only_check_rollup_passed"])
        self.assertFalse(resolved["protected_verify_only_artifact_inspected"])
        self.assertFalse(resolved["extension_write_permission_verified"])
        self.assertFalse(resolved["corrected_runtime_deployed"])

        rbac = self.state["rbac_reconciliation"]["resolved_state"]
        self.assertEqual(rbac["execution_truth"], "conflicting_with_new_check_rollup")
        self.assertEqual(rbac["apply_success"], "assumed_not_evidenced")
        self.assertEqual(rbac["effective_target_identity_permission"], "unverified")
        self.assertEqual(
            rbac["protected_verify_only_outcome"],
            "check_rollup_passed_exact_run_and_artifact_not_observed",
        )

    def test_repository_and_runtime_remain_separate(self) -> None:
        api = self.state["independent_demo_api"]
        repository = api["repository_reconciliation"]
        self.assertEqual(repository["main_ahead_by_commits"], 158)
        self.assertTrue(repository["verify_only_attempt_2_package_merged_into_main"])
        self.assertTrue(repository["structured_pr82_validator_fix_merged_into_main"])
        self.assertFalse(repository["timeout_fix_deployed"])
        self.assertEqual(api["runtime"]["health_contract"], "pre_timeout_fix_contract")
        self.assertFalse(api["runtime"]["corrected_timeout_fields_observed"])

    def test_reconciliation_preserves_azure_boundary(self) -> None:
        azure = self.reconciliation["azure_boundary"]
        self.assertFalse(azure["fresh_azure_inventory_performed"])
        self.assertFalse(azure["fresh_rbac_query_performed"])
        self.assertFalse(azure["fresh_runtime_test_performed"])
        self.assertFalse(azure["azure_mutation_performed"])
        self.assertEqual(azure["effective_extension_write_permission"], "unverified")

    def test_cleanup_plan_does_not_become_cleanup_fact(self) -> None:
        cleanup = self.state["resource_group_cleanup"]
        self.assertTrue(cleanup["repository_plan_merged"])
        self.assertTrue(cleanup["independent_demo_api_protected"])
        self.assertFalse(cleanup["dependency_collection_executed"])
        self.assertEqual(cleanup["candidate_current_presence"], "not_freshly_observed")
        self.assertEqual(cleanup["candidate_orphan_status"], "not_established")
        self.assertFalse(cleanup["azure_cleanup_authorized"])
        self.assertFalse(cleanup["azure_cleanup_performed"])

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
