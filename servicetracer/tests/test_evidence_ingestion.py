from __future__ import annotations

import json
from pathlib import Path
import unittest

from servicetracer.analyzer import analyze_incident
from servicetracer.containment import assess_load_balancer, build_containment_plan
from servicetracer.evidence import (
    build_evidence_bundle,
    derive_load_balancer_state,
    load_adapter_config,
    load_evidence_bundle,
    load_jsonl_records,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class ServiceTracerEvidenceIngestionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service_path = json.loads(
            (EXAMPLES / "remote_access_service_path.json").read_text(encoding="utf-8")
        )
        cls.adapter_config = load_adapter_config(EXAMPLES / "evidence_adapters.json")
        cls.bundle = load_evidence_bundle(
            [EXAMPLES / "source_records.jsonl"],
            EXAMPLES / "evidence_adapters.json",
            cls.service_path,
        )
        cls.report = analyze_incident(
            cls.bundle.attempts,
            cls.service_path,
            cls.bundle.tickets,
        )

    def test_assembles_real_source_records_into_attempts(self) -> None:
        self.assertEqual(len(self.bundle.attempts), 2)
        self.assertEqual(self.bundle.ingestion_summary["assembled_attempts"], 2)
        self.assertEqual(self.bundle.ingestion_summary["incomplete_transactions"], 0)
        self.assertEqual(len(self.bundle.tickets), 1)
        self.assertEqual(len(self.bundle.context_observations), 3)

    def test_localizes_failure_from_mixed_evidence_sources(self) -> None:
        localization = self.report["localization"]
        self.assertEqual(localization["candidate_gateway"], "VPN-02")
        self.assertEqual(localization["healthy_peer"], "VPN-01")
        self.assertEqual(localization["last_successful_stage"], "radius_request")
        self.assertEqual(localization["first_failed_stage"], "radius_response")
        self.assertEqual(localization["representative_retries"], 3)
        self.assertEqual(localization["representative_timeout_ms"], 15000)
        self.assertEqual(
            [item["ticket_id"] for item in self.report["related_operational_history"]],
            ["CHG-1042"],
        )

    def test_derives_load_balancer_state_from_context_evidence(self) -> None:
        state = derive_load_balancer_state(self.bundle.context_observations)
        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(
            [backend["backend_id"] for backend in state["backends"]],
            ["VPN-01", "VPN-02"],
        )
        assessment = assess_load_balancer(self.report, state)
        self.assertTrue(assessment["shallow_probe_gap_detected"])
        self.assertEqual(assessment["candidate_backend"], "VPN-02")

    def test_assembles_post_containment_source_records(self) -> None:
        containment = load_evidence_bundle(
            [EXAMPLES / "containment_source_records.jsonl"],
            EXAMPLES / "evidence_adapters.json",
            self.service_path,
        )
        plan = build_containment_plan(
            self.report,
            self.service_path,
            containment.attempts,
        )
        self.assertEqual(plan["status"], "stabilized_under_containment")
        self.assertEqual(plan["verification"]["attempts"], 2)
        self.assertEqual(plan["verification"]["success_rate"], 1.0)
        self.assertEqual(plan["verification"]["observed_gateways"], ["VPN-01"])

    def test_idempotent_duplicate_is_counted_not_reprocessed(self) -> None:
        records = load_jsonl_records([EXAMPLES / "source_records.jsonl"])
        records.append(json.loads(json.dumps(records[0])))
        bundle = build_evidence_bundle(records, self.adapter_config, self.service_path)
        self.assertEqual(bundle.ingestion_summary["idempotent_duplicates"], 1)
        self.assertEqual(len(bundle.attempts), 2)

    def test_divergent_reused_event_identity_is_rejected(self) -> None:
        records = load_jsonl_records([EXAMPLES / "source_records.jsonl"])
        divergent = json.loads(json.dumps(records[0]))
        divergent["probe_status"] = "unhealthy"
        records.append(divergent)
        with self.assertRaisesRegex(ValueError, "reused with different content"):
            build_evidence_bundle(records, self.adapter_config, self.service_path)

    def test_incomplete_transaction_is_reported_not_fabricated(self) -> None:
        records = load_jsonl_records([EXAMPLES / "source_records.jsonl"])
        records = [
            record
            for record in records
            if not (
                record.get("session_id") == "ATT-001"
                and record.get("event") == "tls_completed"
            )
        ]
        bundle = build_evidence_bundle(records, self.adapter_config, self.service_path)
        self.assertEqual(len(bundle.attempts), 1)
        self.assertEqual(bundle.incomplete_transactions[0]["correlation_id"], "ATT-001")
        self.assertIn(
            "tls_handshake", bundle.incomplete_transactions[0]["missing_stages"]
        )


if __name__ == "__main__":
    unittest.main()
