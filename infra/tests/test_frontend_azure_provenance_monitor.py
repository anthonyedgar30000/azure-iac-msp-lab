import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs" / "index.html"
MONITOR = ROOT / "docs" / "live-monitor.js"
MONITOR_STYLES = ROOT / "docs" / "live-monitor.css"
SOURCE_CONFIG = ROOT / "docs" / "report-source.json"
SERVER = ROOT / "demo_api" / "standalone_server.py"
INSTALLER = ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "install.sh"
INDEPENDENT_API = "https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/demo/run"


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

    def test_source_configuration_binds_exact_independent_deployment(self) -> None:
        config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))

        self.assertEqual(config["live_demo_api_url"], INDEPENDENT_API)
        self.assertEqual(config["candidate_demo_api_url"], INDEPENDENT_API)
        self.assertEqual(
            config["activation_status"],
            "independent_demo_api_live_default_pending_github_pages_verification",
        )
        self.assertEqual(
            config["expected_azure_host"],
            {
                "resource_group": "rg-st-demo-api-dev-westus2",
                "vm_name": "vm-st-demo-api-mst-dev",
                "location": "westus2",
                "hosting_model": "dedicated_vm_subproject",
            },
        )
        self.assertEqual(
            config["evidence_anchor"],
            ".project/evidence/servicetracer-demo-api-deployment-run-30661015789.json",
        )

    def test_frontend_accepts_api_assigned_request_id_and_verifies_runtime_identity(self) -> None:
        source = MONITOR.read_text(encoding="utf-8")

        self.assertIn("window.fetch = async", source)
        self.assertIn("response.clone().json()", source)
        self.assertIn("const requestId = payload?.request_id || null;", source)
        self.assertIn("Awaiting API-assigned request ID", source)
        self.assertIn("verifiedRuntimeIdentity(payload)", source)
        self.assertIn("Live API response rejected", source)
        self.assertIn("Live API transaction and Azure runtime identity verified", source)
        self.assertIn("Live API transaction verified · Azure runtime identity remains unverified", source)
        self.assertIn("setInterval(pollHealth, HEALTH_INTERVAL_MS)", source)
        self.assertIn("identity.verified !== true", source)
        self.assertIn("identity.resource_group !== expected.resource_group", source)
        self.assertIn("identity.vm_name !== expected.vm_name", source)
        self.assertIn("identity.location !== expected.location", source)
        self.assertIn("payload.hosting_model !== expected.hosting_model", source)
        self.assertIn("API healthy · Azure runtime identity verified", source)
        self.assertNotIn("const REQUEST_HEADER = 'X-ServiceTracer-Request-ID';", source)
        self.assertNotIn("headers.set(REQUEST_HEADER", source)

    def test_api_uses_azure_instance_metadata_without_exposing_subscription_identity(self) -> None:
        source = SERVER.read_text(encoding="utf-8")

        self.assertIn("169.254.169.254/metadata/instance/compute", source)
        self.assertIn('headers={"Metadata": "true"}', source)
        self.assertIn('compute.get("resourceGroupName")', source)
        self.assertIn('compute.get("name")', source)
        self.assertIn('compute.get("location")', source)
        self.assertIn('"verification_source": "azure_instance_metadata_service"', source)
        self.assertIn('payload["request_id"] = request_id', source)
        self.assertIn('payload["hosting_model"] = HOSTING_MODEL', source)
        self.assertIn('payload["azure_host"] = azure_host_identity()', source)
        self.assertIn("Access-Control-Expose-Headers", source)
        self.assertNotIn('compute.get("subscriptionId")', source)
        self.assertNotIn('compute.get("tenantId")', source)

    def test_installer_binds_runtime_identity_to_exact_deployed_source(self) -> None:
        source = INSTALLER.read_text(encoding="utf-8")

        self.assertIn("SERVICETRACER_DEPLOYED_SOURCE_REF=${SOURCE_REF}", source)
        self.assertIn("SERVICETRACER_HOSTING_MODEL=dedicated_vm_subproject", source)
        self.assertIn("SERVICETRACER_SOURCE_ID=${PUBLIC_FQDN}", source)

    def test_monitor_styles_remain_responsive(self) -> None:
        styles = MONITOR_STYLES.read_text(encoding="utf-8")

        self.assertIn(".monitor-path {", styles)
        self.assertIn(".monitor-scope {", styles)
        self.assertIn("@media (max-width: 900px)", styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)


if __name__ == "__main__":
    unittest.main()
