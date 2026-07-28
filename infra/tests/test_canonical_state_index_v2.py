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
TERMINAL = (
    ROOT
    / ".project"
    / "reconciliations"
    / "correlation-identity-run1-terminal-20260727.json"
)
POST_CONTAINMENT = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr182-containment-20260727.json"
)
POST_PR183 = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr183-repository-watermark-20260728.json"
)
POST_PR185 = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr185-repository-watermark-20260728.json"
)
POST_PR187 = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr187-repository-watermark-20260728.json"
)
DESIGN = ROOT / ".project/designs/durable-single-use-authorization-ledger-v1.md"
CONTRACT = ROOT / ".project/contracts/durable-single-use-authorization-ledger-v1.json"
REQUEST = ROOT / ".project/deployment-requests/correlation-identity-run1.json"

MAIN = "07f32b59eda11b5a3627d398f1ffca00c8c88e69"
PR187_SOURCE = "44bc3ab202c2e3d709aa2d9906ef9aba365acfb2"
PR186_SOURCE = "138659609b15ef80f6cce12d916e26382ab71205"
PR186_MERGE = "30e312ef5122831a8233835db2f541437a97b125"
PR185_MAIN = "ca994ce53642587bea370bee1c5a0633faaaece8"
PR185_SOURCE = "36bbd5ab1ef3c579c43ad2df589f44362feced37"
PR183_MAIN = "db74fc764f93a972344dae35ed906e8128f51eb8"
PR183_SOURCE = "52ab387418e77aed0cd23a2d827b359a8ae0ac40"
CONTAINMENT_MAIN = "516cc45972725f494815449f55f02f96727afbde"
DEPLOYED_SOURCE = "0b6b5322f25b3d0289f6c0febdcfd800ea4b909a"

PREFLIGHT_PATH = (
    ".project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json"
)
TERMINAL_PATH = ".project/reconciliations/correlation-identity-run1-terminal-20260727.json"
POST_CONTAINMENT_PATH = ".project/reconciliations/post-pr182-containment-20260727.json"
POST_PR185_PATH = ".project/reconciliations/post-pr185-repository-watermark-20260728.json"
POST_PR187_PATH = ".project/reconciliations/post-pr187-repository-watermark-20260728.json"
DESIGN_PATH = ".project/designs/durable-single-use-authorization-ledger-v1.md"
CONTRACT_PATH = ".project/contracts/durable-single-use-authorization-ledger-v1.json"
REQUEST_PATH = ".project/deployment-requests/correlation-identity-run1.json"
HISTORICAL_CONSUMED_PATH = (
    ".project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json"
)


