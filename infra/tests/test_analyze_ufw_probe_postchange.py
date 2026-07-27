from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "infra" / "scripts" / "analyze_ufw_probe_postchange.py"
VMS = ("vm-vpn01-mst-dev", "vm-vpn02-mst-dev")


def run_command_payload() -> dict:
    message = """Enable succeeded:\n[stdout]\n=== SYSTEMD_ACTIVE ===\nactive\n=== SYSTEMD_ENABLED ===\nenabled\n=== TCP_443_LISTENER ===\nLISTEN 0 5 0.0.0.0:443 0.0.0.0:* users:((\"python3\",pid=123,fd=3))\n=== UFW ===\nStatus: active\n[ 1] 443/tcp ALLOW IN 168.63.129.16\n=== END ===\n[stderr]\n"""
    return {"value": [{"message": message}]}


def probe_payload(healthy: bool) -> dict:
    average = 100.0 if healthy else 0.0
    return {
        "value": [
            {
                "timeseries": [
                    {
                        "metadatavalues": [
                            {"name": {"value": "BackendIPAddress"}, "value": ip},
                            {"name": {"value": "BackendPort"}, "value": "443"},
                        ],
                        "data": [{"average": average, "timeStamp": "2026-07-27T16:20:00Z"}],
                    }
                    for ip in ("10.20.10.11", "10.20.10.12")
                ]
            }
        ]
    }


def transactions_payload() -> list[dict]:
    return [
        {
            "attempt": 1,
            "http_code": 200,
            "response": {
                "backend": "VPN-01",
                "transaction_status": "successful",
                "failure_boundary": None,
            },
        },
        {
            "attempt": 2,
            "http_code": 503,
            "response": {
                "backend": "VPN-02",
                "transaction_status": "failed",
                "failure_boundary": "radius_response",
            },
        },
    ]


class UfwProbePostchangeAnalyzerTests(unittest.TestCase):
    def execute(self, healthy: bool) -> dict:
        with tempfile.TemporaryDirectory() as temporary_directory:
            evidence = Path(temporary_directory)
            for vm in VMS:
                (evidence / f"{vm}-run-command.json").write_text(
                    json.dumps(run_command_payload()), encoding="utf-8"
                )
            (evidence / "probe-metrics-final.json").write_text(
                json.dumps(probe_payload(healthy)), encoding="utf-8"
            )
            (evidence / "transactions.json").write_text(
                json.dumps(transactions_payload()), encoding="utf-8"
            )
            output_json = evidence / "result.json"
            output_md = evidence / "result.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ANALYZER),
                    "--evidence-dir",
                    str(evidence),
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

    def test_verified_recovery_and_intended_scenario(self) -> None:
        result = self.execute(True)
        self.assertEqual(
            result["conclusion"],
            "probe_recovered_after_ufw_change_and_scenario_verified",
        )
        self.assertTrue(result["operator_report_verified"])
        self.assertTrue(result["both_azure_probes_healthy"])
        self.assertTrue(result["transactions"]["intended_scenario_observed"])
        self.assertFalse(result["causal_attribution_supported"])

    def test_unhealthy_probe_does_not_claim_recovery(self) -> None:
        result = self.execute(False)
        self.assertEqual(
            result["conclusion"],
            "probe_still_unhealthy_despite_observed_guest_readiness",
        )
        self.assertFalse(result["both_azure_probes_healthy"])
        self.assertFalse(result["exact_root_cause_claimed"])


if __name__ == "__main__":
    unittest.main()
