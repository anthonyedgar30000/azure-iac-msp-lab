import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIVE_API = "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run"
DEPLOYMENT_RECORD = (
    ROOT
    / ".project"
    / "reconciliations"
    / "collector-demo-api-deployment-run18-20260726.json"
)
VERIFIER = ROOT / "scripts" / "verify_frontend_live_default.mjs"


class FrontendLiveDefaultActivationTests(unittest.TestCase):
    def test_default_source_is_exact_deployed_api_with_fixture_fallback(self) -> None:
        config = json.loads((ROOT / "docs" / "report-source.json").read_text(encoding="utf-8"))
        self.assertEqual(config["live_demo_api_url"], LIVE_API)
        self.assertEqual(config["candidate_demo_api_url"], LIVE_API)
        self.assertEqual(config["fallback_report_url"], "technician-handoff-report.json")
        self.assertEqual(
            config["activation_status"],
            "collector_live_default_pending_github_pages_verification",
        )
        self.assertEqual(
            config["evidence_anchor"],
            ".project/reconciliations/collector-demo-api-deployment-run18-20260726.json",
        )

    def test_deployment_record_proves_connection_without_inventing_backend_health(self) -> None:
        record = json.loads(DEPLOYMENT_RECORD.read_text(encoding="utf-8"))
        self.assertEqual(record["source"]["reviewed_commit"], "98b092201053fd3592be157a24de6e623e6b74a6")
        self.assertEqual(record["source"]["workflow_run_id"], 30196388398)
        self.assertEqual(record["artifact"]["artifact_id"], 8630260279)
        self.assertEqual(record["artifact"]["manifest_payloads_verified"], 48)
        self.assertEqual(record["deployment"]["parent_deployment"], "Succeeded")
        self.assertEqual(record["deployment"]["nested_deployment"], "Succeeded")
        self.assertEqual(record["deployment"]["backend_pool"]["address_count"], 1)
        self.assertEqual(record["deployment"]["backend_pool"]["private_ip"], "10.20.40.10")
        self.assertEqual(
            record["deployment"]["collector_vm_extension"]["provisioning_state"],
            "Succeeded",
        )
        self.assertTrue(record["runtime_evidence"]["backend_target_configured"])
        self.assertEqual(record["runtime_evidence"]["transaction_count"], 20)
        self.assertEqual(record["runtime_evidence"]["successful_transactions"], 0)
        self.assertFalse(record["runtime_evidence"]["stable_backend_localization"])
        self.assertFalse(record["runtime_evidence"]["exact_root_cause_claimed"])
        self.assertFalse(record["workflow_conclusion"]["deployment_failed"])
        self.assertFalse(record["workflow_conclusion"]["service_failed"])
        self.assertTrue(record["authority"]["one_shot_deployment_authority_consumed"])
        self.assertFalse(record["authority"]["retry_authorized"])

    def test_browser_verifier_uses_real_pages_without_query_override(self) -> None:
        source = VERIFIER.read_text(encoding="utf-8")
        self.assertIn("sourceConfig.live_demo_api_url", source)
        self.assertIn("actual_github_pages_deployment_verified: true", source)
        self.assertIn("fixture_fallback_used: false", source)
        self.assertIn("frontend used fixture fallback", source)
        self.assertIn("transaction response must contain exactly 20 attempts", source)
        self.assertIn("exact_root_cause_claimed", source)
        self.assertNotIn("?api=", source)


if __name__ == "__main__":
    unittest.main()
