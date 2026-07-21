from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "infra"
MODULE = (INFRA / "modules" / "report_publication.bicep").read_text(
    encoding="utf-8"
)
MAIN = (INFRA / "main.bicep").read_text(encoding="utf-8")
DEV = (INFRA / "main.dev.bicepparam").read_text(encoding="utf-8")


class ReportPublicationInfrastructureTests(unittest.TestCase):
    def test_endpoint_is_dedicated_and_uses_secure_write_authentication(self) -> None:
        self.assertIn("kind: 'StorageV2'", MODULE)
        self.assertIn("allowBlobPublicAccess: false", MODULE)
        self.assertIn("allowSharedKeyAccess: false", MODULE)
        self.assertIn("defaultToOAuthAuthentication: true", MODULE)
        self.assertIn("minimumTlsVersion: 'TLS1_2'", MODULE)
        self.assertIn("supportsHttpsTrafficOnly: true", MODULE)

    def test_static_endpoint_has_bounded_browser_access(self) -> None:
        self.assertIn("staticWebsite", MODULE)
        self.assertIn("allowedOrigins: allowedOrigins", MODULE)
        self.assertIn("'GET'", MODULE)
        self.assertIn("'HEAD'", MODULE)
        self.assertIn("'OPTIONS'", MODULE)
        self.assertNotIn("allowedOrigins: [\n            '*'", MODULE)
        self.assertIn("isVersioningEnabled: true", MODULE)
        self.assertIn("deleteRetentionPolicy", MODULE)

    def test_collector_identity_receives_blob_data_role(self) -> None:
        self.assertIn("collectorPrincipalId", MODULE)
        self.assertIn("principalType: 'ServicePrincipal'", MODULE)
        self.assertIn("ba92f5b4-2d11-453d-a403-e96b0029c9fe", MODULE)
        self.assertIn("scope: reportStorage", MODULE)

    def test_endpoint_requires_collector_and_remains_opt_in(self) -> None:
        self.assertIn(
            "deployPublicReportEndpoint && deployOperationsCollector",
            MAIN,
        )
        self.assertIn("if (deployReportPublicationResources)", MAIN)
        self.assertIn(
            "collectorPrincipalId: operationsCollector.outputs.collectorPrincipalId",
            MAIN,
        )
        self.assertIn("param deployPublicReportEndpoint = false", DEV)
        self.assertIn("https://anthonyedgar30000.github.io", DEV)

    def test_main_exports_browser_report_url(self) -> None:
        self.assertIn("output publicReportUrl string", MODULE)
        self.assertIn("output publicReportUrl string", MAIN)
        self.assertIn("reports/technician-handoff-report.json", MODULE)


if __name__ == "__main__":
    unittest.main()
