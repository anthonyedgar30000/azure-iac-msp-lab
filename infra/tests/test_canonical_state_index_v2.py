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
RUN19 = ROOT / ".project/reconciliations/collector-provenance-deployment-run19-20260726.json"
AUTH = ROOT / ".project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json"

MAIN = "bd1ef50451c85d9f0e9e77c9ac54882d44940933"
MERGED_SOURCE = "db2c95d279f06f379c13b4cd8664518eda417843"
DEPLOYMENT_SOURCE = "1677606ded960c951fa37f0fdbfae50ba4b3cc34"
COLLECTOR = "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run"
PREFLIGHT = ".project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json"
RUN19_PATH = ".project/reconciliations/collector-provenance-deployment-run19-20260726.json"
PRIOR_RESOLUTION = ".project/reconciliations/post-pr137-provenance-authority-expiry-20260727.json"


class CanonicalStateIndexV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.current = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
        cls.gate = json.loads(GATE.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.run19 = json.loads(RUN19.read_text(encoding="utf-8"))
        cls.auth = json.loads(AUTH.read_text(encoding="utf-8"))

    def test_index_selects_current_records_and_no_active_grant(self):
        self.assertEqual(self.index["canonical_current_reality"], ".project/current-reality-v2.json")
        self.assertEqual(self.index["latest_verified_reconciliation"], PREFLIGHT)
        self.assertEqual(self.index["latest_deployment_reconciliation"], RUN19_PATH)
        self.assertEqual(self.index["latest_authorization_resolution"], RUN19_PATH)
        self.assertEqual(self.index["prior_authorization_resolution"], PRIOR_RESOLUTION)
        self.assertIsNone(self.index["active_deployment_authorization"])
        self.assertIn("consumed_deployment_authorization", self.index)
        self.assertFalse(self.index["legacy_compatibility_snapshots"][0]["authoritative_for_current_operations"])
        self.assertEqual(
            self.legacy["repository_state"]["observed_head"],
            "665e051375594d11e58e434231bd06775dbdc560",
        )

    def test_current_repository_watermark_is_pr138(self):
        repo = self.current["repository_state"]
        self.assertEqual(repo["observed_head"], MAIN)
        self.assertEqual(repo["latest_merged_pull_request"], 138)
        self.assertEqual(repo["open_pull_requests_observed"], [139])
        self.assertEqual(repo["exact_source_head"], MERGED_SOURCE)
        self.assertEqual(repo["exact_source_ci_run_id"], 30267618707)
        self.assertEqual(repo["exact_source_ci_conclusion"], "success")
        self.assertEqual(repo["merge_commit_ci"], "not_observed")

    def test_run19_is_failed_closed_and_authority_consumed(self):
        deployment = self.current["collector_demo_api"]["deployment"]
        self.assertTrue(deployment["performed"])
        self.assertFalse(deployment["succeeded"])
        self.assertTrue(deployment["network_reconciliation_succeeded"])
        self.assertFalse(deployment["extension_provisioning_succeeded"])
        self.assertTrue(deployment["authority_consumed"])
        self.assertEqual(self.auth["consumption"]["status"], "consumed")
        self.assertEqual(self.auth["consumption"]["deployment_run_id"], 30224770178)
        self.assertFalse(self.auth["consumption"]["renewable"])
        self.assertFalse(self.auth["consumption"]["transferable"])
        self.assertFalse(self.auth["verification_authority"]["automatic_retry"])

    def test_source_and_runtime_boundaries_remain_visible(self):
        api = self.current["collector_demo_api"]
        self.assertEqual(api["source_binding"]["attempted_source"], DEPLOYMENT_SOURCE)
        self.assertTrue(api["source_binding"]["files_and_environment_replaced_with_attempted_source"])
        self.assertEqual(api["source_binding"]["running_process_source_after_run19"], "not_observed")
        self.assertFalse(api["source_binding"]["attempted_source_runtime_verified"])
        self.assertEqual(api["source_binding"]["current_main"], MAIN)
        self.assertEqual(api["frontend_binding"]["configured_endpoint"], COLLECTOR)
        self.assertFalse(api["frontend_binding"]["browser_transaction_verified"])

    def test_run19_artifact_and_failure_are_locked(self):
        self.assertEqual(self.run19["execution"]["workflow_run_id"], 30224770178)
        self.assertEqual(self.run19["artifact"]["manifest_payloads_verified"], 44)
        self.assertEqual(self.run19["artifact"]["manifest_payload_failures"], 0)
        self.assertEqual(
            self.run19["failure_classification"]["status"],
            "deterministic_repository_lifecycle_defect",
        )
        self.assertFalse(self.run19["authorization"]["automatic_retry_authorized"])
        self.assertFalse(self.run19["authorization"]["rollback_authorized"])

    def test_gate_requires_new_authority_after_repository_repair(self):
        criteria = {item["criterion_id"]: item for item in self.gate["p0"]["criteria"]}
        self.assertFalse(criteria["p0-collector-deployment"]["complete"])
        self.assertFalse(criteria["p0-runtime-contract"]["complete"])
        self.assertFalse(criteria["p0-browser-demonstration"]["complete"])
        self.assertEqual(self.gate["evidence_inputs"]["current_main"], MAIN)
        self.assertEqual(self.gate["evidence_inputs"]["active_reconciliation_pull_request"], 139)
        self.assertIn("failed_attempt != authorization_to_retry", self.handoff)
        self.assertIn("PR #139 merge: unauthorized", self.handoff)

    def test_no_azure_or_merge_authority_is_manufactured(self):
        authority = self.current["authority"]
        self.assertTrue(authority["restart_repair_repository_change_authorized"])
        self.assertFalse(authority["pull_request_merge_authorized"])
        for key in (
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
            "browser_verification_authorized",
        ):
            self.assertFalse(authority[key], key)


if __name__ == "__main__":
    unittest.main()
