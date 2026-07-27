import json
import tempfile
import unittest
from pathlib import Path

from infra.scripts.analyze_vpn_backend_guest_inspection import build_diagnosis


class GuestInspectionAnalyzerTests(unittest.TestCase):
    def write_payload(self, root: Path, vm: str, message: str) -> None:
        payload = {"value": [{"code": "ComponentStatus/StdOut/succeeded", "message": message}]}
        (root / f"{vm}-run-command.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_failed_service_is_localized_without_claiming_root_cause(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            failed = """=== CLOUD_INIT ===
status: done
=== SYSTEMD_SHOW ===
ActiveState=failed
=== SYSTEMD_STATUS ===
failed
=== SYSTEMD_ACTIVE ===
failed
=== SYSTEMD_ENABLED ===
enabled
=== TCP_443_LISTENER ===
State Recv-Q Send-Q Local Address:Port
=== JOURNAL ===
Process exited with status=1/FAILURE
=== UFW ===
Status: inactive
=== END ===
"""
            healthy = """=== CLOUD_INIT ===
status: done
=== SYSTEMD_SHOW ===
ActiveState=active
=== SYSTEMD_STATUS ===
active
=== SYSTEMD_ACTIVE ===
active
=== SYSTEMD_ENABLED ===
enabled
=== TCP_443_LISTENER ===
LISTEN 0 5 0.0.0.0:443 0.0.0.0:* users:((\"python3\",pid=1,fd=3))
=== JOURNAL ===
Started ServiceTracer simulated remote-access backend.
=== UFW ===
Status: inactive
=== END ===
"""
            self.write_payload(root, "vm-vpn01-mst-dev", failed)
            self.write_payload(root, "vm-vpn02-mst-dev", healthy)
            diagnosis = build_diagnosis(root)
            self.assertEqual(diagnosis["conclusion"], "guest_listener_fault_observed")
            self.assertEqual(
                diagnosis["virtual_machines"]["vm-vpn01-mst-dev"]["boundary"],
                "systemd_service_failed",
            )
            self.assertTrue(
                diagnosis["virtual_machines"]["vm-vpn02-mst-dev"]["tcp_443_listener_observed"]
            )
            self.assertFalse(diagnosis["exact_root_cause_claimed"])
            self.assertFalse(diagnosis["azure_mutation_performed"])

    def test_both_listeners_observed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            active = """=== CLOUD_INIT ===
status: done
=== SYSTEMD_SHOW ===
ActiveState=active
=== SYSTEMD_STATUS ===
active
=== SYSTEMD_ACTIVE ===
active
=== SYSTEMD_ENABLED ===
enabled
=== TCP_443_LISTENER ===
LISTEN 0 5 0.0.0.0:443 0.0.0.0:*
=== JOURNAL ===
Started ServiceTracer simulated remote-access backend.
=== UFW ===
Status: inactive
=== END ===
"""
            for vm in ("vm-vpn01-mst-dev", "vm-vpn02-mst-dev"):
                self.write_payload(root, vm, active)
            diagnosis = build_diagnosis(root)
            self.assertEqual(diagnosis["conclusion"], "both_tcp_443_listeners_observed")
            self.assertTrue(diagnosis["both_tcp_443_listeners_observed"])


if __name__ == "__main__":
    unittest.main()
