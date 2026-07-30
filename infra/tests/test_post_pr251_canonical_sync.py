from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SELECTOR = ROOT / ".project/selectors/post-pr251-current.json"
REALITY = ROOT / ".project/current-reality-v4.json"
INDEX = ROOT / ".project/state-index-v13.json"
HANDOFF = ROOT / ".project/handoffs/current-state-v3.md"
SYNC = ROOT / ".project/reconciliations/post-pr251-canonical-sync-20260730.json"
RUN8_RECON = ROOT / ".project/reconciliations/azure-ai-go-live-run8-terminal-20260730.json"
RUN8_EVIDENCE = ROOT / ".project/evidence/azure-ai-go-live-run8-terminal-summary.json"
RUN8_MANIFEST = ROOT / ".project/evidence/azure-ai-go-live-run8-terminal-summary.sha256"
RUN8_REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run8.json"
PLAN_RECON = ROOT / ".project/reconciliations/servicetracer-demo-api-plan-run1-terminal-20260730.json"
PLAN_EVIDENCE = ROOT / ".project/evidence/servicetracer-demo-api-plan-run1-terminal-summary.json"
PLAN_MANIFEST = ROOT / ".project/evidence/servicetracer-demo-api-plan-run1-terminal-summary.sha256"
PLAN_REQUEST = ROOT / ".project/deployment-requests/servicetracer-demo-api-plan-run1.json"

MAIN = "09fe72e3a82ea6ae56e1e85fd9745c9940ed6c12"
PR251_SOURCE = "2d17b70edc2d0474967db388bd3d425fb5400b74"
RUN8_ARTIFACT_DIGEST = "sha256:e05dccbc1618e052f905f12f03d3576a05357bdf6c298d380a140f3ecef25f51"
RUN8_EVIDENCE_SHA = "572489ee1380b239b4cd229ad1d99ef8aeb2e9831ee46366ed0b4664d4e417b7"
PLAN_ARTIFACT_DIGEST = "sha256:a3bb46d90bdff6329bcfe15f5b00b1f144b68b009724f9e912ca890ced9384d9"
PLAN_EVIDENCE_SHA = "3c79f43342356bd448531ba35501d9ab0591f1eee8d2bba1f0437d44c88a71da"


