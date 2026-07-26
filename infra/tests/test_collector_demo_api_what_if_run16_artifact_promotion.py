from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RECORD = (
    ROOT
    / ".project"
    / "reconciliations"
    / "collector-demo-api-what-if-run16-artifact-promotion-20260726.json"
)
REVIEW = ROOT / "docs" / "reviews" / "collector-demo-api-what-if-run16-artifact-promotion.md"


class CollectorDemoApiWhatIfRun16ArtifactPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(RECORD.read_text(encoding="utf-8"))
        cls.review = REVIEW.read_text(encoding="utf-8")

    def test_exact_run_job_and_source_are_promoted(self):
        run = self.record["workflow_run"]
        self.assertEqual(run["run_number"], 16)
        self.assertEqual(run["run_id"], 30192970923)
        self.assertEqual(run["run_attempt"], 1)
        self.assertEqual(run["reviewed_commit"], "8de1f61f8a0ea06dcf94b94c798edde2aace357d")
        self.assertEqual(run["job"]["job_id"], 89769401839)
        self.assertEqual(run["job"]["conclusion"], "success")
        self.assertFalse(run["azure_mutations_performed"])
        self.assertFalse(run["transaction_replay_performed"])

    def test_artifact_integrity_is_exact_and_complete(self):
        artifact = self.record["artifact"]
        self.assertEqual(artifact["artifact_id"], 8629191915)
        self.assertEqual(artifact["name"], "collector-demo-api-30192970923-1")
        self.assertEqual(
            artifact["github_digest"],
            "sha256:57fe05c113d0fefc86437a4aa247b920dc6a02680a1c2bfe8e67873fe7612e6e",
        )
        self.assertTrue(artifact["zip_digest_matches_github"])
        self.assertEqual(artifact["archive_entry_count"], 31)
        self.assertEqual(artifact["manifest_payload_count"], 29)
        self.assertEqual(artifact["manifest_payload_hashes_verified"], 29)
        self.assertEqual(artifact["manifest_payload_hash_failures"], 0)

    def test_accepted_plan_remains_narrow_and_non_destructive(self):
        plan = self.record["accepted_what_if_plan"]
        self.assertEqual(plan["total_entries"], 30)
        self.assertEqual(
            plan["change_counts"],
            {
                "Ignore": 24,
                "Modify": 3,
                "NoChange": 3,
                "Create": 0,
                "Delete": 0,
                "Replace": 0,
            },
        )
        self.assertEqual(len(plan["approved_modifications"]), 3)
        self.assertEqual(plan["forbidden_changes"], [])
        self.assertEqual(plan["base_infrastructure_modifications"], [])
        self.assertEqual(plan["collector_vm_modifications"], [])
        self.assertEqual(plan["collector_nic_modifications"], [])
        self.assertFalse(plan["managed_web_resources_proposed"])

        resources = {item["resource_name"]: item for item in plan["approved_modifications"]}
        extension = resources["vm-stcollector-mst-dev/servicetracer-demo-api"]
        self.assertEqual(extension["force_update_tag"], "8de1f61f8a0ea06dcf94b94c798edde2aace357d")
        self.assertEqual(extension["publisher"], "Microsoft.Azure.Extensions")
        self.assertEqual(extension["handler_type"], "CustomScript")

        backend = resources["lb-st-demo-api-mst-dev/be-st-demo-api"]
        self.assertEqual(backend["backend_name"], "collector")
        self.assertEqual(backend["backend_ip"], "10.20.40.10")
        self.assertEqual(backend["virtual_network_name"], "vnet-onprem-sim-mst-dev")

    def test_sensitive_identity_values_are_fingerprinted_not_raw(self):
        identity = self.record["azure_identity_context"]
        for key in (
            "subscription_id_sha256",
            "tenant_id_sha256",
            "service_principal_object_id_sha256",
        ):
            self.assertRegex(identity[key], r"^[0-9a-f]{64}$")

        serialized = json.dumps(self.record)
        for raw_identifier in (
            "9fc6081d-0d0e-49b8-a181-b1a142d02f7c",
            "c46b18cd-b7f5-4b45-95cb-cccb37283116",
            "5a60e381-9d40-488e-9b01-21fa5dbe0a96",
        ):
            self.assertNotIn(raw_identifier, serialized)

    def test_deployment_and_merge_authority_remain_false(self):
        authority = self.record["authority"]
        for key in (
            "pull_request_merge_authorized",
            "azure_query_authorized",
            "workflow_dispatch_authorized",
            "deployment_authorized",
            "verify_operation_authorized",
            "transaction_replay_authorized",
            "rollback_authorized",
            "cleanup_authorized",
            "rbac_mutation_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(authority[key])

        self.assertEqual(
            self.record["next_gate"]["deployment_status"],
            "blocked_pending_separate_exact_source_authorization",
        )

    def test_review_preserves_claim_and_source_boundaries(self):
        for statement in (
            "artifact_verified != deployment_authorized",
            "deployment_decision_ready != deployment_authorized",
            "WhatIf_accepted != service_restored",
            "deploying accepted source != deploying current main",
            "not_observed != false",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, self.review)


if __name__ == "__main__":
    unittest.main()
