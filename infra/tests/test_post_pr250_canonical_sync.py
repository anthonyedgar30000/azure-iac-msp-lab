from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SELECTOR = ROOT / ".project/CURRENT.json"
REALITY = ROOT / ".project/current-reality-v4.json"
INDEX = ROOT / ".project/state-index-v13.json"
HANDOFF = ROOT / ".project/handoffs/current-state-v3.md"
SYNC = ROOT / ".project/reconciliations/post-pr250-canonical-sync-20260730.json"
RUN8_RECON = ROOT / ".project/reconciliations/azure-ai-go-live-run8-terminal-20260730.json"
RUN8_EVIDENCE = ROOT / ".project/evidence/azure-ai-go-live-run8-terminal-summary.json"
RUN8_MANIFEST = ROOT / ".project/evidence/azure-ai-go-live-run8-terminal-summary.sha256"
RUN8_REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run8.json"
PLAN_REQUEST = ROOT / ".project/deployment-requests/servicetracer-demo-api-plan-run1.json"

MAIN = "feae9da6427c2205f86185e729dc88f820cd67e7"
PR250_SOURCE = "8530fab6dcf9e9aaad25f7d44e773da786de5a13"
RUN8_COMMIT = "798486cb9e7c20fcf7fe508314317605dd4100ba"
RUN8_ARTIFACT_DIGEST = "sha256:e05dccbc1618e052f905f12f03d3576a05357bdf6c298d380a140f3ecef25f51"
EVIDENCE_SHA = "572489ee1380b239b4cd229ad1d99ef8aeb2e9831ee46366ed0b4664d4e417b7"


