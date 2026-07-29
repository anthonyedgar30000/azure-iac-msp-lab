from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / ".project/state-index.json"
CURRENT = ROOT / ".project/current-reality-v2.json"
LEGACY = ROOT / ".project/current-reality.json"
GATE = ROOT / ".project/lab-v1-completion-gate-v2.json"
HANDOFF = ROOT / ".project/handoffs/current-state.md"
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "correlation-identity-run1-terminal-20260727.json"
)
POST_CONTAINMENT_RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr182-containment-20260727.json"
)
POST_PR183_RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr183-repository-watermark-20260728.json"
)
POST_PR185_RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr185-repository-watermark-20260728.json"
)
DESIGN = (
    ROOT
    / ".project"
    / "designs"
    / "durable-single-use-authorization-ledger-v1.md"
)
REQUEST = (
    ROOT
    / ".project"
    / "deployment-requests"
    / "correlation-identity-run1.json"
)

MAIN = "ca994ce53642587bea370bee1c5a0633faaaece8"
CONTAINMENT_MAIN = "516cc45972725f494815449f55f02f96727afbde"
PR183_MAIN = "db74fc764f93a972344dae35ed906e8128f51eb8"
PR183_SOURCE = "52ab387418e77aed0cd23a2d827b359a8ae0ac40"
PR184_MAIN = "b92e9e0d6c4c2bcb8d4b7628eb21fb342a19f686"
PR185_SOURCE = "36bbd5ab1ef3c579c43ad2df589f44362feced37"
DEPLOYED_SOURCE = "0b6b5322f25b3d0289f6c0febdcfd800ea4b909a"
PREFLIGHT_PATH = (
    ".project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json"
)
RECONCILIATION_PATH = (
    ".project/reconciliations/correlation-identity-run1-terminal-20260727.json"
)
AZURE_MCP_RUN1_TERMINAL_PATH = (
    ".project/reconciliations/azure-mcp-read-only-preflight-run1-terminal-20260729.json"
)
POST_CONTAINMENT_PATH = (
    ".project/reconciliations/post-pr182-containment-20260727.json"
)
POST_PR183_PATH = (
    ".project/reconciliations/post-pr183-repository-watermark-20260728.json"
)
POST_PR185_PATH = (
    ".project/reconciliations/post-pr185-repository-watermark-20260728.json"
)
DESIGN_PATH = ".project/designs/durable-single-use-authorization-ledger-v1.md"
HISTORICAL_CONSUMED_PATH = (
    ".project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json"
)
REQUEST_PATH = ".project/deployment-requests/correlation-identity-run1.json"


