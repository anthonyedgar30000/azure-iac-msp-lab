from __future__ import annotations

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from servicetracer.publish_cli import main as publish_main
from servicetracer.report_publication import (
    PUBLIC_SCHEMA_VERSION,
    PublicationError,
    build_public_envelope,
    publish_to_azure_blob,
    sanitize_technician_handoff,
)


def technician_handoff() -> dict:
    return {
        "scenario": "intermittent_remote_access",
        "status": "technician_investigation_required",
        "incident": {
            "classification": "intermittent_failure",
            "attempts": 2,
            "successful_attempts": 1,
            "failed_attempts": 1,
            "customer_email": "must-not-publish@example.test",
        },
        "load_balancer": {
            "status": "healthy_under_configured_probe",
            "probe_name": "tcp-443-shallow",
            "probe_scope": "listener-only",
            "backend_states": {
                "VPN-01": {
                    "administrative_state": "active",
                    "probe_status": "healthy",
                    "private_ip": "10.20.10.4",
                },
                "VPN-02": {
                    "administrative_state": "active",
                    "probe_status": "healthy",
                    "private_ip": "10.20.10.5",
                },
            },
            "probe_gap_detected": True,
            "subscription_id": "must-not-publish",
        },
        "localization": {
            "suspect_backend": "VPN-02",
            "healthy_comparison_backend": "VPN-01",
            "suspect_probe_status": "healthy",
            "backend_failure_rates": {"VPN-01": 0.0, "VPN-02": 1.0},
            "radius_response": "must-not-publish",
        },
        "service_tracer_finding": (
            "The configured load-balancer probe is healthy, but failed "
            "remote-access sessions are concentrated on VPN-02."
        ),
        "investigation_boundary": {
            "service_tracer_stops_at": "VPN-02",
            "exact_root_cause_claimed": False,
            "statement": "The technician performs device-specific diagnosis.",
            "debug_trace": "must-not-publish",
        },
        "root_cause": {
            "status": "not_determined_by_servicetracer",
            "owner": "technician",
            "candidate": "shared secret",
        },
        "temporary_service_status": "stabilized_under_containment",
        "technician_workflow": [
            {
                "step_id": "temporary-user-reroute",
                "owner": "technician",
                "status": "pending",
                "action": "Temporarily route the user through VPN-01.",
                "purpose": "Restore access.",
                "success_criteria": "The transaction succeeds.",
                "internal_ticket": "INC-SECRET",
            }
        ],
        "collector_token": "must-not-publish",
    }


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class ReportPublicationTests(unittest.TestCase):
    def test_sanitizer_is_allowlist_based(self) -> None:
        public = sanitize_technician_handoff(technician_handoff())
        rendered = json.dumps(public)

        for forbidden in (
            "customer_email",
            "private_ip",
            "subscription_id",
            "radius_response",
            "debug_trace",
            "candidate",
            "internal_ticket",
            "collector_token",
            "shared secret",
        ):
            self.assertNotIn(forbidden, rendered)

        self.assertEqual(public["localization"]["suspect_backend"], "VPN-02")
        self.assertFalse(
            public["investigation_boundary"]["exact_root_cause_claimed"]
        )

    def test_sanitizer_rejects_exact_root_cause_claim(self) -> None:
        report = technician_handoff()
        report["investigation_boundary"]["exact_root_cause_claimed"] = True
        with self.assertRaises(PublicationError):
            sanitize_technician_handoff(report)

    def test_envelope_contains_provenance_and_expiry(self) -> None:
        generated = datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc)
        envelope = build_public_envelope(
            technician_handoff(),
            source_id="stcollector-dev",
            servicetracer_version="0.5.0",
            generated_at=generated,
            ttl_seconds=900,
        )
        self.assertEqual(envelope["schema_version"], PUBLIC_SCHEMA_VERSION)
        self.assertEqual(envelope["generated_at"], "2026-07-20T20:00:00Z")
        self.assertEqual(envelope["expires_at"], "2026-07-20T20:15:00Z")
        self.assertEqual(envelope["source"]["id"], "stcollector-dev")

    def test_managed_identity_upload_uses_bearer_token(self) -> None:
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            if request.full_url.startswith(
                "http://169.254.169.254/metadata/identity/oauth2/token"
            ):
                self.assertEqual(request.headers["Metadata"], "true")
                return FakeResponse(json.dumps({"access_token": "test-token"}).encode())
            return FakeResponse(b"", status=201)

        envelope = build_public_envelope(
            technician_handoff(),
            source_id="stcollector-dev",
            servicetracer_version="0.5.0",
            generated_at=datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc),
        )
        destination = publish_to_azure_blob(
            envelope,
            storage_account="streport123",
            opener=opener,
            now=datetime(2026, 7, 20, 20, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(len(calls), 2)
        upload_request = calls[1][0]
        self.assertEqual(
            destination,
            "https://streport123.blob.core.windows.net/"
            "$web/reports/technician-handoff-report.json",
        )
        self.assertEqual(upload_request.get_method(), "PUT")
        self.assertEqual(
            upload_request.headers["Authorization"], "Bearer test-token"
        )
        self.assertEqual(upload_request.headers["X-ms-blob-type"], "BlockBlob")
        self.assertNotIn(b"must-not-publish", upload_request.data)

    def test_cli_can_write_public_envelope_locally(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "handoff.json"
            output_path = Path(directory) / "public.json"
            input_path.write_text(json.dumps(technician_handoff()), encoding="utf-8")

            argv = [
                "servicetracer-publish-report",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--source-id",
                "stcollector-dev",
                "--servicetracer-version",
                "0.5.0",
            ]
            with patch("sys.argv", argv), patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(publish_main(), 0)

            public = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(public["schema_version"], PUBLIC_SCHEMA_VERSION)
            self.assertEqual(public["source"]["id"], "stcollector-dev")
            self.assertNotIn("collector_token", json.dumps(public))


if __name__ == "__main__":
    unittest.main()
