import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIVE_API = "https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/demo/run"


class FrontendApiDemoLabIntegrationTests(unittest.TestCase):
    def test_deployed_api_is_the_default_with_fail_closed_fixture_fallback(self) -> None:
        config = json.loads((ROOT / "docs" / "report-source.json").read_text(encoding="utf-8"))
        self.assertEqual(config["schema_version"], "servicetracer.report-source.v1")
        self.assertEqual(
            config["activation_status"],
            "independent_demo_api_live_default_pending_github_pages_verification",
        )
        self.assertEqual(config["live_demo_api_url"], LIVE_API)
        self.assertEqual(config["candidate_demo_api_url"], LIVE_API)
        self.assertEqual(config["fallback_report_url"], "technician-handoff-report.json")
        self.assertEqual(
            config["evidence_anchor"],
            ".project/evidence/servicetracer-demo-api-deployment-run-30661015789.json",
        )
        self.assertIn("normal frontend", config["claim_boundary"])
        self.assertIn("fail-closed fallback", config["claim_boundary"])
        self.assertIn("does not by itself prove", config["claim_boundary"])

    def test_frontend_checks_health_and_does_not_hardcode_localization(self) -> None:
        app = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")
        self.assertIn("validateDemoApiHealth", app)
        self.assertIn("deriveDemoApiHealthUrl", app)
        self.assertIn("localizationIsStable", app)
        self.assertIn("Repeat the bounded sample before localizing", app)
        self.assertIn("new URLSearchParams(window.location.search).get('api')", app)
        self.assertIn("state.demoApiUrl = queryApiUrl || config.live_demo_api_url || '';", app)
        self.assertIn(
            "technician_workflow_hidden_until_stable_backend_comparison",
            (
                ROOT
                / ".project"
                / "reconciliations"
                / "frontend-api-demo-lab-integration.json"
            ).read_text(encoding="utf-8"),
        )
        self.assertNotIn("setNodeState(elements.vpn01Node, 'healthy');", app)
        self.assertNotIn("setNodeState(elements.vpn02Node, 'failed');", app)

    def test_deferred_issues_remain_unresolved_and_historical_authority_is_preserved(self) -> None:
        record = json.loads(
            (
                ROOT
                / ".project"
                / "reconciliations"
                / "frontend-api-demo-lab-integration.json"
            ).read_text(encoding="utf-8")
        )
        statuses = {item["issue"]: item["status"] for item in record["deferred_operational_issues"]}
        self.assertEqual(set(statuses.values()), {"deferred_not_resolved"})
        self.assertFalse(record["authority"]["pull_request_merge_authorized"])
        self.assertFalse(record["authority"]["workflow_dispatch_authorized"])
        self.assertFalse(record["authority"]["azure_authentication_authorized"])
        self.assertFalse(record["authority"]["azure_mutations_authorized"])
        self.assertFalse(record["validation"]["browser_rendering_verified"])
        self.assertFalse(record["validation"]["live_twenty_attempt_sample_verified"])


if __name__ == "__main__":
    unittest.main()
