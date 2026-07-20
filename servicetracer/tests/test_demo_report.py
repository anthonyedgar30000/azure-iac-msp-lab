from __future__ import annotations

import json
from pathlib import Path
import unittest

from servicetracer.analyzer import analyze_incident, load_tickets
from servicetracer.containment import assess_load_balancer, build_containment_plan
from servicetracer.demo_data import build_containment_attempts, build_demo_attempts
from servicetracer.demo_report import build_technician_handoff


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class ServiceTracerDemoReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service_path = json.loads(
            (EXAMPLES / "remote_access_service_path.json").read_text(encoding="utf-8")
        )
        cls.tickets = load_tickets(EXAMPLES / "tickets.json")
        cls.incident_report = analyze_incident(
            build_demo_attempts(),
            cls.service_path,
            cls.tickets,
        )
        cls.load_balancer_state = json.loads(
            (EXAMPLES / "load_balancer_state.json").read_text(encoding="utf-8")
        )
        cls.load_balancer_assessment = assess_load_balancer(
            cls.incident_report,
            cls.load_balancer_state,
        )
        cls.containment = build_containment_plan(
            cls.incident_report,
            cls.service_path,
            build_containment_attempts(),
        )
        cls.report = build_technician_handoff(
            cls.incident_report,
            cls.load_balancer_assessment,
            cls.containment,
        )

    def test_stops_at_vpn02_investigation_boundary(self) -> None:
        self.assertEqual(self.report["status"], "technician_investigation_required")
        self.assertEqual(self.report["localization"]["suspect_backend"], "VPN-02")
        self.assertEqual(
            self.report["localization"]["healthy_comparison_backend"],
            "VPN-01",
        )
        self.assertEqual(
            self.report["investigation_boundary"]["service_tracer_stops_at"],
            "VPN-02",
        )
        self.assertFalse(
            self.report["investigation_boundary"]["exact_root_cause_claimed"]
        )

    def test_reports_load_balancer_healthy_without_calling_it_root_cause(self) -> None:
        self.assertEqual(
            self.report["load_balancer"]["status"],
            "healthy_under_configured_probe",
        )
        self.assertTrue(self.report["load_balancer"]["probe_gap_detected"])
        self.assertEqual(
            self.report["root_cause"]["status"],
            "not_determined_by_servicetracer",
        )
        self.assertEqual(self.report["root_cause"]["owner"], "technician")

    def test_encodes_the_manual_technician_sequence(self) -> None:
        steps = self.report["technician_workflow"]
        self.assertEqual(
            [step["step_id"] for step in steps],
            [
                "temporary-user-reroute",
                "manual-backend-troubleshooting",
                "controlled-test-user-validation",
                "original-user-return",
            ],
        )
        actions = " ".join(step["action"] for step in steps)
        self.assertIn("affected user through VPN-01", actions)
        self.assertIn("Review VPN-02 manually", actions)
        self.assertIn("dedicated test user", actions)
        self.assertIn("Return the original user to VPN-02", actions)

    def test_demo_view_does_not_expose_deeper_stage_diagnosis(self) -> None:
        rendered = json.dumps(self.report, sort_keys=True)
        self.assertNotIn("first_failed_stage", rendered)
        self.assertNotIn("radius_response", rendered)
        self.assertNotIn("shared secret", rendered)

    def test_reports_verified_temporary_service_state_without_claiming_repair(self) -> None:
        self.assertEqual(
            self.report["temporary_service_status"],
            "stabilized_under_containment",
        )
        self.assertEqual(
            self.report["root_cause"]["status"],
            "not_determined_by_servicetracer",
        )


if __name__ == "__main__":
    unittest.main()