class CanonicalStateIndexV6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.current = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
        cls.gate = json.loads(GATE.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.post_containment = json.loads(
            POST_CONTAINMENT_RECONCILIATION.read_text(encoding="utf-8")
        )
        cls.post_pr183 = json.loads(
            POST_PR183_RECONCILIATION.read_text(encoding="utf-8")
        )
        cls.post_pr185 = json.loads(
            POST_PR185_RECONCILIATION.read_text(encoding="utf-8")
        )
        cls.design = DESIGN.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))

    def test_index_preserves_terminal_containment_and_repository_evidence(self) -> None:
        self.assertEqual(
            self.index["canonical_current_reality"],
            ".project/current-reality-v2.json",
        )
        self.assertEqual(self.index["latest_verified_reconciliation"], PREFLIGHT_PATH)
        self.assertEqual(
            self.index["latest_terminal_reconciliation"],
            AZURE_MCP_RUN1_TERMINAL_PATH,
        )
        self.assertEqual(
            self.index["latest_deployment_reconciliation"], RECONCILIATION_PATH
        )
        self.assertEqual(
            self.index["latest_authorization_resolution"],
            AZURE_MCP_RUN1_TERMINAL_PATH,
        )
        self.assertEqual(self.index["latest_control_incident"], RECONCILIATION_PATH)
        self.assertEqual(
            self.index["latest_repository_reconciliation"],
            AZURE_MCP_RUN1_TERMINAL_PATH,
        )
        self.assertEqual(
            self.index["latest_repository_watermark_reconciliation"],
            AZURE_MCP_RUN1_TERMINAL_PATH,
        )
        self.assertEqual(
            self.index["latest_lifecycle_reconciliation"],
            AZURE_MCP_RUN1_TERMINAL_PATH,
        )
        self.assertEqual(
            self.index["previous_repository_reconciliation"], POST_PR185_PATH
        )
        self.assertEqual(
            self.index["current_containment_reconciliation"],
            POST_CONTAINMENT_PATH,
        )
        self.assertEqual(self.index["replacement_authorization_design"], DESIGN_PATH)
        self.assertIsNone(self.index["active_deployment_authorization"])
        self.assertEqual(
            self.index["consumed_deployment_authorization"],
            HISTORICAL_CONSUMED_PATH,
        )
        self.assertEqual(
            self.index["latest_consumed_deployment_authorization"], REQUEST_PATH
        )
        self.assertFalse(
            self.index["legacy_compatibility_snapshots"][0][
                "authoritative_for_current_operations"
            ]
        )
        self.assertEqual(
            self.legacy["repository_state"]["observed_head"],
            "665e051375594d11e58e434231bd06775dbdc560",
        )

    def test_current_repository_and_source_watermarks_are_explicit(self) -> None:
        repo = self.current["repository_state"]
        self.assertEqual(repo["observed_main"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 185)
        self.assertEqual(repo["latest_merged_source_head"], PR185_SOURCE)
        self.assertEqual(repo["latest_exact_head_ci_run"], 30359529916)
        self.assertEqual(repo["repository_watermark_pull_request_184"], "merged")
        self.assertEqual(repo["repository_watermark_merge_commit"], PR184_MAIN)
        self.assertEqual(repo["frontend_architecture_pull_request_185"], "merged")
        self.assertEqual(repo["frontend_architecture_merge_commit"], MAIN)
        self.assertEqual(repo["trigger_pull_request_181"], "closed_without_merge")
        self.assertEqual(
            repo["open_pull_requests_after_frontend_architecture_merge"], [186]
        )
        candidate = repo["open_pull_request_186"]
        self.assertEqual(candidate["state"], "open_draft")
        self.assertEqual(candidate["head_sha"], "138659609b15ef80f6cce12d916e26382ab71205")
        self.assertEqual(candidate["exact_head_ci_run"], 30389249099)
        self.assertFalse(candidate["merged"])
        self.assertEqual(repo["merge_commit_pr_triggered_ci"], "not_observed")
        self.assertEqual(
            self.current["source_lineage"]["reviewed_source"], DEPLOYED_SOURCE
        )
        self.assertFalse(
            self.current["source_lineage"]["current_main_equals_deployed_source"]
        )

    def test_frontend_implementation_is_not_collapsed_into_publication_truth(self) -> None:
        frontend = self.current["frontend_state"]
        self.assertEqual(frontend["exact_tested_source_head"], PR185_SOURCE)
        self.assertEqual(frontend["exact_head_ci_run"], 30359529916)
        self.assertEqual(frontend["exact_head_ci_conclusion"], "success")
        self.assertFalse(frontend["github_pages_publication_freshly_observed"])
        self.assertFalse(frontend["browser_render_freshly_verified"])
        self.assertFalse(frontend["azure_collector_runtime_change_claimed"])
        self.assertIn(
            "main_contains_frontend_implementation != GitHub_Pages_publication_observed",
            self.current["canonical_distinctions"],
        )
        self.assertIn(
            "architecture_explained != runtime_proof_manufactured",
            self.current["canonical_distinctions"],
        )

    def test_authority_consumption_and_replay_are_not_collapsed(self) -> None:
        authority = self.current["authorization_state"]
        self.assertEqual(
            authority["status"], "consumed_with_unauthorized_replay_observed"
        )
        self.assertEqual(authority["attempt_limit"], 1)
        self.assertEqual(authority["attempts_observed"], 2)
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["rollback_authorized"])

        first, second = self.current["deployment_attempts"]
        self.assertEqual(first["authority"], "authorized_consuming_attempt")
        self.assertEqual(first["deployment_run"], 30310439500)
        self.assertEqual(second["authority"], "unauthorized_replay_after_consumption")
        self.assertEqual(second["deployment_run"], 30315658677)
        for attempt in (first, second):
            self.assertEqual(attempt["arm_parent"], "Succeeded")
            self.assertEqual(attempt["vm_extension"], "Succeeded")

    def test_runtime_truth_remains_separate_from_workflow_authority_and_repo(self) -> None:
        runtime = self.current["runtime_state"]
        self.assertEqual(runtime["status"], "healthy")
        self.assertEqual(runtime["deployed_source"], DEPLOYED_SOURCE)
        self.assertTrue(runtime["azure_host_identity_verified"])
        self.assertTrue(runtime["request_header_body_identity_verified"])
        self.assertEqual(runtime["transactions_verified"], 20)
        self.assertFalse(runtime["exact_root_cause_claimed"])
        self.assertFalse(runtime["browser_dom_refresh_verified"])
        self.assertFalse(runtime["freshly_observed_during_repository_reconciliation"])
        self.assertFalse(self.current["azure_state"]["fresh_live_query_during_reconciliation"])

        attempts = self.reconciliation["attempts"]
        self.assertEqual(attempts[0]["workflow_conclusion"], "failure")
        self.assertEqual(attempts[0]["azure_result"]["arm_parent"], "Succeeded")
        self.assertFalse(attempts[1]["authority_valid"])

    def test_gate_tracks_frontend_evidence_and_remaining_operational_work(self) -> None:
        criteria = {item["criterion_id"]: item for item in self.gate["p0"]["criteria"]}
        self.assertTrue(criteria["p0-collector-deployment"]["complete"])
        self.assertTrue(criteria["p0-runtime-contract"]["complete"])
        self.assertTrue(criteria["p0-servicetracer-scenario"]["complete"])
        self.assertFalse(criteria["p0-source-and-cost-decision"]["complete"])
        self.assertFalse(criteria["p0-browser-demonstration"]["complete"])
        self.assertFalse(criteria["p0-evidence-lock"]["complete"])
        self.assertIn(
            "authorization replay incident",
            " ".join(self.gate["p2"]["required_story"]),
        )
        self.assertIn(
            "verified frontend architecture explainer",
            self.gate["p2"]["required_story"],
        )
        evidence = self.gate["evidence_inputs"]
        self.assertEqual(evidence["observed_main"], MAIN)
        self.assertEqual(evidence["latest_merged_pull_request"], 185)
        self.assertEqual(evidence["latest_merged_source_head"], PR185_SOURCE)
        self.assertEqual(evidence["post_pr185_repository_reconciliation"], POST_PR185_PATH)
        self.assertEqual(evidence["open_authorization_ledger_candidate_pull_request"], 186)
        self.assertEqual(evidence["open_authorization_ledger_candidate_ci_run"], 30389249099)

    def test_containment_is_merged_fail_closed_and_cloud_authority_is_absent(self) -> None:
        containment = self.current["control_incident"]["containment"]
        self.assertTrue(containment["collector_workflow_quarantined"])
        self.assertEqual(containment["collector_workflow_state"], "quarantined_on_main")
        self.assertFalse(containment["collector_workflow_oidc_permission"])
        self.assertFalse(containment["collector_workflow_azure_commands"])
        self.assertTrue(containment["one_shot_dispatcher_retired"])
        self.assertTrue(containment["trigger_pr_closed_without_merge"])
        self.assertEqual(containment["containment_pull_request_state"], "merged")
        self.assertTrue(containment["static_replay_boundary_verified"])

        authority = self.current["authority"]
        self.assertTrue(authority["pull_request_creation_authorized"])
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_or_rerun_authorized",
            "azure_authentication_authorized",
            "azure_query_authorized",
            "azure_mutation_authorized",
            "rollback_authorized",
            "cleanup_authorized",
            "rbac_mutation_authorized",
        ):
            self.assertFalse(authority[key], key)

        self.assertEqual(
            self.request["status"], "consumed_with_unauthorized_replay_observed"
        )
        self.assertFalse(self.request["active"])
        self.assertEqual(
            self.reconciliation["root_cause"]["canonical_rule_violated"],
            "Authorization Consumption Principle",
        )
        self.assertIn("workflow dispatch or rerun: unauthorized", self.handoff)

    def test_repository_reconciliations_preserve_their_time_boundaries(self) -> None:
        self.assertEqual(
            self.post_containment["github_state"]["observed_main"], CONTAINMENT_MAIN
        )
        self.assertEqual(
            self.post_containment["github_state"]["latest_merged_pull_request"], 182
        )
        self.assertTrue(
            self.post_containment["containment_static_proof"][
                "workflow_quarantined_on_main"
            ]
        )
        self.assertFalse(
            self.post_containment["containment_static_proof"]["id_token_write_present"]
        )
        self.assertFalse(
            self.post_containment["containment_static_proof"][
                "azure_cli_commands_present"
            ]
        )

        github183 = self.post_pr183["github_state"]
        self.assertEqual(github183["observed_main"], PR183_MAIN)
        self.assertEqual(github183["latest_merged_pull_request"], 183)
        self.assertEqual(github183["latest_merged_source_head"], PR183_SOURCE)
        self.assertEqual(github183["open_pull_requests_observed"], [])
        self.assertEqual(github183["merge_commit_pr_triggered_ci"], "not_observed")
        self.assertFalse(self.post_pr183["azure_boundary"]["fresh_live_query_performed"])
        self.assertFalse(self.post_pr183["next_gate"]["workflow_restoration_allowed"])

        github185 = self.post_pr185["github_state"]
        self.assertEqual(github185["observed_main"], MAIN)
        self.assertEqual(github185["latest_merged_pull_request"], 185)
        self.assertEqual(github185["latest_merged_source_head"], PR185_SOURCE)
        self.assertEqual(github185["open_pull_requests_observed"], [186])
        self.assertEqual(github185["merge_commit_pr_triggered_ci"], "not_observed")
        self.assertFalse(self.post_pr185["azure_boundary"]["fresh_live_query_performed"])
        self.assertFalse(
            self.post_pr185["frontend_boundary"][
                "github_pages_publication_freshly_observed"
            ]
        )
        self.assertFalse(self.post_pr185["next_gate"]["workflow_restoration_allowed"])
        self.assertFalse(self.post_pr185["next_gate"]["merge_allowed"])
        concurrent = self.post_pr185["concurrent_open_pull_requests"][0]
        self.assertEqual(concurrent["pull_request"], 186)
        self.assertEqual(concurrent["state"], "open_draft")
        self.assertFalse(concurrent["merged"])
        self.assertFalse(concurrent["activation_claimed"])

    def test_design_remains_proposed_and_not_cloud_authority(self) -> None:
        self.assertIn("claim-authority job", self.design)
        self.assertIn("refs/tags/authority-consumed/<request_id>", self.design)
        self.assertIn("exactly one successful claimant", self.design)
        self.assertIn("Proposed, not implemented", self.design)


if __name__ == "__main__":
    unittest.main()
