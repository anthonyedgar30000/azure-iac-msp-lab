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

MAIN = "81df65ca7d4cd77fc89aefb2fac128ead456df7d"
SOURCE = "1f9a00f572235c74b99520a504d8b057003d411c"
DEPLOYED_SOURCE = "98b092201053fd3592be157a24de6e623e6b74a6"
RUN_ID = 30196388398
ARTIFACT_ID = 8630260279
COLLECTOR = "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run"


class CanonicalStateIndexV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.current = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
        cls.gate = json.loads(GATE.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.deployment = json.loads(DEPLOYMENT.read_text(encoding="utf-8"))
        cls.post_merge = json.loads(POST_MERGE.read_text(encoding="utf-8"))

    def test_index_selects_versioned_canonical_state(self):
        self.assertEqual(self.index["canonical_current_reality"], ".project/current-reality-v2.json")
        self.assertEqual(self.index["canonical_completion_gate"], ".project/lab-v1-completion-gate-v2.json")
        self.assertFalse(self.index["legacy_compatibility_snapshots"][0]["authoritative_for_current_operations"])
        self.assertEqual(self.legacy["repository_state"]["observed_head"], "665e051375594d11e58e434231bd06775dbdc560")

    def test_current_repository_watermark_is_pr126(self):
        repo = self.current["repository_state"]
        self.assertEqual(repo["observed_head"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 126)
        self.assertEqual(repo["open_pull_requests_observed"], [127])
        self.assertEqual(repo["exact_source_head"], SOURCE)
        self.assertEqual(repo["exact_source_ci_run_id"], 30203751115)
        self.assertEqual(repo["exact_source_ci_conclusion"], "success")
        self.assertEqual(repo["merge_commit_ci"], "not_observed")
        self.assertTrue(repo["merge_observation"]["human_or_external_merge_observed"])
        self.assertFalse(repo["merge_observation"]["assistant_merge_action_performed"])

    def test_post_merge_record_is_fail_closed(self):
        self.assertEqual(self.post_merge["repository_observation"]["main"], MAIN)
        self.assertEqual(self.post_merge["repository_observation"]["open_pull_requests_observed"], [127])
        self.assertTrue(self.post_merge["collector_binding"]["merged_into_main"])
        self.assertFalse(self.post_merge["collector_binding"]["github_pages_publication_verified"])
        self.assertFalse(self.post_merge["collector_binding"]["browser_transaction_verified"])
        self.assertFalse(self.post_merge["open_pr127_boundary"]["accepted_as_current_evidence"])
        self.assertFalse(self.post_merge["authority"]["pull_request_merge_authorized"])

    def test_run18_deployment_is_current_evidence(self):
        anchors = self.current["evidence_anchors"]
        self.assertEqual(anchors["workflow_run_id"], RUN_ID)
        self.assertEqual(anchors["artifact_id"], ARTIFACT_ID)
        self.assertEqual(anchors["artifact_manifest_payloads_verified"], 48)
        self.assertEqual(anchors["pr126_merge_commit"], MAIN)
        self.assertEqual(anchors["pr126_exact_source_head"], SOURCE)
        self.assertEqual(self.deployment["source"]["reviewed_commit"], DEPLOYED_SOURCE)
        self.assertTrue(self.deployment["deployment"]["deployment_step_succeeded"])
        self.assertEqual(self.deployment["deployment"]["backend_pool"]["address_count"], 1)
        self.assertEqual(self.deployment["deployment"]["collector_vm_extension"]["provisioning_state"], "Succeeded")

    def test_collector_is_deployed_but_browser_gate_remains_open(self):
        api = self.current["collector_demo_api"]
        self.assertTrue(api["deployment"]["performed"])
        self.assertTrue(api["deployment"]["succeeded"])
        self.assertTrue(api["deployment"]["authority_consumed"])
        self.assertEqual(api["source_binding"]["current_main"], MAIN)
        self.assertFalse(api["source_binding"]["current_main_deployed"])
        self.assertEqual(api["runtime_evidence"]["collector_endpoint"], COLLECTOR)
        self.assertEqual(api["runtime_evidence"]["health_status"], "healthy")
        self.assertEqual(api["runtime_evidence"]["transaction_count"], 20)
        self.assertEqual(api["runtime_evidence"]["successful_transactions"], 0)
        self.assertFalse(api["runtime_evidence"]["stable_backend_localization"])
        self.assertFalse(api["frontend_binding"]["browser_transaction_verified"])
        self.assertFalse(api["frontend_binding"]["retry_authorized"])

    def test_gate_tracks_completed_deployment_without_overclaiming(self):
        criteria = {item["criterion_id"]: item for item in self.gate["p0"]["criteria"]}
        self.assertTrue(criteria["p0-collector-deployment"]["complete"])
        self.assertFalse(criteria["p0-runtime-contract"]["complete"])
        self.assertFalse(criteria["p0-servicetracer-scenario"]["complete"])
        self.assertFalse(criteria["p0-browser-demonstration"]["complete"])
        self.assertEqual(self.gate["evidence_inputs"]["current_main"], MAIN)
        self.assertEqual(self.gate["evidence_inputs"]["open_draft_pull_requests_observed"], [127])
        self.assertIn(COLLECTOR, self.handoff)
        self.assertIn("independent_API_ready != collector_golden_path_verified", self.handoff)

    def test_no_new_execution_authority_is_manufactured(self):
        authority = self.current["authority"]
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_authorized",
            "azure_authentication_authorized",
            "azure_query_authorized",
            "azure_mutation_authorized",
            "deployment_authorized",
            "browser_verification_authorized",
            "transaction_replay_authorized",
            "rollback_authorized",
            "cleanup_authorized",
            "rbac_mutation_authorized",
        ):
            self.assertFalse(authority[key], key)


if __name__ == "__main__":
    unittest.main()
