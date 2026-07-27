from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "vpn01-guest-local-tls-sidecar.yml"
AUTHORITY = (
    ROOT
    / ".project"
    / "change-requests"
    / "vpn01-guest-local-tls-sidecar-20260727.json"
)


class Vpn01GuestLocalSidecarWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.authority = AUTHORITY.read_text(encoding="utf-8")

    def test_workflow_is_manual_only(self) -> None:
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("\n  push:\n", self.workflow)
        self.assertNotIn("\n  pull_request:\n", self.workflow)
        self.assertIn("AUTHORIZE-VPN01-GUEST-LOCAL-SIDECAR", self.workflow)

    def test_scope_is_vpn01_only(self) -> None:
        self.assertIn("TARGET_VM: vm-vpn01-mst-dev", self.workflow)
        self.assertIn("TARGET_IP: 10.20.10.11", self.workflow)
        self.assertNotIn("vm-vpn02-mst-dev", self.workflow)
        self.assertNotIn("10.20.10.12", self.workflow)

    def test_sidecar_is_separate_from_production(self) -> None:
        self.assertIn(
            "CANARY_SERVICE: servicetracer-demo-backend-canary.service",
            self.workflow,
        )
        self.assertIn("CANARY_ROOT: /opt/servicetracer-demo-canary", self.workflow)
        self.assertIn("CANARY_PORT: '8443'", self.workflow)
        self.assertIn("SERVICETRACER_LISTENER_PORT=8443", self.workflow)
        self.assertIn("Restart=no", self.workflow)
        self.assertIn("systemctl start \"\\$canary_service\"", self.workflow)
        self.assertNotIn("systemctl restart \"\\$production_service\"", self.workflow)
        self.assertNotIn("systemctl stop \"\\$production_service\"", self.workflow)

    def test_production_integrity_and_cleanup_are_mandatory(self) -> None:
        for required in (
            "production-preflight",
            "production-pre.sha256",
            "sha256sum -c \"\\$pre_hashes\"",
            "cleanup-start",
            "cleanup-complete",
            "rm -f \"\\$canary_unit\"",
            "rm -rf \"\\$canary_root\"",
            "SERVICETRACER_GUEST_LOCAL_SIDECAR_SUCCESS",
            "cleanup=verified production_integrity=verified",
        ):
            self.assertIn(required, self.workflow)

    def test_raw_tcp_regression_is_exercised_in_guest(self) -> None:
        for required in (
            "RAW_PROBES_CONNECTED count=12",
            "https-survives-raw-probes",
            "listener-queue-below-backlog",
            "curl -kfsS",
            "127.0.0.1",
        ):
            self.assertIn(required, self.workflow)

    def test_no_network_or_firewall_mutation(self) -> None:
        forbidden = (
            "az network",
            "az monitor",
            "ufw allow",
            "ufw delete",
            "ufw enable",
            "ufw disable",
            "az deployment",
            "az group create",
            "az vm create",
        )
        for command in forbidden:
            self.assertNotIn(command, self.workflow)

    def test_authority_requires_separate_dispatch_approval(self) -> None:
        self.assertIn('"requires_new_explicit_authorization": true', self.authority)
        self.assertIn('"workflow_dispatch": false', self.authority)
        self.assertIn('"merge_to_main": false', self.authority)
        self.assertIn('"production_service_restart": false', self.authority)
        self.assertIn('"vpn02_access": false', self.authority)


if __name__ == "__main__":
    unittest.main()