class PostPr250CanonicalSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector = json.loads(SELECTOR.read_text(encoding="utf-8"))
        cls.reality = json.loads(REALITY.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.sync = json.loads(SYNC.read_text(encoding="utf-8"))
        cls.run8 = json.loads(RUN8_RECON.read_text(encoding="utf-8"))
        cls.run8_evidence = json.loads(RUN8_EVIDENCE.read_text(encoding="utf-8"))
        cls.run8_request = json.loads(RUN8_REQUEST.read_text(encoding="utf-8"))
        cls.plan_request = json.loads(PLAN_REQUEST.read_text(encoding="utf-8"))

    def test_selector_promotes_versioned_state_and_clears_pending_run8(self) -> None:
        self.assertEqual(self.selector["schema_version"], "project.current-selector.v2")
        self.assertEqual(self.selector["authoritative_current_reality"], ".project/current-reality-v4.json")
        self.assertEqual(self.selector["authoritative_state_index"], ".project/state-index-v13.json")
        self.assertEqual(self.selector["authoritative_handoff"], ".project/handoffs/current-state-v3.md")
        self.assertIsNone(self.selector["pending_azure_ai_terminal_reconciliation"])
        self.assertIsNone(self.selector["active_azure_ai_activation_authorization"])
        self.assertEqual(
            self.selector["active_servicetracer_planning_authorization"],
            ".project/deployment-requests/servicetracer-demo-api-plan-run1.json",
        )

    def test_repository_watermark_advances_through_pr250(self) -> None:
        repo = self.reality["repository_state"]
        self.assertEqual(repo["observed_main"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 250)
        self.assertEqual(repo["latest_merged_source_head"], PR250_SOURCE)
        self.assertEqual(repo["latest_exact_head_ci"]["run_id"], 30512595145)
        self.assertEqual(repo["latest_exact_head_ci"]["conclusion"], "success")
        self.assertEqual(repo["open_pull_requests_observed"], [])

    def test_run8_terminal_artifact_supersedes_trigger_uncertainty(self) -> None:
        self.assertEqual(self.run8["status"], "consumed_terminal_failure")
        self.assertEqual(self.run8["repository"]["execution_commit"], RUN8_COMMIT)
        self.assertEqual(self.run8["workflow"]["artifact_digest"], RUN8_ARTIFACT_DIGEST)
        self.assertEqual(self.run8["result"]["direct_account_scoped_matches"], 0)
        self.assertFalse(self.run8["result"]["direct_account_role_verified"])
        for key in (
            "deployment_inventory_queried",
            "model_listing_queried",
            "model_capacity_queried",
            "arm_what_if_performed",
            "azure_mutations_performed",
            "deployment_started",
            "account_hardening_started",
            "model_request_performed",
            "endpoint_live",
            "separate_verified_gpt5_runtime_modified",
        ):
            self.assertFalse(self.run8["operation_boundary"][key], key)
        self.assertTrue(self.run8["authority"]["authorization_consumed"])
        self.assertFalse(self.run8["authority"]["workflow_rerun_authorized"])

    def test_promoted_run8_evidence_hash_matches_manifest(self) -> None:
        expected = RUN8_MANIFEST.read_text(encoding="utf-8").strip().split()[0]
        actual = hashlib.sha256(RUN8_EVIDENCE.read_bytes()).hexdigest()
        self.assertEqual(actual, expected)
        self.assertEqual(actual, EVIDENCE_SHA)
        self.assertEqual(self.run8_evidence["source"]["artifact_digest"], RUN8_ARTIFACT_DIGEST)
        self.assertEqual(self.run8_evidence["identity_observation"]["direct_account_scoped_matches"], 0)
        self.assertFalse(self.run8_evidence["operation_boundary"]["azure_mutations_performed"])

    def test_run8_request_is_terminalized(self) -> None:
        self.assertEqual(self.run8_request["status"], "consumed_terminal_failure")
        self.assertFalse(self.run8_request["active"])
        self.assertEqual(self.run8_request["attempts_observed"], 1)
        terminal = self.run8_request["terminal_execution"]
        self.assertTrue(terminal["workflow_run_retrieved"])
        self.assertEqual(terminal["workflow_run"], 30510660758)
        self.assertFalse(terminal["azure_mutations_performed"])
        self.assertFalse(self.run8_request["authority"]["manual_rerun_authorized"])

    def test_servicetracer_authority_remains_unconsumed_after_skipped_edit_recovery(self) -> None:
        self.assertEqual(self.plan_request["status"], "authorized_pending_dispatch")
        self.assertTrue(self.plan_request["active"])
        self.assertFalse(self.plan_request["dispatch"]["performed"])
        state = self.reality["domain_state"]["servicetracer_planning_run1"]
        self.assertEqual(state["accepted_dispatches_observed"], 0)
        self.assertEqual(state["remaining_authorized_dispatches"], 1)
        self.assertEqual(state["edited_command_workflow_run_id"], 30512805833)
        self.assertFalse(state["edited_command_workflow_jobs_started"])
        self.assertFalse(state["durable_consumption_marker_observed"])
        self.assertFalse(state["child_workflow_dispatch_accepted"])
        self.assertFalse(state["azure_authentication_or_query_observed"])
        self.assertFalse(state["arm_validation_or_what_if_observed"])
        self.assertFalse(state["azure_mutation_or_deployment_observed"])
        self.assertFalse(state["deployment_authorized"])

    def test_state_index_has_only_planning_authority_active(self) -> None:
        active = self.index["active_authorizations"]
        self.assertIsNone(active["azure_ai_activation"])
        self.assertIsNone(active["deployment"])
        self.assertEqual(
            active["servicetracer_demo_api_planning"],
            ".project/deployment-requests/servicetracer-demo-api-plan-run1.json",
        )
        self.assertTrue(self.index["consumed_authorities"]["azure_ai_go_live_run8"])
        self.assertFalse(self.index["consumed_authorities"]["azure_ai_go_live_run8_rerun_authorized"])

    def test_handoff_preserves_cost_and_execution_boundaries(self) -> None:
        self.assertIn(f"observed main: {MAIN}", self.handoff)
        self.assertIn("latest merged PR: #250", self.handoff)
        self.assertIn("direct account-scoped Cognitive Services OpenAI User matches: 0", self.handoff)
        self.assertIn("edited-command workflow jobs started: false", self.handoff)
        self.assertIn("accepted child dispatches observed: 0", self.handoff)
        self.assertIn("planning ceiling: CAD $25.00", self.handoff)
        self.assertIn("deployment authorized: false", self.handoff)

    def test_sync_is_repository_only(self) -> None:
        authority = self.sync["authority"]
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
