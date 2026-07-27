from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMOTION_PATH = ROOT / ".project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json"
AUTHORIZATION_PATH = ROOT / ".project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json"
STATE_INDEX_PATH = ROOT / ".project/state-index.json"


class CollectorProvenancePreflightRun1PromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.promotion = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
        self.authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        self.state_index = json.loads(STATE_INDEX_PATH.read_text(encoding="utf-8"))

    def test_exact_artifact_identity_and_integrity_are_bound(self) -> None:
        artifact = self.promotion["artifact"]
        self.assertEqual(self.promotion["preflight_identity"]["workflow_run_id"], 30206242759)
        self.assertEqual(artifact["artifact_id"], 8633143093)
        self.assertEqual(
            artifact["github_digest"],
            "sha256:2f8a63d18d6c2e07e86cc607c49d111e6b788d40637b2adcd30b1d5ce05de902",
        )
        self.assertTrue(artifact["independently_verified_digest"])
        self.assertEqual(artifact["manifest_payloads_verified"], 26)
        self.assertEqual(artifact["manifest_payload_failures"], 0)
        self.assertFalse(artifact["raw_subscription_or_tenant_identifiers_promoted"])

    def test_exact_source_and_plan_are_fail_closed(self) -> None:
        self.assertEqual(
            self.promotion["preflight_identity"]["exact_reviewed_source"],
            "1677606ded960c951fa37f0fdbfae50ba4b3cc34",
        )
        self.assertFalse(
            self.promotion["preflight_identity"]["deployment_payload_difference_observed"]
        )
        what_if = self.promotion["what_if"]
        self.assertEqual(what_if["status"], "accepted_isolated_collector_api_changes")
        self.assertEqual(
            what_if["change_counts"],
            {"Ignore": 24, "Modify": 3, "NoChange": 3, "Create": 0, "Delete": 0, "Replace": 0},
        )
        self.assertEqual(what_if["forbidden_changes"], [])
        self.assertEqual(what_if["base_infrastructure_modifications"], [])
        self.assertEqual(what_if["collector_vm_modifications"], [])
        self.assertEqual(what_if["collector_nic_modifications"], [])
        self.assertFalse(what_if["managed_web_resources_proposed"])
        self.assertFalse(what_if["deployment_authorized_by_preflight"])
        self.assertFalse(what_if["azure_mutation_performed"])

    def test_cost_is_observed_without_claiming_remaining_credit(self) -> None:
        cost = self.promotion["cost"]
        self.assertAlmostEqual(cost["amount"], 4.03203831168191)
        self.assertEqual(cost["currency"], "CAD")
        self.assertEqual(cost["remaining_azure_for_students_credit"], "not_observed")

    def test_deployment_grant_is_exact_finite_and_nonrenewing(self) -> None:
        action = self.authorization["action"]
        self.assertEqual(action["operation"], "deploy")
        self.assertEqual(action["reviewed_commit"], "1677606ded960c951fa37f0fdbfae50ba4b3cc34")
        self.assertEqual(action["resource_group"], "rg-servicetracer-dev-westus2")
        self.assertEqual(action["location"], "westus2")
        self.assertEqual(
            action["confirmation"],
            "COLLECTOR-DEMO-API:deploy:rg-servicetracer-dev-westus2:st-demo-api-aeg30000",
        )
        self.assertEqual(self.authorization["consumption"]["attempt_limit"], 1)
        self.assertFalse(self.authorization["consumption"]["renewable"])
        self.assertFalse(self.authorization["consumption"]["transferable"])
        self.assertFalse(self.authorization["verification_authority"]["automatic_retry"])
        self.assertFalse(self.authorization["rollback_authority"]["automatic_rollback"])
        self.assertFalse(self.authorization["rollback_authority"]["manual_rollback"])

    def test_mutation_scope_contains_only_three_approved_targets(self) -> None:
        scope = self.authorization["authorized_mutation_scope"]
        self.assertEqual(scope["creates"], 0)
        self.assertEqual(scope["deletes"], 0)
        self.assertEqual(scope["replaces"], 0)
        self.assertEqual(len(scope["modifies"]), 3)
        self.assertFalse(scope["base_infrastructure_mutation_authorized"])
        self.assertFalse(scope["collector_vm_mutation_authorized"])
        self.assertFalse(scope["collector_nic_mutation_authorized"])
        self.assertFalse(scope["microsoft_web_mutation_authorized"])
        self.assertFalse(scope["rbac_mutation_authorized"])
        self.assertFalse(scope["cleanup_authorized"])

    def test_state_index_preserves_preflight_and_resolves_expired_grant(self) -> None:
        self.assertEqual(
            self.state_index["latest_verified_reconciliation"],
            ".project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json",
        )
        self.assertEqual(
            self.state_index["latest_deployment_authorization"],
            ".project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json",
        )
        self.assertIsNone(self.state_index["active_deployment_authorization"])
        self.assertEqual(
            self.state_index["latest_authorization_resolution"],
            ".project/reconciliations/post-pr137-provenance-authority-expiry-20260727.json",
        )


if __name__ == "__main__":
    unittest.main()
