from __future__ import annotations

import json
from pathlib import Path
import unittest

from servicetracer.analyzer import analyze_incident, load_tickets
from servicetracer.demo_data import build_demo_attempts


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class ServiceTracerAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.attempts = build_demo_attempts()
        cls.tickets = load_tickets(EXAMPLES / "tickets.json")
        cls.service_path = json.loads(
            (EXAMPLES / "remote_access_service_path.json").read_text(encoding="utf-8")
        )
        cls.report = analyze_incident(cls.attempts, cls.service_path, cls.tickets)

    def test_classifies_intermittent_failure(self) -> None:
        self.assertEqual(self.report["summary"]["classification"], "intermittent_failure")
        self.assertEqual(self.report["summary"]["attempts"], 20)
        self.assertEqual(self.report["summary"]["failed_attempts"], 9)
        self.assertEqual(self.report["summary"]["successful_attempts"], 11)

    def test_localizes_failure_to_vpn02_radius_response(self) -> None:
        localization = self.report["localization"]
        self.assertEqual(localization["candidate_gateway"], "VPN-02")
        self.assertEqual(localization["healthy_peer"], "VPN-01")
        self.assertEqual(localization["last_successful_stage"], "radius_request")
        self.assertEqual(localization["first_failed_stage"], "radius_response")
        self.assertEqual(localization["representative_retries"], 3)
        self.assertEqual(localization["representative_timeout_ms"], 15000)

    def test_preserves_downstream_not_reached_distinction(self) -> None:
        self.assertEqual(
            self.report["localization"]["not_reached"],
            [
                "vpn_address_assignment",
                "tunnel_established",
                "internal_dns",
                "kerberos_ticket",
                "rdp_session",
            ],
        )

    def test_correlates_relevant_change_without_claiming_causation(self) -> None:
        history = self.report["related_operational_history"]
        self.assertEqual([record["ticket_id"] for record in history], ["CHG-1042"])
        self.assertIn("same asset and failed service stage", history[0]["reason"])
        self.assertTrue(
            any(
                "does not by itself establish" in item
                for item in self.report["remaining_uncertainty"]
            )
        )

    def test_recommends_containment_and_comparison(self) -> None:
        recommendations = " ".join(self.report["recommendations"])
        self.assertIn("Stop assigning new sessions to VPN-02", recommendations)
        self.assertIn("Compare VPN-02 with VPN-01", recommendations)
        self.assertIn("RADIUS destination", recommendations)

    def test_rejects_out_of_order_stages(self) -> None:
        broken = json.loads(json.dumps(self.attempts))
        broken[0]["stages"][0], broken[0]["stages"][1] = (
            broken[0]["stages"][1],
            broken[0]["stages"][0],
        )
        with self.assertRaisesRegex(ValueError, "stage order"):
            analyze_incident(broken, self.service_path, self.tickets)


if __name__ == "__main__":
    unittest.main()
