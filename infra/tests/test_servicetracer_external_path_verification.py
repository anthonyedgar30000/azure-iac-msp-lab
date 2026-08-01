from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION = (
    ROOT
    / ".project"
    / "authorizations"
    / "servicetracer-external-validation-20260801.json"
)
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-live-verify.yml"
BROWSER_VERIFIER = ROOT / "scripts" / "verify_servicetracer_external_path.mjs"


class ServiceTracerExternalPathVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.browser = BROWSER_VERIFIER.read_text(encoding="utf-8")

    def test_authority_is_consumed_and_non_renewing(self) -> None:
        self.assertEqual(self.record["source_instruction"], "Proceed")
        self.assertEqual(
            self.record["operation"],
            "read_only_external_service_validation",
        )
        authority = self.record["authorization"]
        self.assertEqual(authority["status"], "consumed_success")
        self.assertFalse(authority["active_for_one_attempt"])
        self.assertTrue(authority["attempt_consumed"])
        self.assertTrue(authority["non_renewing"])
        self.assertFalse(authority["retry_authorized"])
        self.assertFalse(authority["manual_dispatch_authorized"])

    def test_successful_attempt_and_artifact_are_exactly_recorded(self) -> None:
        execution = self.record["execution"]
        self.assertEqual(execution["pull_request"], 263)
        self.assertEqual(execution["workflow_run_id"], 30693434244)
        self.assertEqual(execution["workflow_run_attempt"], 1)
        self.assertEqual(execution["workflow_conclusion"], "success")
        self.assertEqual(
            execution["pull_request_head_sha"],
            "0ca222703585f6e0403957f096f424d0d2a22b91",
        )
        self.assertEqual(
            execution["pull_request_merge_checkout_sha"],
            "150a4b5d895b2be426180540316e8588520545c3",
        )
        self.assertFalse(execution["checkout_was_exact_pull_request_head"])
        self.assertEqual(execution["artifact_id"], 8816461373)
        self.assertEqual(
            execution["artifact_digest"],
            "sha256:f162c7a266c35146d827e05cb8b70db6d0438599149e99affe5cbfb5f18d4b6a",
        )
        self.assertTrue(execution["artifact_manifest_verified"])

    def test_observed_outcome_preserves_uncertainty(self) -> None:
        outcome = self.record["observed_outcome"]
        self.assertTrue(outcome["github_pages_published_and_rendered"])
        self.assertFalse(outcome["fixture_fallback_used"])
        self.assertEqual(outcome["health_http_status"], 200)
        self.assertEqual(outcome["allowed_origin_preflight_http_status"], 204)
        self.assertEqual(outcome["transaction_http_status"], 200)
        self.assertTrue(outcome["request_header_and_body_ids_matched"])
        self.assertTrue(outcome["azure_runtime_identity_matched"])
        self.assertEqual(outcome["disallowed_origin_http_status"], 403)
        self.assertEqual(outcome["sample_attempts"], 20)
        self.assertEqual(outcome["successful_downstream_transactions"], 0)
        self.assertEqual(outcome["failed_downstream_transactions"], 20)
        self.assertEqual(outcome["transport_errors"], 0)
        self.assertEqual(outcome["backend_counts"], {"VPN-02": 20})
        self.assertFalse(outcome["stable_backend_localization"])
        self.assertFalse(outcome["exact_root_cause_claimed"])

    def test_workflow_requires_fresh_authority_and_exact_head(self) -> None:
        self.assertNotIn("\n  workflow_dispatch:\n", self.workflow)
        self.assertIn(
            "ref: ${{ github.event.pull_request.head.sha }}",
            self.workflow,
        )
        self.assertIn("Evaluate one-shot authority", self.workflow)
        self.assertIn("exact_head_checkout", self.workflow)
        self.assertIn(
            "if: steps.authority.outputs.authorized == 'true'",
            self.workflow,
        )
        self.assertIn("skipped_no_active_authority", self.workflow)
        self.assertIn("A new explicit authorization is required", self.workflow)

    def test_workflow_has_no_azure_control_plane_or_mutation_authority(self) -> None:
        self.assertIn("permissions:\n  contents: read", self.workflow)
        self.assertNotIn("id-token: write", self.workflow)
        self.assertNotIn("azure/login", self.workflow)
        self.assertNotIn("az login", self.workflow)
        self.assertNotIn("az deployment", self.workflow)
        self.assertNotIn("az vm run-command", self.workflow)
        self.assertNotIn("az role assignment", self.workflow)
        self.assertIn("bounded_live_post_requests\": 1", self.workflow)
        self.assertIn("bounded_live_post_attempts\": 20", self.workflow)

    def test_workflow_targets_current_external_path(self) -> None:
        self.assertIn(
            "https://anthonyedgar30000.github.io/azure-iac-msp-lab/",
            self.workflow,
        )
        self.assertIn(
            "https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/demo/run",
            self.workflow,
        )
        self.assertIn("rg-st-demo-api-dev-westus2", self.workflow)
        self.assertIn("vm-st-demo-api-mst-dev", self.workflow)
        self.assertIn(
            "ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3",
            self.workflow,
        )

    def test_browser_verifier_preserves_evidence_boundaries(self) -> None:
        self.assertIn("transactions.length === 20", self.browser)
        self.assertIn("exactAzureIdentity", self.browser)
        self.assertIn("response body and header request IDs differ", self.browser)
        self.assertIn("exact_root_cause_claimed === false", self.browser)
        self.assertIn("frontend used fixture fallback", self.browser)
        self.assertIn("stable_localization != exact_root_cause", self.browser)
        self.assertNotIn("azure/login", self.browser)
        self.assertNotIn("az deployment", self.browser)


if __name__ == "__main__":
    unittest.main()
