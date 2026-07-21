from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "infra"
MODULE = (INFRA / "modules" / "remote_access_backends.bicep").read_text(
    encoding="utf-8"
)
BOOTSTRAP = (INFRA / "bootstrap" / "vpn-backend-cloud-init.yaml").read_text(
    encoding="utf-8"
)
MAIN = (INFRA / "main.bicep").read_text(encoding="utf-8")
DEV = (INFRA / "main.dev.bicepparam").read_text(encoding="utf-8")
LIFECYCLE = (ROOT / ".github" / "workflows" / "azure-lab-lifecycle.yml").read_text(
    encoding="utf-8"
)


class RemoteAccessBackendTests(unittest.TestCase):
    def test_two_private_backends_join_the_load_balancer_pool(self) -> None:
        for expected in (
            "backendId: 'VPN-01'",
            "backendId: 'VPN-02'",
            "privateIpAddress: '10.20.10.11'",
            "privateIpAddress: '10.20.10.12'",
            "loadBalancerBackendAddressPools",
            "id: loadBalancerBackendPoolId",
        ):
            self.assertIn(expected, MODULE)
        self.assertNotIn("publicIPAddresses", MODULE)

    def test_backends_use_trusted_launch_and_ssh_only_management(self) -> None:
        self.assertIn("disablePasswordAuthentication: true", MODULE)
        self.assertIn("securityType: 'TrustedLaunch'", MODULE)
        self.assertIn("secureBootEnabled: true", MODULE)
        self.assertIn("vTpmEnabled: true", MODULE)
        self.assertIn("Microsoft.Compute/availabilitySets", MODULE)

    def test_probe_scope_contradiction_is_deliberate_and_bounded(self) -> None:
        self.assertIn("mode: 'healthy'", MODULE)
        self.assertIn("mode: 'radius-timeout'", MODULE)
        self.assertIn("503 if failed else 200", BOOTSTRAP)
        self.assertIn('parsed.path == "/healthz"', BOOTSTRAP)
        self.assertIn('parsed.path != "/transaction"', BOOTSTRAP)
        self.assertIn("X-ServiceTracer-Backend", BOOTSTRAP)
        self.assertIn("radius_response_timeout", BOOTSTRAP)

    def test_compute_remains_opt_in(self) -> None:
        self.assertIn("param deployDemoBackends bool = false", MAIN)
        self.assertIn("if (deployDemoBackends)", MAIN)
        self.assertIn("param deployDemoBackends = false", DEV)
        self.assertIn("deploy_demo_backends:", LIFECYCLE)
        self.assertIn("default: false", LIFECYCLE)


if __name__ == "__main__":
    unittest.main()
