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

MAIN = "516cc45972725f494815449f55f02f96727afbde"
DEPLOYED_SOURCE = "0b6b5322f25b3d0289f6c0febdcfd800ea4b909a"
PREFLIGHT_PATH = (
    ".project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json"
)
RECONCILIATION_PATH = (
    ".project/reconciliations/correlation-identity-run1-terminal-20260727.json"
)
POST_CONTAINMENT_PATH = (
    ".project/reconciliations/post-pr182-containment-20260727.json"
)
DESIGN_PATH = (
    ".project/designs/durable-single-use-authorization-ledger-v1.md"
)
HISTORICAL_CONSUMED_PATH = (
    ".project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json"
)
REQUEST_PATH = ".project/deployment-requests/correlation-identity-run1.json"


class CanonicalStateIndexV4Tests(unittest.TestCase):
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
        cls.design = DESIGN.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))

    def test_index_preserves_terminal_evidence_and_selects_post_merge_state(self) -> None:
        self.assertEqual(
            self.index["canonical_current_reality"],
            ".project/current-reality-v2.json",
        )
        self.assertEqual(self.index["latest_verified_reconciliation"], PREFLIGHT_PATH)
        self.assertEqual(
            self.index["latest_terminal_reconciliation"], RECONCILIATION_PATH
        )
        self.assertEqual(
            self.index["latest_deployment_reconciliation"], RECONCILIATION_PATH
        )
        self.assertEqual(
            self.index["latest_authorization_resolution"], RECONCILIATION_PATH
        )
        self.assertEqual(self.index["latest_control_incident"], RECONCILIATION_PATH)
        self.assertEqual(
            self.index["latest_repository_reconciliation"], POST_CONTAINMENT_PATH
        )
        self.assertEqual(
            self.index["current_containment_reconciliation"], POST_CONTAINMENT_PATH
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
        self.assertEqual(repo["latest_merged_pull_request"], 182)
        self.assertEqual(repo["containment_pull_request_182"], "merged")
        self.assertEqual(repo["trigger_pull_request_181"], "closed_without_merge")
        self.assertEqual(repo["open_pull_requests_after_containment_merge"], [])
        self.assertEqual(
            self.current["source_lineage"]["reviewed_source"], DEPLOYED_SOURCE
        )
        self.assertFalse(
            self.current["source_lineage"]["current_main_equals_deployed_source"]
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

    def test_runtime_truth_remains_separate_from_workflow_and_authority(self) -> None:
        runtime = self.current["runtime_state"]
        self.assertEqual(runtime["status"], "healthy")
        self.assertEqual(runtime["deployed_source"], DEPLOYED_SOURCE)
        self.assertTrue(runtime["azure_host_identity_verified"])
        self.assertTrue(runtime["request_header_body_identity_verified"])
        self.assertEqual(runtime["transactions_verified"], 20)
        self.assertFalse(runtime["exact_root_cause_claimed"])
        self.assertFalse(runtime["browser_dom_refresh_verified"])
        self.assertFalse(self.current["azure_state"]["fresh_live_query_during_reconciliation"])

        attempts = self.reconciliation["attempts"]
        self.assertEqual(attempts[0]["workflow_conclusion"], "failure")
        self.assertEqual(attempts[0]["azure_result"]["arm_parent"], "Succeeded")
        self.assertFalse(attempts[1]["authority_valid"])

    def test_gate_tracks_completed_runtime_and_remaining_operational_work(self) -> None:
        criteria = {item["criterion_id"]: item for item in self.gate["p0"]["criteria"]}
        self.assertTrue(criteria["p0-collector-deployment"]["complete"])
        self.assertTrue(criteria["p0-runtime-contract"]["complete"])
        self.assertTrue(criteria["p0-servicetracer-scenario"]["complete"])
        self.assertFalse(criteria["p0-source-and-cost-decision"]["complete"])
        self.assertFalse(criteria["p0-browser-demonstration"]["complete"])
        self.assertFalse(criteria["p0-evidence-lock"]["complete"])
        self.assertIn("authorization replay incident", " ".join(self.gate["p2"]["required_story"]))

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
        for key in (
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

    def test_post_containment_reconciliation_and_design_preserve_restoration_gate(self) -> None:
        self.assertEqual(self.post_containment["github_state"]["observed_main"], MAIN)
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
        self.assertFalse(
            self.post_containment["next_gate"]["workflow_restoration_allowed"]
        )
        self.assertIn("claim-authority job", self.design)
        self.assertIn("refs/tags/authority-consumed/<request_id>", self.design)
        self.assertIn("exactly one successful claimant", self.design)
        self.assertIn("Proposed, not implemented", self.design)


if __name__ == "__main__":
    unittest.main()
