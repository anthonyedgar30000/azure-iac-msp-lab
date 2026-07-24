import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class FrontendApiDemoLabIntegrationTests(unittest.TestCase):
    def test_candidate_api_configuration_is_bounded_and_not_default(self) -> None:
        config = json.loads((ROOT / "docs" / "report-source.json").read_text(encoding="utf-8"))
        self.assertEqual(config["schema_version"], "servicetracer.report-source.v1")
        self.assertEqual(config["activation_status"], "candidate_frontend_integration")
        self.assertEqual(config["live_demo_api_url"], "")
        self.assertTrue(config["candidate_demo_api_url"].startswith("https://"))
        self.assertTrue(config["candidate_demo_api_url"].endswith("/api/demo/run"))
        self.assertEqual(config["fallback_report_url"], "technician-handoff-report.json")
        self.assertIn("explicit ?api= URL", config["claim_boundary"])
        self.assertIn("does not prove", config["claim_boundary"])

    def test_frontend_checks_health_and_does_not_hardcode_localization(self) -> None:
        app = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")
        self.assertIn("validateDemoApiHealth", app)
        self.assertIn("deriveDemoApiHealthUrl", app)
        self.assertIn("localizationIsStable", app)
        self.assertIn("Repeat the bounded sample before localizing", app)
        self.assertIn("const queryApiUrl = query.get('api');", app)
        self.assertIn("state.demoApiUrl = queryApiUrl || config.live_demo_api_url || '';", app)
        self.assertIn("technician_workflow_hidden_until_stable_backend_comparison", (
            ROOT / ".project" / "reconciliations" / "frontend-api-demo-lab-integration.json"
        ).read_text(encoding="utf-8"))
        self.assertNotIn("setNodeState(elements.vpn01Node, 'healthy');", app)
        self.assertNotIn("setNodeState(elements.vpn02Node, 'failed');", app)

    def test_deferred_issues_remain_unresolved_and_authority_is_fail_closed(self) -> None:
        record = json.loads((
            ROOT / ".project" / "reconciliations" / "frontend-api-demo-lab-integration.json"
        ).read_text(encoding="utf-8"))
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
