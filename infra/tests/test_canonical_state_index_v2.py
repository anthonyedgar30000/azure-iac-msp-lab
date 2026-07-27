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
DEPLOYMENT = ROOT / ".project/reconciliations/collector-demo-api-deployment-run18-20260726.json"
POST_MERGE = ROOT / ".project/reconciliations/collector-golden-path-post-merge-20260726.json"
PREFLIGHT = ROOT / ".project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json"
AUTHORIZATION = ROOT / ".project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json"
RESOLUTION = ROOT / ".project/reconciliations/post-pr137-provenance-authority-expiry-20260727.json"

MAIN = "f6e79818150d72b75d1e4f25be172e6dc577114d"
SOURCE = "f6e79818150d72b75d1e4f25be172e6dc577114d"
SELECTED_SOURCE = "1677606ded960c951fa37f0fdbfae50ba4b3cc34"
DEPLOYED_SOURCE = "98b092201053fd3592be157a24de6e623e6b74a6"
COLLECTOR = "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run"


class CanonicalStateIndexV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads(INDEX.read_text())
        cls.current = json.loads(CURRENT.read_text())
        cls.legacy = json.loads(LEGACY.read_text())
        cls.gate = json.loads(GATE.read_text())
        cls.handoff = HANDOFF.read_text()
        cls.deployment = json.loads(DEPLOYMENT.read_text())
        cls.post_merge = json.loads(POST_MERGE.read_text())
        cls.preflight = json.loads(PREFLIGHT.read_text())
        cls.authorization = json.loads(AUTHORIZATION.read_text())
        cls.resolution = json.loads(RESOLUTION.read_text())

    def test_index_selects_versioned_canonical_state_and_resolution(self):
        self.assertEqual(self.index["canonical_current_reality"], ".project/current-reality-v2.json")
        self.assertFalse(self.index["legacy_compatibility_snapshots"][0]["authoritative_for_current_operations"])
        self.assertEqual(self.legacy["repository_state"]["observed_head"], "665e051375594d11e58e434231bd06775dbdc560")
        self.assertIsNone(self.index["active_deployment_authorization"])
        self.assertEqual(
            self.index["latest_authorization_resolution"],
            ".project/reconciliations/post-pr137-provenance-authority-expiry-20260727.json",
        )

    def test_current_repository_watermark_is_pr137(self):
        repo = self.current["repository_state"]
        self.assertEqual(repo["observed_head"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 137)
        self.assertEqual(repo["open_pull_requests_observed"], [])
        self.assertEqual(repo["exact_source_head"], SOURCE)
        self.assertEqual(repo["exact_source_ci_run_id"], 30224641320)
        self.assertEqual(repo["exact_source_ci_conclusion"], "success")
        self.assertEqual(repo["merge_commit_ci"], "success")
        self.assertTrue(repo["merge_observation"]["human_or_external_merge_observed"])
        self.assertFalse(repo["merge_observation"]["assistant_merge_action_performed"])

    def test_ci_history_preserves_failed_merged_heads_and_latest_green_head(self):
        anchors = self.current["evidence_anchors"]
        self.assertEqual(anchors["pr130_exact_source_ci_conclusion"], "failure")
        self.assertEqual(anchors["pr131_exact_source_ci_conclusion"], "failure")
        self.assertEqual(anchors["pr132_exact_source_ci_conclusion"], "success")
        self.assertEqual(anchors["pr137_exact_source_ci_conclusion"], "success")
        self.assertEqual(anchors["pr137_merge_commit"], MAIN)

    def test_collector_deployment_and_provenance_boundaries(self):
        api = self.current["collector_demo_api"]
        self.assertEqual(api["runtime_evidence"]["collector_endpoint"], COLLECTOR)
        self.assertEqual(api["source_binding"]["deployed_source"], DEPLOYED_SOURCE)
        self.assertEqual(api["source_binding"]["selected_provenance_deployment_source"], SELECTED_SOURCE)
        self.assertEqual(api["source_binding"]["current_main"], MAIN)
        self.assertFalse(api["source_binding"]["current_main_deployed"])
        self.assertEqual(api["source_binding"]["selected_provenance_source_deployed"], "not_observed")
        provenance = api["provenance_monitor"]
        self.assertTrue(provenance["repository_implemented"])
        self.assertFalse(provenance["exact_source_runtime_deployed"])
        self.assertEqual(provenance["deployment_outcome"], "not_observed")
        self.assertFalse(provenance["azure_host_identity_verified_live"])
        self.assertFalse(provenance["browser_rendering_verified"])

    def test_verified_preflight_and_cost_are_promoted(self):
        self.assertTrue(self.preflight["artifact"]["independently_verified_digest"])
        self.assertEqual(self.preflight["artifact"]["manifest_payloads_verified"], 26)
        self.assertEqual(self.preflight["what_if"]["change_counts"]["Create"], 0)
        cost = self.current["collector_demo_api"]["cost_and_budget"]
        self.assertEqual(cost["actual_cost_cad"], 4.03203831168191)
        self.assertEqual(cost["currency"], "CAD")
        self.assertEqual(cost["remaining_Azure_for_Students_credit"], "not_observed")

    def test_expired_grant_does_not_manufacture_consumption_or_retry(self):
        resolution = self.resolution["authorization_resolution"]
        self.assertEqual(resolution["current_temporal_status"], "expired")
        self.assertEqual(resolution["consumption_status"], "not_observed")
        self.assertFalse(resolution["expired_unused_claimed"])
        self.assertFalse(resolution["consumed_claimed"])
        self.assertFalse(resolution["deployment_success_claimed"])
        self.assertFalse(resolution["deployment_failure_claimed"])
        self.assertFalse(resolution["retry_authorized"])
        self.assertEqual(self.authorization["consumption"]["status"], "pending_consumption")

    def test_historical_post_merge_record_remains_fail_closed(self):
        self.assertEqual(
            self.post_merge["repository_observation"]["main"],
            "2f5b60c1d8328d13823e2cc1def09e6be384ecb5",
        )
        self.assertTrue(self.post_merge["provenance_monitor"]["repository_merged"])
        self.assertFalse(self.post_merge["provenance_monitor"]["exact_source_runtime_deployed"])
        self.assertFalse(self.post_merge["authority"]["pull_request_merge_authorized"])

    def test_gate_requires_new_authority_before_provenance_runtime_proof(self):
        criteria = {x["criterion_id"]: x for x in self.gate["p0"]["criteria"]}
        self.assertTrue(criteria["p0-exact-what-if-evidence"]["complete"])
        self.assertTrue(criteria["p0-source-and-cost-decision"]["complete"])
        self.assertTrue(criteria["p0-collector-deployment"]["complete"])
        self.assertFalse(criteria["p0-runtime-contract"]["complete"])
        self.assertFalse(criteria["p0-browser-demonstration"]["complete"])
        self.assertEqual(self.gate["evidence_inputs"]["current_main"], MAIN)
        self.assertIn("repository_implemented != deployed_to_collector_VM", self.handoff)
        self.assertIn("authorization_expired != authorization_consumed", self.handoff)

    def test_no_new_execution_authority_is_manufactured(self):
        for key, value in self.current["authority"].items():
            if key in {
                "repository_reconciliation_authorized",
                "draft_pull_request_authorized",
                "ordinary_pull_request_ci_authorized",
            }:
                continue
            self.assertFalse(value, key)


if __name__ == "__main__":
    unittest.main()
