from __future__ import annotations

import json
from pathlib import Path
import unittest

from servicetracer.analyzer import analyze_incident, load_tickets
from servicetracer.containment import assess_load_balancer, build_containment_plan
from servicetracer.demo_data import build_containment_attempts, build_demo_attempts


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class ServiceTracerContainmentTests(unittest.TestCase):
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

    def test_detects_shallow_probe_gap(self) -> None:
        assessment = assess_load_balancer(
            self.incident_report,
            self.load_balancer_state,
        )
        self.assertTrue(assessment["shallow_probe_gap_detected"])
        self.assertEqual(assessment["candidate_backend"], "VPN-02")
        self.assertEqual(assessment["candidate_probe_status"], "healthy")
        self.assertEqual(assessment["candidate_end_to_end_failure_rate"], 0.9)
        self.assertIn("full remote-access transaction", assessment["explanation"])

    def test_verifies_service_stabilization_after_drain(self) -> None:
        plan = build_containment_plan(
            self.incident_report,
            self.service_path,
            build_containment_attempts(),
        )
        self.assertEqual(plan["status"], "stabilized_under_containment")
        self.assertEqual(plan["suspect_backend"], "VPN-02")
        self.assertEqual(plan["temporary_healthy_backend"], "VPN-01")
        verification = plan["verification"]
        self.assertTrue(verification["performed"])
        self.assertEqual(verification["attempts"], 12)
        self.assertEqual(verification["success_rate"], 1.0)
        self.assertEqual(verification["observed_gateways"], ["VPN-01"])
        self.assertFalse(verification["suspect_received_new_attempts"])
        self.assertTrue(verification["service_stabilized_under_containment"])

    def test_drain_does_not_claim_suspect_ready_for_service(self) -> None:
        plan = build_containment_plan(
            self.incident_report,
            self.service_path,
            build_containment_attempts(),
        )
        uncertainty = " ".join(plan["remaining_uncertainty"])
        self.assertIn("does not establish that the node is ready", uncertainty)
        gates = " ".join(plan["return_to_service_gates"])
        self.assertIn("Run direct synthetic transactions against VPN-02", gates)
        self.assertIn("Return VPN-02 gradually", gates)

    def test_rejects_duplicate_backend_identity(self) -> None:
        broken = json.loads(json.dumps(self.load_balancer_state))
        broken["backends"].append(dict(broken["backends"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate load-balancer backend"):
            assess_load_balancer(self.incident_report, broken)


if __name__ == "__main__":
    unittest.main()
