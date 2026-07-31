import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIVE_API = "https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/demo/run"
DEPLOYMENT_RECORD = (
    ROOT
    / ".project"
    / "evidence"
    / "servicetracer-demo-api-deployment-run-30661015789.json"
)
HISTORICAL_COLLECTOR_RECORD = (
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
            "independent_demo_api_live_default_pending_github_pages_verification",
        )
        self.assertEqual(
            config["evidence_anchor"],
            ".project/evidence/servicetracer-demo-api-deployment-run-30661015789.json",
        )

    def test_current_deployment_record_proves_bounded_health_not_full_browser_path(self) -> None:
        record = json.loads(DEPLOYMENT_RECORD.read_text(encoding="utf-8"))
        self.assertEqual(record["source"]["accepted_plan_run_id"], 30660575435)
        self.assertEqual(record["source"]["workflow_run_id"], 30661015789)
        self.assertEqual(record["source"]["head_sha"], "ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3")
        self.assertEqual(record["artifact"]["artifact_id"], 8805241142)
        self.assertTrue(record["artifact"]["internal_manifest_verified"])
        self.assertEqual(record["artifact"]["internal_manifest_entries"], 45)
        self.assertEqual(record["deployment"]["provisioning_state"], "Succeeded")
        self.assertEqual(record["post_deployment_inventory"]["vm_power_state"], "VM running")
        self.assertEqual(
            record["post_deployment_inventory"]["vm_extension_provisioning_state"],
            "Succeeded",
        )
        runtime = record["runtime_evidence"]
        self.assertEqual(runtime["local_process_health"]["status"], "healthy")
        self.assertEqual(runtime["public_fqdn_health_from_vm_guest"]["status"], "healthy")
        self.assertTrue(runtime["public_fqdn_health_from_vm_guest"]["azure_host"]["verified"])
        self.assertFalse(runtime["external_browser_path_verified"])
        self.assertFalse(runtime["cors_verified"])
        self.assertFalse(runtime["transaction_post_verified"])
        self.assertTrue(record["authorization"]["attempt_consumed"])
        self.assertFalse(record["authorization"]["rerun_authorized"])
        self.assertFalse(record["authorization"]["cleanup_authorized"])

    def test_historical_collector_record_remains_preserved(self) -> None:
        record = json.loads(HISTORICAL_COLLECTOR_RECORD.read_text(encoding="utf-8"))
        self.assertEqual(record["source"]["workflow_run_id"], 30196388398)
        self.assertEqual(record["artifact"]["artifact_id"], 8630260279)
        self.assertFalse(record["workflow_conclusion"]["deployment_failed"])
        self.assertFalse(record["workflow_conclusion"]["service_failed"])

    def test_browser_verifier_uses_real_pages_without_query_override(self) -> None:
        source = VERIFIER.read_text(encoding="utf-8")
        self.assertIn("sourceConfig.live_demo_api_url", source)
        self.assertIn(LIVE_API, source)
        self.assertIn("actual_github_pages_deployment_verified: true", source)
        self.assertIn("fixture_fallback_used: false", source)
        self.assertIn("frontend used fixture fallback", source)
        self.assertIn("transaction response must contain exactly 20 attempts", source)
        self.assertIn("exact_root_cause_claimed", source)
        self.assertNotIn("?api=", source)


if __name__ == "__main__":
    unittest.main()
