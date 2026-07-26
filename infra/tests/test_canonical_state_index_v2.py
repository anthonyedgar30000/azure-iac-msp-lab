from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / ".project/state-index.json"
CURRENT = ROOT / ".project/current-reality-v2.json"
LEGACY = ROOT / ".project/current-reality.json"
GATE = ROOT / ".project/lab-v1-completion-gate.json"
HANDOFF = ROOT / ".project/handoffs/current-state.md"
PROMOTION = ROOT / ".project/reconciliations/collector-demo-api-what-if-run16-artifact-promotion-20260726.json"

MAIN = "9bfff60bd2e1e3bbf5610807df7d970c9bd9f229"
RUN_ID = 30192970923
ARTIFACT_ID = 8629191915
REVIEWED = "8de1f61f8a0ea06dcf94b94c798edde2aace357d"


class CanonicalStateIndexV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.current = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
        cls.gate = json.loads(GATE.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.promotion = json.loads(PROMOTION.read_text(encoding="utf-8"))

    def test_index_selects_new_canonical_state(self):
        self.assertEqual(
            self.index["canonical_current_reality"],
            ".project/current-reality-v2.json",
        )
        legacy = self.index["legacy_compatibility_snapshots"][0]
        self.assertEqual(legacy["path"], ".project/current-reality.json")
        self.assertFalse(legacy["authoritative_for_current_operations"])
        self.assertEqual(
            self.legacy["repository_state"]["observed_head"],
            "665e051375594d11e58e434231bd06775dbdc560",
        )

    def test_current_repository_watermark_is_pr120(self):
        repo = self.current["repository_state"]
        self.assertEqual(repo["observed_head"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 120)
        self.assertEqual(repo["open_pull_requests_observed"], [])
        self.assertEqual(repo["exact_source_ci_run_id"], 30194713992)
        self.assertEqual(repo["exact_source_ci_conclusion"], "success")

    def test_run16_artifact_and_plan_are_exact(self):
        anchors = self.current["evidence_anchors"]
        self.assertEqual(anchors["workflow_run_id"], RUN_ID)
        self.assertEqual(anchors["artifact_id"], ARTIFACT_ID)
        self.assertEqual(anchors["artifact_manifest_payloads_verified"], 29)
        self.assertEqual(anchors["artifact_manifest_payload_failures"], 0)

        api = self.current["collector_demo_api"]
        self.assertEqual(api["observation"]["reviewed_commit"], REVIEWED)
        self.assertFalse(api["observation"]["azure_mutation_performed"])
        self.assertEqual(
            api["accepted_what_if"]["change_counts"],
            {"Ignore": 24, "Modify": 3, "NoChange": 3, "Create": 0, "Delete": 0, "Replace": 0},
        )
        self.assertEqual(api["predeployment_state"]["backend_pool_address_count"], 0)
        self.assertEqual(api["predeployment_state"]["vm_extension_provisioning_state"], "Failed")

    def test_deployment_and_cost_remain_blocked(self):
        api = self.current["collector_demo_api"]
        self.assertTrue(api["deployment"]["decision_ready"])
        self.assertFalse(api["deployment"]["authorized"])
        self.assertFalse(api["deployment"]["performed"])
        self.assertEqual(api["deployment"]["service_restored"], "not_verified")
        self.assertEqual(api["cost_and_budget"]["current_billing_cost"], "not_observed")
        self.assertEqual(
            api["cost_and_budget"]["remaining_Azure_for_Students_credit"],
            "not_observed",
        )
        self.assertEqual(api["source_binding"]["deployment_source_decision"], "unresolved")

    def test_gate_and_handoff_follow_index(self):
        self.assertEqual(
            self.gate["evidence_inputs"]["canonical_state_index"],
            ".project/state-index.json",
        )
        self.assertEqual(
            self.gate["evidence_inputs"]["canonical_current_view"],
            ".project/current-reality-v2.json",
        )
        for marker in (
            MAIN,
            str(RUN_ID),
            str(ARTIFACT_ID),
            REVIEWED,
            "artifact_verified != deployment_authorized",
            "pull request merge authorized: false",
        ):
            self.assertIn(marker, self.handoff)

    def test_no_execution_authority_is_manufactured(self):
        authority = self.current["authority"]
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_authorized",
            "azure_authentication_authorized",
            "azure_query_authorized",
            "azure_mutation_authorized",
            "deployment_authorized",
            "verify_operation_authorized",
            "transaction_replay_authorized",
            "rollback_authorized",
            "cleanup_authorized",
            "rbac_mutation_authorized",
        ):
            self.assertFalse(authority[key], key)

        promotion_authority = self.promotion["authority"]
        self.assertFalse(promotion_authority["deployment_authorized"])
        self.assertFalse(promotion_authority["workflow_dispatch_authorized"])


if __name__ == "__main__":
    unittest.main()