class PostPr251CanonicalSyncTests(unittest.TestCase):
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
        cls.plan = json.loads(PLAN_RECON.read_text(encoding="utf-8"))
        cls.plan_evidence = json.loads(PLAN_EVIDENCE.read_text(encoding="utf-8"))
        cls.plan_request = json.loads(PLAN_REQUEST.read_text(encoding="utf-8"))

    def test_selector_promotes_current_state_and_clears_authority(self) -> None:
        self.assertEqual(self.selector["schema_version"], "project.current-selector.v2")
        self.assertEqual(self.selector["authoritative_current_reality"], ".project/current-reality-v4.json")
        self.assertEqual(self.selector["authoritative_state_index"], ".project/state-index-v13.json")
        self.assertEqual(self.selector["authoritative_handoff"], ".project/handoffs/current-state-v3.md")
        self.assertEqual(self.selector["latest_operational_overlay"], ".project/reconciliations/servicetracer-demo-api-plan-run1-terminal-20260730.json")
        self.assertIsNone(self.selector["pending_azure_ai_terminal_reconciliation"])
        self.assertIsNone(self.selector["active_azure_ai_activation_authorization"])
        self.assertIsNone(self.selector["active_servicetracer_planning_authorization"])
        self.assertIsNone(self.selector["active_deployment_authorization"])

    def test_repository_watermark_advances_through_pr251(self) -> None:
        repo = self.reality["repository_state"]
        self.assertEqual(repo["observed_main"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 251)
        self.assertEqual(repo["latest_merged_source_head"], PR251_SOURCE)
        self.assertEqual(repo["latest_exact_head_ci"]["run_id"], 30512881241)
        self.assertEqual(repo["latest_exact_head_ci"]["conclusion"], "success")

    def test_run8_terminal_artifact_and_request(self) -> None:
        self.assertEqual(self.run8["status"], "consumed_terminal_failure")
        self.assertEqual(self.run8["workflow"]["artifact_digest"], RUN8_ARTIFACT_DIGEST)
        self.assertEqual(self.run8["result"]["direct_account_scoped_matches"], 0)
        self.assertFalse(self.run8["operation_boundary"]["azure_mutations_performed"])
        self.assertFalse(self.run8["operation_boundary"]["deployment_started"])
        self.assertTrue(self.run8["authority"]["authorization_consumed"])
        self.assertFalse(self.run8["authority"]["workflow_rerun_authorized"])
        self.assertEqual(self.run8_request["status"], "consumed_terminal_failure")
        self.assertFalse(self.run8_request["active"])
        self.assertTrue(self.run8_request["terminal_execution"]["workflow_run_retrieved"])
        self.assertFalse(self.run8_request["authority"]["manual_rerun_authorized"])

    def test_run8_evidence_hash(self) -> None:
        expected = RUN8_MANIFEST.read_text(encoding="utf-8").strip().split()[0]
        actual = hashlib.sha256(RUN8_EVIDENCE.read_bytes()).hexdigest()
        self.assertEqual(actual, expected)
        self.assertEqual(actual, RUN8_EVIDENCE_SHA)
        self.assertEqual(self.run8_evidence["source"]["artifact_digest"], RUN8_ARTIFACT_DIGEST)

    def test_servicetracer_plan_is_consumed_terminal_failure(self) -> None:
        self.assertEqual(self.plan["status"], "consumed_terminal_failure")
        self.assertEqual(self.plan["workflow"]["run_id"], 30513630134)
        self.assertEqual(self.plan["workflow"]["artifact_digest"], PLAN_ARTIFACT_DIGEST)
        self.assertEqual(self.plan["result"]["failure_classification"], "confirmation_input_mismatch")
        self.assertTrue(self.plan["authority"]["authorization_consumed"])
        self.assertFalse(self.plan["authority"]["workflow_rerun_authorized"])
        for key in ("dependency_subscription_query_started", "target_subscription_query_started", "provider_policy_quota_sku_inventory_queried", "arm_validation_performed", "arm_what_if_performed", "azure_mutations_performed", "deployment_started"):
            self.assertFalse(self.plan["operation_boundary"][key], key)
        self.assertEqual(self.plan_request["status"], "consumed_terminal_failure")
        self.assertFalse(self.plan_request["active"])
        self.assertTrue(self.plan_request["dispatch"]["performed"])
        self.assertEqual(self.plan_request["dispatch"]["accepted_run_id"], 30513630134)
        self.assertFalse(self.plan_request["terminal"]["azure_login_started"])
        self.assertFalse(self.plan_request["terminal"]["rerun_authorized"])

    def test_servicetracer_evidence_hash_and_empty_artifact_boundary(self) -> None:
        expected = PLAN_MANIFEST.read_text(encoding="utf-8").strip().split()[0]
        actual = hashlib.sha256(PLAN_EVIDENCE.read_bytes()).hexdigest()
        self.assertEqual(actual, expected)
        self.assertEqual(actual, PLAN_EVIDENCE_SHA)
        self.assertEqual(self.plan_evidence["source"]["artifact_digest"], PLAN_ARTIFACT_DIGEST)
        self.assertEqual(self.plan_evidence["artifact_observation"]["manifest_entry_count"], 0)
        self.assertFalse(self.plan_evidence["artifact_observation"]["planning_summary_present"])
        self.assertFalse(self.plan_evidence["operation_boundary"]["azure_login_started"])

    def test_no_operational_authority_remains(self) -> None:
        active = self.index["active_authorizations"]
        self.assertTrue(all(value is None for value in active.values()))
        self.assertTrue(self.index["consumed_authorities"]["azure_ai_go_live_run8"])
        self.assertFalse(self.index["consumed_authorities"]["azure_ai_go_live_run8_rerun_authorized"])
        self.assertTrue(self.index["consumed_authorities"]["servicetracer_demo_api_plan_run1"])
        self.assertFalse(self.index["consumed_authorities"]["servicetracer_demo_api_plan_run1_rerun_authorized"])

    def test_handoff_preserves_both_terminal_boundaries(self) -> None:
        self.assertIn(f"observed main: {MAIN}", self.handoff)
        self.assertIn("latest merged PR: #251", self.handoff)
        self.assertIn("workflow run: 30513630134 / attempt 1", self.handoff)
        self.assertIn("failure class: confirmation_input_mismatch", self.handoff)
        self.assertIn("Azure login started: false", self.handoff)
        self.assertIn("direct account-scoped Cognitive Services OpenAI User matches: 0", self.handoff)
        self.assertIn("active ServiceTracer planning authority: none", self.handoff)
        self.assertIn("deployment authorized: false", self.handoff)

    def test_sync_itself_is_repository_only(self) -> None:
        authority = self.sync["authority"]
        self.assertTrue(authority["repository_branch_and_declared_writes"])
        self.assertTrue(authority["pull_request_creation"])
        self.assertTrue(authority["ordinary_exact_head_ci"])
        self.assertTrue(authority["merge_after_green_and_freshness_recheck"])
        for key in ("workflow_dispatch_or_rerun_by_this_sync", "azure_authentication_or_query_by_this_sync", "arm_what_if_by_this_sync", "azure_mutation_by_this_sync", "rbac_mutation", "model_call", "local_mcp_client_call", "remote_mcp_deployment", "chatgpt_connection", "cleanup", "rollback"):
            self.assertFalse(authority[key], key)


if __name__ == "__main__":
    unittest.main()