class CanonicalStateIndexV7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.current = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
        cls.gate = json.loads(GATE.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.terminal = json.loads(TERMINAL.read_text(encoding="utf-8"))
        cls.post_containment = json.loads(POST_CONTAINMENT.read_text(encoding="utf-8"))
        cls.post_pr183 = json.loads(POST_PR183.read_text(encoding="utf-8"))
        cls.post_pr185 = json.loads(POST_PR185.read_text(encoding="utf-8"))
        cls.post_pr187 = json.loads(POST_PR187.read_text(encoding="utf-8"))
        cls.design = DESIGN.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))

    def test_index_selects_latest_terminal_and_repository_evidence(self) -> None:
        self.assertEqual(self.index["canonical_current_reality"], ".project/current-reality-v2.json")
        self.assertEqual(self.index["latest_verified_reconciliation"], PREFLIGHT_PATH)
        self.assertEqual(self.index["latest_terminal_reconciliation"], TERMINAL_PATH)
        self.assertEqual(self.index["latest_deployment_reconciliation"], TERMINAL_PATH)
        self.assertEqual(self.index["latest_authorization_resolution"], TERMINAL_PATH)
        self.assertEqual(self.index["latest_control_incident"], TERMINAL_PATH)
        self.assertEqual(self.index["latest_repository_reconciliation"], POST_PR187_PATH)
        self.assertEqual(
            self.index["latest_repository_watermark_reconciliation"],
            POST_PR187_PATH,
        )
        self.assertEqual(self.index["previous_repository_reconciliation"], POST_PR185_PATH)
        self.assertEqual(
            self.index["current_containment_reconciliation"],
            POST_CONTAINMENT_PATH,
        )
        self.assertEqual(self.index["replacement_authorization_design"], DESIGN_PATH)
        self.assertEqual(self.index["replacement_authorization_contract"], CONTRACT_PATH)
        self.assertIsNone(self.index["active_deployment_authorization"])
        self.assertEqual(
            self.index["consumed_deployment_authorization"],
            HISTORICAL_CONSUMED_PATH,
        )
        self.assertEqual(
            self.index["latest_consumed_deployment_authorization"],
            REQUEST_PATH,
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

    def test_current_repository_watermark_matches_live_merge_state(self) -> None:
        repo = self.current["repository_state"]
        self.assertEqual(repo["observed_main"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 187)
        self.assertEqual(repo["latest_merged_source_head"], PR187_SOURCE)
        self.assertEqual(repo["latest_exact_head_ci_run"], 30390614963)
        self.assertEqual(repo["latest_exact_head_ci_conclusion"], "success")
        self.assertEqual(repo["authorization_implementation_pull_request_186"], "merged")
        self.assertEqual(repo["authorization_implementation_merge_commit"], PR186_MERGE)
        self.assertEqual(repo["repository_reconciliation_pull_request_187"], "merged")
        self.assertEqual(repo["repository_reconciliation_merge_commit"], MAIN)
        self.assertEqual(repo["integrated_main_ci"], "not_observed")
        self.assertEqual(repo["open_pull_requests_after_repository_reconciliation"], [])
        implementation = repo["authorization_implementation"]
        self.assertEqual(implementation["state"], "merged")
        self.assertEqual(implementation["head_sha"], PR186_SOURCE)
        self.assertEqual(implementation["merge_commit"], PR186_MERGE)
        self.assertEqual(implementation["exact_head_ci_run"], 30389249099)
        self.assertTrue(implementation["merged"])
        self.assertFalse(implementation["activated"])
        self.assertIn(
            "PR_exact_head_CI_success != integrated_main_CI_observed",
            self.current["canonical_distinctions"],
        )

    def test_merged_authorization_implementation_is_not_promoted_as_activated(self) -> None:
        controls = self.current["operational_controls"]
        self.assertEqual(
            controls["replacement_authorization_design_status"],
            "implemented_on_main_not_activated",
        )
        ledger = controls["authorization_ledger"]
        self.assertEqual(ledger["state"], "merged_not_activated")
        self.assertTrue(ledger["merged_to_main"])
        self.assertFalse(ledger["ruleset_configured"])
        self.assertFalse(ledger["ruleset_independently_inspected"])
        self.assertFalse(ledger["live_claim_performed"])
        self.assertFalse(ledger["concurrent_claim_verified"])
        self.assertFalse(ledger["collector_workflow_restored"])
        self.assertFalse(ledger["azure_execution_enabled"])
        self.assertFalse(ledger["operationally_verified"])

        self.assertEqual(self.contract["status"], "implementation_merged_not_activated")
        self.assertTrue(self.contract["activation"]["merged_to_main"])
        self.assertFalse(self.contract["activation"]["ruleset_configured"])
        self.assertFalse(self.contract["activation"]["live_claim_test_performed"])
        self.assertFalse(
            self.contract["activation"]["concurrent_claim_test_performed"]
        )
        self.assertEqual(self.contract["merge"]["pull_request"], 186)
        self.assertEqual(self.contract["merge"]["merge_commit"], PR186_MERGE)
        self.assertIn("merged, not activated", self.design.lower())
        self.assertIn("Proposed, not implemented", self.design)
        self.assertIn("claim-authority job", self.design)
        self.assertIn("refs/tags/authority-consumed/<request_id>", self.design)
        self.assertIn("exactly one successful claimant", self.design)

    def test_frontend_implementation_is_not_collapsed_into_publication_truth(self) -> None:
        frontend = self.current["frontend_state"]
        self.assertEqual(frontend["exact_tested_source_head"], PR185_SOURCE)
        self.assertEqual(frontend["exact_head_ci_run"], 30359529916)
        self.assertEqual(frontend["exact_head_ci_conclusion"], "success")
        self.assertFalse(frontend["github_pages_publication_freshly_observed"])
        self.assertFalse(frontend["browser_render_freshly_verified"])
        self.assertFalse(frontend["azure_collector_runtime_change_claimed"])

    def test_authority_consumption_runtime_and_workflow_truth_remain_separate(self) -> None:
        authority = self.current["authorization_state"]
        self.assertEqual(
            authority["status"],
            "consumed_with_unauthorized_replay_observed",
        )
        self.assertEqual(authority["attempt_limit"], 1)
        self.assertEqual(authority["attempts_observed"], 2)
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["rollback_authorized"])

        first, second = self.current["deployment_attempts"]
        self.assertEqual(first["authority"], "authorized_consuming_attempt")
        self.assertEqual(second["authority"], "unauthorized_replay_after_consumption")
        for attempt in (first, second):
            self.assertEqual(attempt["arm_parent"], "Succeeded")
            self.assertEqual(attempt["vm_extension"], "Succeeded")

        runtime = self.current["runtime_state"]
        self.assertEqual(runtime["status"], "healthy")
        self.assertEqual(runtime["deployed_source"], DEPLOYED_SOURCE)
        self.assertTrue(runtime["azure_host_identity_verified"])
        self.assertTrue(runtime["request_header_body_identity_verified"])
        self.assertEqual(runtime["transactions_verified"], 20)
        self.assertFalse(runtime["exact_root_cause_claimed"])
        self.assertFalse(runtime["browser_dom_refresh_verified"])
        self.assertFalse(runtime["freshly_observed_during_repository_reconciliation"])
        self.assertFalse(
            self.current["azure_state"]["fresh_live_query_during_reconciliation"]
        )

    def test_gate_tracks_merged_implementation_and_remaining_operational_work(self) -> None:
        criteria = {item["criterion_id"]: item for item in self.gate["p0"]["criteria"]}
        self.assertTrue(criteria["p0-collector-deployment"]["complete"])
        self.assertTrue(criteria["p0-runtime-contract"]["complete"])
        self.assertTrue(criteria["p0-servicetracer-scenario"]["complete"])
        self.assertFalse(criteria["p0-source-and-cost-decision"]["complete"])
        self.assertFalse(criteria["p0-browser-demonstration"]["complete"])
        self.assertFalse(criteria["p0-evidence-lock"]["complete"])

        evidence = self.gate["evidence_inputs"]
        self.assertEqual(evidence["observed_main"], MAIN)
        self.assertEqual(evidence["latest_merged_pull_request"], 187)
        self.assertEqual(evidence["latest_merged_source_head"], PR187_SOURCE)
        self.assertEqual(evidence["post_pr187_repository_reconciliation"], POST_PR187_PATH)
        self.assertEqual(evidence["authorization_implementation_pull_request"], 186)
        self.assertEqual(evidence["authorization_implementation_head"], PR186_SOURCE)
        self.assertEqual(
            evidence["authorization_implementation_merge_commit"],
            PR186_MERGE,
        )
        self.assertFalse(evidence["authorization_implementation_activated"])
        self.assertEqual(evidence["integrated_main_ci"], "not_observed")

    def test_containment_and_current_authority_remain_fail_closed(self) -> None:
        containment = self.current["control_incident"]["containment"]
        self.assertTrue(containment["collector_workflow_quarantined"])
        self.assertEqual(containment["collector_workflow_state"], "quarantined_on_main")
        self.assertFalse(containment["collector_workflow_oidc_permission"])
        self.assertFalse(containment["collector_workflow_azure_commands"])
        self.assertTrue(containment["one_shot_dispatcher_retired"])
        self.assertTrue(containment["trigger_pr_closed_without_merge"])
        self.assertEqual(containment["containment_pull_request_state"], "merged")
        self.assertTrue(containment["static_replay_boundary_verified"])

        current_authority = self.current["authority"]
        self.assertTrue(current_authority["pull_request_creation_authorized"])
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_or_rerun_authorized",
            "repository_ruleset_mutation_authorized",
            "authorization_tag_claim_authorized",
            "azure_authentication_authorized",
            "azure_query_authorized",
            "azure_mutation_authorized",
            "rollback_authorized",
            "cleanup_authorized",
            "rbac_mutation_authorized",
        ):
            self.assertFalse(current_authority[key], key)

        self.assertEqual(
            self.request["status"],
            "consumed_with_unauthorized_replay_observed",
        )
        self.assertFalse(self.request["active"])
        self.assertEqual(
            self.terminal["root_cause"]["canonical_rule_violated"],
            "Authorization Consumption Principle",
        )
        self.assertIn("workflow dispatch or rerun: unauthorized", self.handoff)
        self.assertIn("repository ruleset mutation: unauthorized", self.handoff)
        self.assertIn("authorization tag claim execution: unauthorized", self.handoff)

    def test_repository_reconciliations_preserve_time_bounded_truth(self) -> None:
        self.assertEqual(
            self.post_containment["github_state"]["observed_main"],
            CONTAINMENT_MAIN,
        )
        self.assertEqual(
            self.post_containment["github_state"]["latest_merged_pull_request"],
            182,
        )
        self.assertTrue(
            self.post_containment["containment_static_proof"][
                "workflow_quarantined_on_main"
            ]
        )
        self.assertFalse(
            self.post_containment["containment_static_proof"]["id_token_write_present"]
        )

        github183 = self.post_pr183["github_state"]
        self.assertEqual(github183["observed_main"], PR183_MAIN)
        self.assertEqual(github183["latest_merged_pull_request"], 183)
        self.assertEqual(github183["latest_merged_source_head"], PR183_SOURCE)
        self.assertEqual(github183["open_pull_requests_observed"], [])

        github185 = self.post_pr185["github_state"]
        self.assertEqual(github185["observed_main"], PR185_MAIN)
        self.assertEqual(github185["latest_merged_pull_request"], 185)
        self.assertEqual(github185["latest_merged_source_head"], PR185_SOURCE)
        self.assertEqual(github185["open_pull_requests_observed"], [186])
        concurrent = self.post_pr185["concurrent_open_pull_requests"][0]
        self.assertEqual(concurrent["pull_request"], 186)
        self.assertEqual(concurrent["state"], "open_draft")
        self.assertFalse(concurrent["merged"])
        self.assertFalse(concurrent["activation_claimed"])

        github187 = self.post_pr187["github_state"]
        self.assertEqual(github187["observed_main"], MAIN)
        self.assertEqual(github187["latest_merged_pull_request"], 187)
        self.assertEqual(github187["latest_merged_source_head"], PR187_SOURCE)
        self.assertEqual(github187["open_pull_requests_observed"], [])
        self.assertEqual(github187["integrated_main_ci"], "not_observed")
        self.assertTrue(
            self.post_pr187["authorization_control_boundary"][
                "implementation_merged_to_main"
            ]
        )
        self.assertFalse(
            self.post_pr187["authorization_control_boundary"]["ruleset_configured"]
        )
        self.assertFalse(
            self.post_pr187["authorization_control_boundary"][
                "concurrent_exactly_one_claimant_verified"
            ]
        )
        self.assertFalse(self.post_pr187["azure_boundary"]["fresh_live_query_performed"])
        self.assertFalse(self.post_pr187["next_gate"]["merge_allowed"])
        self.assertFalse(self.post_pr187["next_gate"]["workflow_restoration_allowed"])


if __name__ == "__main__":
    unittest.main()
