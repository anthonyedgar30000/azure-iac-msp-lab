from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SELECTOR = ROOT / ".project/CURRENT.json"
REALITY = ROOT / ".project/current-reality-v3.json"
INDEX = ROOT / ".project/state-index-v12.json"
HANDOFF = ROOT / ".project/handoffs/current-state-v2.md"
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr220-canonical-sync-20260729.json"
)

MAIN = "8926a5b48db9bb7cb08523d337e43d20ba7ed69d"
PR220_SOURCE = "5d5e8cf2e9022204f3cd032945f777237c9d8f4d"


class PostPr220CanonicalSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector = json.loads(SELECTOR.read_text(encoding="utf-8"))
        cls.reality = json.loads(REALITY.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.reconciliation = json.loads(
            RECONCILIATION.read_text(encoding="utf-8")
        )

    def test_selector_promotes_versioned_authoritative_files(self) -> None:
        self.assertEqual(
            self.selector["authoritative_current_reality"],
            ".project/current-reality-v3.json",
        )
        self.assertEqual(
            self.selector["authoritative_state_index"],
            ".project/state-index-v12.json",
        )
        self.assertEqual(
            self.selector["authoritative_handoff"],
            ".project/handoffs/current-state-v2.md",
        )
        self.assertEqual(
            {item["status"] for item in self.selector["compatibility_records"]},
            {"historical_compatibility_only"},
        )

    def test_repository_state_advances_through_pr220(self) -> None:
        repository = self.reality["repository_state"]
        self.assertEqual(repository["observed_main"], MAIN)
        self.assertEqual(repository["latest_merged_pull_request"], 220)
        self.assertEqual(repository["latest_merge_commit"], MAIN)
        self.assertEqual(repository["latest_merged_source_head"], PR220_SOURCE)
        self.assertEqual(repository["exact_head_ci"]["run_id"], 30504354336)
        self.assertEqual(repository["exact_head_ci"]["conclusion"], "success")
        self.assertEqual(
            repository["merge_commit_pr_triggered_workflows"],
            "not_observed",
        )

    def test_concurrent_pr221_is_preserved_without_promotion(self) -> None:
        candidate = self.reality["repository_state"]["open_pull_requests_observed"][0]
        self.assertEqual(candidate["pull_request"], 221)
        self.assertEqual(candidate["state"], "open_draft")
        self.assertFalse(candidate["changed_paths_overlap_this_increment"])
        self.assertFalse(candidate["terminal_evidence_reconciliation_observed"])
        self.assertFalse(candidate["merged"])
        self.assertFalse(candidate["authority_transferred"])
        self.assertTrue(
            all(
                run["conclusion"] == "success"
                for run in candidate["initial_exact_head_runs"].values()
            )
        )

    def test_domain_state_preserves_cloud_and_mcp_boundaries(self) -> None:
        domain = self.reality["domain_state"]

        factory = domain["azure_lab_factory_lite"]
        self.assertTrue(factory["repository_implementation_merged"])
        self.assertFalse(factory["arm_what_if_verified"])
        self.assertFalse(factory["azure_deployment_verified"])
        self.assertFalse(factory["cleanup_verified"])

        server = domain["azure_mcp_server"]
        self.assertEqual(
            server["tool_inventory"],
            ["get_current_reality", "list_lab_profiles", "prepare_lab_request"],
        )
        self.assertFalse(server["local_client_call_verified_on_main"])
        self.assertFalse(server["concurrent_candidate_terminal_evidence_observed"])
        self.assertFalse(server["remote_endpoint_deployed"])
        self.assertFalse(server["chatgpt_connection_verified"])
        self.assertFalse(server["azure_openai_mcp_invocation_verified"])

        mcp = domain["azure_mcp_current_reality_run1"]
        self.assertEqual(mcp["observed_deployment_count"], 0)
        self.assertTrue(mcp["authorization_consumed"])
        self.assertFalse(mcp["rerun_authorized"])
        self.assertFalse(mcp["azure_mutations_performed"])

        runtime = domain["azure_ai_verified_runtime"]
        self.assertEqual(runtime["deployment"], "gpt-5-mini")
        self.assertTrue(runtime["model_response_verified"])
        self.assertFalse(runtime["arm_resource_identity_reconciled"])
        self.assertFalse(runtime["azure_openai_mcp_invocation_verified"])

    def test_state_index_selects_current_files_and_closed_authority(self) -> None:
        self.assertEqual(self.index["schema_version"], "project.state-index.v12")
        self.assertEqual(
            self.index["authoritative_current_reality"],
            ".project/current-reality-v3.json",
        )
        self.assertEqual(
            self.index["authoritative_handoff"],
            ".project/handoffs/current-state-v2.md",
        )
        self.assertTrue(
            all(value is None for value in self.index["active_authorizations"].values())
        )
        self.assertFalse(
            self.index["consumed_authorities"][
                "azure_mcp_current_reality_run1_rerun_authorized"
            ]
        )

    def test_handoff_contains_current_and_historical_boundaries(self) -> None:
        self.assertIn(f"observed main: {MAIN}", self.handoff)
        self.assertIn("latest merged PR: #220", self.handoff)
        self.assertIn("PR #221 state: open draft", self.handoff)
        self.assertIn("terminal evidence reconciliation observed: false", self.handoff)
        self.assertIn("actual Azure cost freshly observed: false", self.handoff)
        self.assertIn(
            "observed main: f8f29d8601666646d354ffc450a85348e891483f",
            self.handoff,
        )
        self.assertIn("latest merged PR: #212", self.handoff)
        self.assertIn("Draft PR #186", self.handoff)

    def test_authority_is_repository_only_with_explicit_merge(self) -> None:
        authority = self.reconciliation["authority"]
        self.assertTrue(authority["repository_branch_and_declared_writes"])
        self.assertTrue(authority["pull_request_creation"])
        self.assertTrue(authority["ordinary_exact_head_ci"])
        self.assertTrue(authority["merge_after_green_and_freshness_recheck"])
        for key in (
            "workflow_dispatch_or_rerun",
            "azure_authentication_or_query",
            "arm_what_if",
            "azure_mutation",
            "rbac_mutation",
            "model_call",
            "local_mcp_client_call",
            "remote_mcp_deployment",
            "chatgpt_connection",
            "cleanup",
            "rollback",
        ):
            self.assertFalse(authority[key], key)


if __name__ == "__main__":
    unittest.main()
