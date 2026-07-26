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

MAIN = "2f5b60c1d8328d13823e2cc1def09e6be384ecb5"
SOURCE = "6b7bd5362b17c9edfc0b41da65d5b798e5d00b45"
DEPLOYED_SOURCE = "98b092201053fd3592be157a24de6e623e6b74a6"
COLLECTOR = "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run"

class CanonicalStateIndexV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index=json.loads(INDEX.read_text())
        cls.current=json.loads(CURRENT.read_text())
        cls.legacy=json.loads(LEGACY.read_text())
        cls.gate=json.loads(GATE.read_text())
        cls.handoff=HANDOFF.read_text()
        cls.deployment=json.loads(DEPLOYMENT.read_text())
        cls.post_merge=json.loads(POST_MERGE.read_text())

    def test_index_selects_versioned_canonical_state(self):
        self.assertEqual(self.index["canonical_current_reality"], ".project/current-reality-v2.json")
        self.assertFalse(self.index["legacy_compatibility_snapshots"][0]["authoritative_for_current_operations"])
        self.assertEqual(self.legacy["repository_state"]["observed_head"], "665e051375594d11e58e434231bd06775dbdc560")

    def test_current_repository_watermark_is_pr132(self):
        repo=self.current["repository_state"]
        self.assertEqual(repo["observed_head"],MAIN)
        self.assertEqual(repo["latest_merged_pull_request"],132)
        self.assertEqual(repo["open_pull_requests_observed"],[])
        self.assertEqual(repo["exact_source_head"],SOURCE)
        self.assertEqual(repo["exact_source_ci_run_id"],30204497860)
        self.assertEqual(repo["exact_source_ci_conclusion"],"success")
        self.assertTrue(repo["merge_observation"]["human_or_external_merge_observed"])
        self.assertFalse(repo["merge_observation"]["assistant_merge_action_performed"])

    def test_ci_history_preserves_failed_merged_heads_and_final_repair(self):
        anchors=self.current["evidence_anchors"]
        self.assertEqual(anchors["pr130_exact_source_ci_conclusion"],"failure")
        self.assertEqual(anchors["pr131_exact_source_ci_conclusion"],"failure")
        self.assertEqual(anchors["pr132_exact_source_ci_conclusion"],"success")
        self.assertEqual(anchors["pr132_merge_commit"],MAIN)

    def test_collector_deployment_and_provenance_boundaries(self):
        api=self.current["collector_demo_api"]
        self.assertTrue(api["deployment"]["succeeded"])
        self.assertEqual(api["runtime_evidence"]["collector_endpoint"],COLLECTOR)
        self.assertEqual(api["source_binding"]["deployed_source"],DEPLOYED_SOURCE)
        self.assertEqual(api["source_binding"]["current_main"],MAIN)
        self.assertFalse(api["source_binding"]["current_main_deployed"])
        provenance=api["provenance_monitor"]
        self.assertTrue(provenance["repository_implemented"])
        self.assertFalse(provenance["exact_source_runtime_deployed"])
        self.assertFalse(provenance["azure_host_identity_verified_live"])
        self.assertFalse(provenance["browser_rendering_verified"])

    def test_post_merge_record_is_fail_closed(self):
        self.assertEqual(self.post_merge["repository_observation"]["main"],MAIN)
        self.assertEqual(self.post_merge["repository_observation"]["open_pull_requests_observed"],[])
        self.assertTrue(self.post_merge["provenance_monitor"]["repository_merged"])
        self.assertFalse(self.post_merge["provenance_monitor"]["exact_source_runtime_deployed"])
        self.assertFalse(self.post_merge["authority"]["pull_request_merge_authorized"])

    def test_gate_requires_deployment_before_browser_proof(self):
        criteria={x["criterion_id"]:x for x in self.gate["p0"]["criteria"]}
        self.assertTrue(criteria["p0-collector-deployment"]["complete"])
        self.assertFalse(criteria["p0-runtime-contract"]["complete"])
        self.assertFalse(criteria["p0-browser-demonstration"]["complete"])
        self.assertEqual(self.gate["evidence_inputs"]["current_main"],MAIN)
        self.assertIn("repository_implemented != deployed_to_collector_VM",self.handoff)

    def test_no_new_execution_authority_is_manufactured(self):
        for key,value in self.current["authority"].items():
            if key in {"repository_reconciliation_authorized","draft_pull_request_authorized","ordinary_pull_request_ci_authorized"}:
                continue
            self.assertFalse(value,key)

if __name__ == "__main__": unittest.main()
