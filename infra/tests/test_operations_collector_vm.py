from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "infra"
MODULE = (INFRA / "modules" / "operations_collector_vm.bicep").read_text(encoding="utf-8")
BOOTSTRAP = (INFRA / "bootstrap" / "collector-cloud-init.yaml").read_text(encoding="utf-8")
MAIN = (INFRA / "main.bicep").read_text(encoding="utf-8")
DEV = (INFRA / "main.dev.bicepparam").read_text(encoding="utf-8")


class OperationsCollectorVmTests(unittest.TestCase):
    def test_private_identity_and_trusted_launch(self) -> None:
        self.assertIn("privateIPAllocationMethod: 'Static'", MODULE)
        self.assertNotIn("publicIPAddresses", MODULE)
        self.assertIn("type: 'SystemAssigned'", MODULE)
        self.assertIn("securityType: 'TrustedLaunch'", MODULE)
        self.assertIn("secureBootEnabled: true", MODULE)
        self.assertIn("vTpmEnabled: true", MODULE)

    def test_managed_evidence_disk_is_preserved(self) -> None:
        self.assertIn("Microsoft.Compute/disks", MODULE)
        self.assertIn("networkAccessPolicy: 'DenyAll'", MODULE)
        self.assertIn("publicNetworkAccess: 'Disabled'", MODULE)
        self.assertIn("deleteOption: 'Detach'", MODULE)

    def test_bootstrap_is_restart_safe_and_secret_free(self) -> None:
        self.assertIn("blkid -s TYPE", BOOTSTRAP)
        self.assertIn("openssl rand -hex 32", BOOTSTRAP)
        self.assertNotIn("SERVICETRACER_COLLECTOR_TOKEN=changeme", BOOTSTRAP)
        self.assertIn("RequiresMountsFor=${DATA_ROOT}", BOOTSTRAP)

    def test_bootstrap_installs_and_verifies_collector(self) -> None:
        self.assertIn("fetch --depth 1 origin", BOOTSTRAP)
        self.assertIn("pip install \"${SOURCE_ROOT}/servicetracer\"", BOOTSTRAP)
        self.assertIn("--tls-cert", BOOTSTRAP)
        self.assertIn("systemctl enable --now servicetracer-collector.service", BOOTSTRAP)
        self.assertIn("/healthz", BOOTSTRAP)

    def test_committed_parameters_avoid_accidental_compute(self) -> None:
        self.assertIn("param deployOperationsCollector = false", DEV)
        self.assertNotIn("collectorAdminSshPublicKey =", DEV)
        self.assertIn("if (deployOperationsCollector)", MAIN)

    def test_cloud_init_placeholders_are_rendered(self) -> None:
        for placeholder in (
            "__COLLECTOR_SOURCE_REPOSITORY__",
            "__COLLECTOR_SOURCE_REF__",
            "__COLLECTOR_PORT__",
            "__COLLECTOR_PRIVATE_IP__",
        ):
            self.assertIn(placeholder, BOOTSTRAP)
            self.assertIn(placeholder, MODULE)


if __name__ == "__main__":
    unittest.main()
