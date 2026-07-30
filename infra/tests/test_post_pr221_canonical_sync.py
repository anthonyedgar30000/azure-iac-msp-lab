from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SELECTOR = ROOT / ".project/CURRENT.json"
REALITY = ROOT / ".project/current-reality-v3.json"
INDEX = ROOT / ".project/state-index-v12.json"
HANDOFF = ROOT / ".project/handoffs/current-state-v2.md"
RECONCILIATION = ROOT / ".project/reconciliations/post-pr221-canonical-sync-20260729.json"
MAIN = "82191482f48ccb81dc50b5966733a9d8ff7f2953"
PR221_SOURCE = "968402ad52858d837de03e64c36addf372751d28"


class PostPr221CanonicalSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector = json.loads(SELECTOR.read_text(encoding="utf-8"))
        cls.reality = json.loads(REALITY.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))

    def test_selector_preserves_pr221_files_as_historical_lineage(self) -> None:
        self.assertEqual(self.selector["authoritative_current_reality"], ".project/current-reality-v4.json")
        self.assertEqual(self.selector["authoritative_state_index"], ".project/state-index-v13.json")
        self.assertEqual(self.selector["authoritative_handoff"], ".project/handoffs/current-state-v3.md")
        compatibility = {item["path"]: item["status"] for item in self.selector["compatibility_records"]}
        self.assertEqual(compatibility[".project/current-reality-v3.json"], "historical_compatibility_only")
        self.assertEqual(compatibility[".project/state-index-v12.json"], "historical_compatibility_only")
        self.assertEqual(compatibility[".project/handoffs/current-state-v2.md"], "historical_compatibility_only")

    def test_repository_state_advances_through_pr221(self) -> None:
        repo = self.reality["repository_state"]
        self.assertEqual(repo["observed_main"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 221)
        self.assertEqual(repo["latest_merge_commit"], MAIN)
        self.assertEqual(repo["latest_merged_source_head"], PR221_SOURCE)
        self.assertEqual(set(repo["exact_head_ci_runs"]), {"ci", "lab_factory_local_mcp_smoke"})
        self.assertTrue(all(run["conclusion"] == "success" for run in repo["exact_head_ci_runs"].values()))
        self.assertEqual(repo["open_pull_requests_observed"], [])

    def test_local_mcp_receipt_is_promoted_without_cloud_overclaim(self) -> None:
        server = self.reality["domain_state"]["azure_mcp_server"]
        self.assertTrue(server["local_client_call_verified_on_main"])
        self.assertEqual(server["called_tools"], ["list_lab_profiles", "prepare_lab_request", "prepare_lab_request"])
        self.assertFalse(server["get_current_reality_called"])
        self.assertTrue(server["identical_repeat_request_produced_identical_plan"])
        self.assertFalse(server["parameter_values_returned"])
        self.assertFalse(server["azure_queries_performed"])
        self.assertFalse(server["azure_mutations_performed"])
        self.assertFalse(server["deployment_authorized"])
        self.assertFalse(server["cleanup_authorized"])
        self.assertFalse(server["remote_endpoint_deployed"])
        self.assertFalse(server["chatgpt_connection_verified"])
        self.assertFalse(server["azure_openai_mcp_invocation_verified"])

    def test_azure_and_runtime_boundaries_remain_separate(self) -> None:
        domain = self.reality["domain_state"]
        factory = domain["azure_lab_factory_lite"]
        self.assertFalse(factory["arm_what_if_verified"])
        self.assertFalse(factory["azure_deployment_verified"])
        mcp = domain["azure_mcp_current_reality_run1"]
        self.assertEqual(mcp["observed_deployment_count"], 0)
        self.assertTrue(mcp["authorization_consumed"])
        self.assertFalse(mcp["rerun_authorized"])
        runtime = domain["azure_ai_verified_runtime"]
        self.assertEqual(runtime["deployment"], "gpt-5-mini")
        self.assertTrue(runtime["model_response_verified"])
        self.assertFalse(runtime["arm_resource_identity_reconciled"])
        self.assertFalse(runtime["azure_openai_mcp_invocation_verified"])

    def test_state_index_selects_current_files_and_closed_authority(self) -> None:
        self.assertEqual(self.index["schema_version"], "project.state-index.v12")
        self.assertEqual(self.index["authoritative_current_reality"], ".project/current-reality-v3.json")
        self.assertEqual(self.index["authoritative_handoff"], ".project/handoffs/current-state-v2.md")
        self.assertTrue(all(value is None for value in self.index["active_authorizations"].values()))
        self.assertFalse(self.index["consumed_authorities"]["azure_mcp_current_reality_run1_rerun_authorized"])

    def test_handoff_contains_current_and_historical_boundaries(self) -> None:
        self.assertIn(f"observed main: {MAIN}", self.handoff)
        self.assertIn("latest merged PR: #221", self.handoff)
        self.assertIn("repository-only Lab Factory tools called by local client on main: true", self.handoff)
        self.assertIn("get_current_reality called: false", self.handoff)
        self.assertIn("actual Azure cost freshly observed: false", self.handoff)
        self.assertIn("observed main: f8f29d8601666646d354ffc450a85348e891483f", self.handoff)
        self.assertIn("latest merged PR: #212", self.handoff)
        self.assertIn("Draft PR #186", self.handoff)

    def test_authority_is_repository_only_with_explicit_merge(self) -> None:
        authority = self.reconciliation["authority"]
        self.assertTrue(authority["repository_branch_and_declared_writes"])
        self.assertTrue(authority["pull_request_creation"])
        self.assertTrue(authority["ordinary_exact_head_ci"])
        self.assertTrue(authority["merge_after_green_and_freshness_recheck"])
        for key in ("workflow_dispatch_or_rerun", "azure_authentication_or_query", "arm_what_if", "azure_mutation", "rbac_mutation", "model_call", "local_mcp_client_call", "remote_mcp_deployment", "chatgpt_connection", "cleanup", "rollback"):
            self.assertFalse(authority[key], key)


if __name__ == "__main__":
    unittest.main()
