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
POST_MERGE = ROOT / ".project/reconciliations/provenance-monitor-post-merge-pr132-20260726.json"

MAIN = "2f5b60c1d8328d13823e2cc1def09e6be384ecb5"
SOURCE = "6b7bd5362b17c9edfc0b41da65d5b798e5d00b45"
PR130_HEAD = "07e7056b3d66e88055f93d7f3c27d31f8281c316"
PR131_HEAD = "bec88217096dce5ac205b93bb5f019f0f801fe62"
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
        self.assertEqual(
            self.index["latest_reconciliation"],
            ".project/reconciliations/provenance-monitor-post-merge-pr132-20260726.json",
        )
        self.assertFalse(self.index["legacy_compatibility_snapshots"][0]["authoritative_for_current_operations"])
        self.assertEqual(self.legacy["repository_state"]["observed_head"], "665e051375594d11e58e434231bd06775dbdc560")

    def test_current_repository_watermark_is_pr132(self):
        repo = self.current["repository_state"]
        self.assertEqual(repo["observed_head"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 132)
        self.assertEqual(repo["open_pull_requests_observed"], [])
        self.assertEqual(repo["exact_source_head"], SOURCE)
        self.assertEqual(repo["exact_source_ci_run_id"], 30204497860)
        self.assertEqual(repo["exact_source_ci_conclusion"], "success")
        self.assertFalse(repo["source_vs_merge_file_content_difference_observed"])
        self.assertEqual(repo["merge_commit_ci"], "not_observed")
        self.assertTrue(repo["merge_observation"]["human_or_external_merge_observed"])
        self.assertFalse(repo["merge_observation"]["assistant_merge_action_performed"])

    def test_failed_head_merge_chain_is_preserved(self):
        chain = {item["pull_request"]: item for item in self.current["repository_state"]["recent_merge_chain"]}
        self.assertEqual(chain[130]["exact_source_head"], PR130_HEAD)
        self.assertEqual(chain[130]["exact_source_ci_conclusion"], "failure")
        self.assertEqual(chain[131]["exact_source_head"], PR131_HEAD)
        self.assertEqual(chain[131]["exact_source_ci_conclusion"], "failure")
        self.assertEqual(chain[132]["exact_source_head"], SOURCE)
        self.assertEqual(chain[132]["exact_source_ci_conclusion"], "success")
        self.assertFalse(chain[132]["source_vs_merge_file_content_difference_observed"])

    def test_post_merge_record_is_fail_closed(self):
        self.assertEqual(self.post_merge["repository_observation"]["main"], MAIN)
        self.assertEqual(self.post_merge["repository_observation"]["open_pull_requests_observed"], [])
        self.assertEqual(self.post_merge["merge_chain"][0]["exact_source_ci_conclusion"], "failure")
        self.assertEqual(self.post_merge["merge_chain"][1]["exact_source_ci_conclusion"], "failure")
        self.assertEqual(self.post_merge["merge_chain"][2]["exact_source_ci_conclusion"], "success")
        self.assertFalse(self.post_merge["azure_evidence_boundary"]["fresh_azure_query_performed"])
        self.assertFalse(self.post_merge["azure_evidence_boundary"]["provenance_runtime_contract_deployed"])
        self.assertFalse(self.post_merge["authority"]["pull_request_merge_authorized"])

    def test_run18_deployment_remains_current_azure_evidence(self):
        anchors = self.current["evidence_anchors"]
        self.assertEqual(anchors["workflow_run_id"], RUN_ID)
        self.assertEqual(anchors["artifact_id"], ARTIFACT_ID)
        self.assertEqual(anchors["artifact_manifest_payloads_verified"], 48)
        self.assertEqual(anchors["pr132_merge_commit"], MAIN)
        self.assertEqual(anchors["pr132_exact_source_head"], SOURCE)
        self.assertEqual(self.deployment["source"]["reviewed_commit"], DEPLOYED_SOURCE)
        self.assertTrue(self.deployment["deployment"]["deployment_step_succeeded"])
        self.assertEqual(self.deployment["deployment"]["backend_pool"]["address_count"], 1)
        self.assertEqual(self.deployment["deployment"]["collector_vm_extension"]["provisioning_state"], "Succeeded")

    def test_provenance_monitor_is_repository_only(self):
        monitor = self.current["provenance_monitor"]
        self.assertEqual(monitor["repository_status"]["exact_contract_repair_pr"], 132)
        self.assertEqual(monitor["repository_status"]["exact_contract_repair_ci_conclusion"], "success")
        deployment = monitor["deployment_and_validation"]
        self.assertFalse(deployment["fresh_azure_query_performed"])
        self.assertFalse(deployment["azure_mutation_performed"])
        self.assertFalse(deployment["deployment_performed"])
        self.assertFalse(deployment["runtime_contract_deployed"])
        self.assertFalse(deployment["github_pages_publication_verified"])
        self.assertFalse(deployment["browser_health_identity_verified"])
        self.assertFalse(deployment["browser_request_correlation_verified"])

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
        self.assertFalse(api["frontend_binding"]["provenance_runtime_contract_deployed"])
        self.assertFalse(api["frontend_binding"]["browser_transaction_verified"])
        self.assertFalse(api["frontend_binding"]["retry_authorized"])

    def test_gate_tracks_green_repository_repair_without_overclaiming(self):
        criteria = {item["criterion_id"]: item for item in self.gate["p0"]["criteria"]}
        self.assertTrue(criteria["p0-collector-deployment"]["complete"])
        self.assertFalse(criteria["p0-runtime-contract"]["complete"])
        self.assertFalse(criteria["p0-servicetracer-scenario"]["complete"])
        self.assertFalse(criteria["p0-browser-demonstration"]["complete"])
        evidence = self.gate["evidence_inputs"]
        self.assertEqual(evidence["current_main"], MAIN)
        self.assertEqual(evidence["latest_merged_pull_request"], 132)
        self.assertEqual(evidence["latest_exact_source_ci_conclusion"], "success")
        self.assertEqual(evidence["open_draft_pull_requests_observed"], [])
        self.assertFalse(evidence["provenance_runtime_contract_deployed"])
        self.assertIn(COLLECTOR, self.handoff)
        self.assertIn("PR_merged != exact_head_CI_passed", self.handoff)
        self.assertIn("repository_implemented != deployed_to_collector_VM", self.handoff)

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
