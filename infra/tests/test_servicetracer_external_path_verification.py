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
    def test_authority_is_one_shot_external_only(self) -> None:
        record = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
        self.assertEqual(record["source_instruction"], "Proceed")
        self.assertEqual(record["operation"], "read_only_external_service_validation")
        authority = record["authorization"]
        self.assertTrue(authority["active_for_one_attempt"])
        self.assertTrue(authority["non_renewing"])
        self.assertTrue(authority["consumed_when_attempt_starts"])
        self.assertFalse(authority["retry_authorized"])
        permitted = record["permitted_actions"]
        self.assertEqual(permitted["bounded_api_post_count"], 1)
        self.assertEqual(permitted["bounded_transaction_attempts"], 20)
        self.assertTrue(all(record["prohibited_actions"].values()))

    def test_workflow_has_no_azure_control_plane_or_mutation_authority(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", source)
        self.assertNotIn("id-token: write", source)
        self.assertNotIn("azure/login", source)
        self.assertNotIn("az login", source)
        self.assertNotIn("az deployment", source)
        self.assertNotIn("az vm run-command", source)
        self.assertNotIn("az role assignment", source)
        self.assertNotIn("workflow_dispatch_performed\": true", source)
        self.assertIn("bounded_live_post_requests\": 1", source)
        self.assertIn("bounded_live_post_attempts\": 20", source)

    def test_workflow_targets_current_external_path(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "https://anthonyedgar30000.github.io/azure-iac-msp-lab/",
            source,
        )
        self.assertIn(
            "https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/demo/run",
            source,
        )
        self.assertIn("rg-st-demo-api-dev-westus2", source)
        self.assertIn("vm-st-demo-api-mst-dev", source)
        self.assertIn("ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3", source)

    def test_browser_verifier_preserves_evidence_boundaries(self) -> None:
        source = BROWSER_VERIFIER.read_text(encoding="utf-8")
        self.assertIn("transactions.length === 20", source)
        self.assertIn("exactAzureIdentity", source)
        self.assertIn("response body and header request IDs differ", source)
        self.assertIn("exact_root_cause_claimed === false", source)
        self.assertIn("frontend used fixture fallback", source)
        self.assertIn("stable_localization != exact_root_cause", source)
        self.assertNotIn("azure/login", source)
        self.assertNotIn("az deployment", source)


if __name__ == "__main__":
    unittest.main()
