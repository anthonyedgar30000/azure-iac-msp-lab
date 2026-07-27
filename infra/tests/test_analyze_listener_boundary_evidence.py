from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "infra" / "scripts" / "analyze_listener_boundary_evidence.py"


class ListenerBoundaryAnalyzerTests(unittest.TestCase):
    def write_json(self, root: Path, name: str, value: object) -> None:
        (root / name).write_text(json.dumps(value), encoding="utf-8")

    def base_fixture(self, root: Path, access: str = "Allow") -> None:
        self.write_json(root, "account.json", {"name": "Azure for Students"})
        self.write_json(
            root,
            "resource-group.json",
            {"name": "rg-servicetracer-dev-westus2", "location": "westus2"},
        )
        self.write_json(
            root,
            "load-balancer.json",
            {"name": "lb-remote-access-mst-dev", "provisioningState": "Succeeded"},
        )
        self.write_json(
            root,
            "load-balancer-probes.json",
            [
                {
                    "name": "tcp-443-shallow",
                    "protocol": "Tcp",
                    "port": 443,
                    "intervalInSeconds": 5,
                    "numberOfProbes": 2,
                    "provisioningState": "Succeeded",
                }
            ],
        )
        self.write_json(
            root,
            "load-balancer-rules.json",
            [
                {
                    "name": "remote-access-443",
                    "protocol": "Tcp",
                    "frontendPort": 443,
                    "backendPort": 443,
                    "probe": {"id": "/probes/tcp-443-shallow"},
                    "backendAddressPool": {"id": "/backendAddressPools/vpn-pool"},
                    "provisioningState": "Succeeded",
                }
            ],
        )
        self.write_json(
            root,
            "load-balancer-pools.json",
            [
                {
                    "name": "vpn-pool",
                    "loadBalancerBackendAddresses": [
                        {"name": "VPN-01", "ipAddress": "10.20.10.11"},
                        {"name": "VPN-02", "ipAddress": "10.20.10.12"},
                    ],
                }
            ],
        )
        self.write_json(
            root,
            "network-interfaces.json",
            [
                {
                    "name": "nic-vpn01",
                    "id": "/nics/nic-vpn01",
                    "virtualMachine": {"id": "/virtualMachines/vm-vpn01-mst-dev"},
                    "networkSecurityGroup": {"id": "/nsgs/nsg-vpn"},
                    "ipConfigurations": [
                        {
                            "privateIPAddress": "10.20.10.11",
                            "subnet": {"id": "/subnets/backend"},
                            "loadBalancerBackendAddressPools": [{"id": "/backendAddressPools/vpn-pool"}],
                        }
                    ],
                },
                {
                    "name": "nic-vpn02",
                    "id": "/nics/nic-vpn02",
                    "virtualMachine": {"id": "/virtualMachines/vm-vpn02-mst-dev"},
                    "networkSecurityGroup": {"id": "/nsgs/nsg-vpn"},
                    "ipConfigurations": [
                        {
                            "privateIPAddress": "10.20.10.12",
                            "subnet": {"id": "/subnets/backend"},
                            "loadBalancerBackendAddressPools": [{"id": "/backendAddressPools/vpn-pool"}],
                        }
                    ],
                },
            ],
        )
        self.write_json(
            root,
            "virtual-networks.json",
            [
                {
                    "name": "vnet",
                    "subnets": [
                        {"id": "/subnets/backend", "networkSecurityGroup": {"id": "/nsgs/nsg-vpn"}}
                    ],
                }
            ],
        )
        self.write_json(
            root,
            "virtual-machines.json",
            [
                {"name": "vm-vpn01-mst-dev", "powerState": "VM running", "provisioningState": "Succeeded"},
                {"name": "vm-vpn02-mst-dev", "powerState": "VM running", "provisioningState": "Succeeded"},
            ],
        )
        rule = {
            "name": "AllowAzureLoadBalancerInBound",
            "direction": "Inbound",
            "protocol": "Tcp",
            "sourceAddressPrefix": "AzureLoadBalancer",
            "destinationPortRange": "443",
            "access": access,
            "priority": 100,
        }
        self.write_json(
            root,
            "effective-nsg.json",
            {
                "nic-vpn01": {"value": [{"effectiveSecurityRules": [rule]}]},
                "nic-vpn02": {"value": [{"effectiveSecurityRules": [rule]}]},
            },
        )
        series = []
        for ip in ("10.20.10.11", "10.20.10.12"):
            series.append(
                {
                    "metadatavalues": [
                        {"name": {"value": "BackendIPAddress"}, "value": ip},
                        {"name": {"value": "BackendPort"}, "value": "443"},
                    ],
                    "data": [{"average": 0.0, "timeStamp": "2026-07-27T15:17:00Z"}],
                }
            )
        self.write_json(root, "probe-metrics.json", {"value": [{"timeseries": series}]})
        self.write_json(root, "resource-locks.json", [])

    def run_analyzer(self, root: Path) -> dict[str, object]:
        output_json = root / "diagnosis.json"
        output_md = root / "diagnosis.md"
        completed = subprocess.run(
            [
                sys.executable,
                str(ANALYZER),
                "--evidence-dir",
                str(root),
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(output_json.read_text(encoding="utf-8"))

    def test_running_members_with_effective_allow_preserve_guest_uncertainty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.base_fixture(root)
            result = self.run_analyzer(root)
            self.assertEqual(
                result["diagnosis"]["conclusion"],
                "guest_listener_or_guest_firewall_boundary_not_yet_observed",
            )
            self.assertFalse(result["exact_root_cause_claimed"])
            self.assertFalse(result["guest_command_performed"])
            self.assertEqual(result["backends"]["VPN-01"]["guest_listener_tcp_443"], "not_observed")
            self.assertTrue(
                result["diagnosis"]["both_effective_nsgs_allow_azure_load_balancer_tcp_443"]
            )

    def test_effective_deny_is_reported_as_network_security_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.base_fixture(root, access="Deny")
            result = self.run_analyzer(root)
            self.assertEqual(result["diagnosis"]["conclusion"], "network_security_boundary_observed")
            self.assertFalse(result["exact_root_cause_claimed"])


if __name__ == "__main__":
    unittest.main()
