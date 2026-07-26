import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs" / "index.html"
MONITOR = ROOT / "docs" / "live-monitor.js"
MONITOR_STYLES = ROOT / "docs" / "live-monitor.css"
SERVER = ROOT / "demo_api" / "standalone_server.py"
INSTALLER = ROOT / "infra" / "scripts" / "install_collector_demo_api.sh"


class FrontendAzureProvenanceMonitorTests(unittest.TestCase):
    def test_monitor_is_loaded_before_application_fetches(self) -> None:
        index = INDEX.read_text(encoding="utf-8")

        self.assertIn('id="live-path-monitor"', index)
        self.assertIn('id="monitor-scope"', index)
        self.assertIn('id="monitor-request-id"', index)
        self.assertIn('href="live-monitor.css"', index)
        self.assertLess(
            index.index('src="live-monitor.js"'),
            index.index('src="app.js"'),
        )
        self.assertIn(
            "The resource group is shown as the governed Azure scope.",
            index,
        )

    def test_frontend_correlates_one_request_without_consuming_the_response(self) -> None:
        source = MONITOR.read_text(encoding="utf-8")

        self.assertIn("const REQUEST_HEADER = 'X-ServiceTracer-Request-ID';", source)
        self.assertIn("window.fetch = async", source)
        self.assertIn("headers.set(REQUEST_HEADER, requestId);", source)
        self.assertIn("response.clone().json()", source)
        self.assertIn("responseRequestId !== requestId", source)
        self.assertIn("setInterval(pollHealth, HEALTH_INTERVAL_MS)", source)
        self.assertIn("identity.verified !== true", source)
        self.assertIn("Frontend ↔ governed collector API live", source)

    def test_api_uses_azure_instance_metadata_without_exposing_subscription_identity(self) -> None:
        source = SERVER.read_text(encoding="utf-8")

        self.assertIn("169.254.169.254/metadata/instance/compute", source)
        self.assertIn('headers={"Metadata": "true"}', source)
        self.assertIn('compute.get("resourceGroupName")', source)
        self.assertIn('compute.get("name")', source)
        self.assertIn('compute.get("location")', source)
        self.assertIn('"verification_source": "azure_instance_metadata_service"', source)
        self.assertIn('payload["request_id"] = request_id', source)
        self.assertIn('payload["azure_host"] = azure_host_identity()', source)
        self.assertIn("Access-Control-Expose-Headers", source)
        self.assertNotIn('compute.get("subscriptionId")', source)
        self.assertNotIn('compute.get("tenantId")', source)

    def test_installer_binds_runtime_identity_to_exact_reviewed_source(self) -> None:
        source = INSTALLER.read_text(encoding="utf-8")

        self.assertIn("SERVICETRACER_DEPLOYED_SOURCE_REF=${SOURCE_REF}", source)
        self.assertIn("identity.get('verified') is not True", source)
        self.assertIn("identity.get('source_ref') != expected_source_ref", source)
        self.assertIn("('resource_group', 'vm_name', 'location')", source)

    def test_monitor_styles_remain_responsive(self) -> None:
        styles = MONITOR_STYLES.read_text(encoding="utf-8")

        self.assertIn(".monitor-path {", styles)
        self.assertIn(".monitor-scope {", styles)
        self.assertIn("@media (max-width: 900px)", styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)


if __name__ == "__main__":
    unittest.main()
