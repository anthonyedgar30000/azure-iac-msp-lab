from __future__ import annotations

from unittest import mock
import unittest

from servicetracer.azure_demo import build_source_records, collect_transactions


class AzureDemoEvidenceTests(unittest.TestCase):
    def test_collect_transactions_requires_both_load_balanced_backends(self) -> None:
        responses = [
            (
                200,
                {"x-servicetracer-backend": "VPN-01"},
                {
                    "schema_version": "servicetracer.azure-demo-response.v1",
                    "correlation_id": "placeholder",
                    "backend": "VPN-01",
                    "transaction_status": "successful",
                    "stages": [
                        {
                            "source_type": "vpn_syslog",
                            "event": "tcp_established",
                            "elapsed_ms": 1,
                        }
                    ],
                },
            ),
            (
                503,
                {"x-servicetracer-backend": "VPN-02"},
                {
                    "schema_version": "servicetracer.azure-demo-response.v1",
                    "correlation_id": "placeholder",
                    "backend": "VPN-02",
                    "transaction_status": "failed",
                    "stages": [
                        {
                            "source_type": "vpn_syslog",
                            "event": "radius_response_timeout",
                            "elapsed_ms": 15000,
                            "retries": 3,
                            "timeout_ms": 15000,
                        }
                    ],
                },
            ),
        ]

        def fake_read(url: str, *, timeout_seconds: float):
            del timeout_seconds
            status, headers, payload = responses.pop(0)
            correlation_id = url.split("correlation_id=", 1)[1]
            return status, headers, {**payload, "correlation_id": correlation_id}

        with mock.patch(
            "servicetracer.azure_demo._read_json_response",
            side_effect=fake_read,
        ):
            transactions = collect_transactions(
                "https://example.test",
                attempts=4,
                pause_seconds=0,
            )

        self.assertEqual([item["backend"] for item in transactions], ["VPN-01", "VPN-02"])
        self.assertEqual([item["http_status"] for item in transactions], [200, 503])

    def test_source_records_preserve_probe_transaction_contradiction(self) -> None:
        transactions = [
            {
                "correlation_id": "AZURE-001",
                "started_at": "2026-07-20T20:00:00.000Z",
                "backend": "VPN-01",
                "payload": {
                    "stages": [
                        {
                            "source_type": "vpn_syslog",
                            "event": "tcp_established",
                            "elapsed_ms": 82,
                        },
                        {
                            "source_type": "nps_windows",
                            "event": "radius_access_accept",
                            "elapsed_ms": 95,
                        },
                        {
                            "source_type": "synthetic_probe",
                            "event": "rdp_session_usable",
                            "elapsed_ms": 980,
                        },
                    ]
                },
            },
            {
                "correlation_id": "AZURE-002",
                "started_at": "2026-07-20T20:01:00.000Z",
                "backend": "VPN-02",
                "payload": {
                    "stages": [
                        {
                            "source_type": "vpn_syslog",
                            "event": "tcp_established",
                            "elapsed_ms": 90,
                        },
                        {
                            "source_type": "vpn_syslog",
                            "event": "radius_response_timeout",
                            "elapsed_ms": 15000,
                            "retries": 3,
                            "timeout_ms": 15000,
                        },
                    ]
                },
            },
        ]

        records = build_source_records(
            transactions,
            {"VPN-01": "healthy", "VPN-02": "healthy"},
        )

        probe_records = [
            record for record in records if record["event"] == "backend_probe_state"
        ]
        self.assertEqual(len(probe_records), 2)
        self.assertTrue(all(record["probe_status"] == "healthy" for record in probe_records))
        self.assertTrue(
            any(
                record["event"] == "radius_response_timeout"
                and record["device"] == "VPN-02"
                for record in records
            )
        )
        self.assertTrue(
            any(
                record["event"] == "rdp_session_usable"
                and record["gateway"] == "VPN-01"
                for record in records
            )
        )


if __name__ == "__main__":
    unittest.main()
