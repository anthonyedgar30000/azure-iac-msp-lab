from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".project" / "evidence" / "servicetracer-demo-api-live-verification-30086152352.json"
VALIDATOR = ROOT / "scripts" / "validate_servicetracer_demo_api_live_evidence.py"


class ServiceTracerDemoApiLiveEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_public_api_is_verified_without_overclaiming_backend_success(self) -> None:
        typed = self.document["typed_verification"]
        self.assertTrue(typed["public_api_operationally_verified"])
        self.assertTrue(typed["transaction_protocol_verified"])
        self.assertFalse(typed["backend_transaction_success_verified"])
        self.assertFalse(typed["full_workload_operationally_verified"])

    def test_bounded_sample_preserves_failures_and_observation_gap(self) -> None:
        transaction = self.document["public_runtime_observation"]["transaction_protocol"]
        self.assertEqual(transaction["attempts"], 2)
        self.assertEqual(transaction["successful_attempts"], 0)
        self.assertEqual(transaction["failed_attempts"], 2)
        self.assertEqual(transaction["observed_backends"], ["VPN-02"])
        self.assertEqual(transaction["backend_attempt_counts"], {"VPN-01": 0, "VPN-02": 2})
        self.assertFalse(transaction["backend_specific_localization_stable"])
        self.assertFalse(transaction["exact_root_cause_claimed"])

    def test_control_plane_provenance_remains_not_observed(self) -> None:
        control = self.document["azure_control_plane_provenance"]
        self.assertEqual(control["state"], "not_observed")
        for field, value in control.items():
            if field != "state":
                self.assertFalse(value, field)

    def test_no_new_operational_authority_is_granted(self) -> None:
        authority = self.document["mutation_and_authority"]
        self.assertTrue(authority["repository_evidence_promotion_authorized"])
        self.assertTrue(authority["pull_request_creation_authorized"])
        self.assertFalse(authority["pull_request_merge_authorized"])
        self.assertFalse(authority["azure_authentication_authorized"])
        self.assertFalse(authority["azure_mutations_authorized"])
        self.assertFalse(authority["deployment_authorized"])
        self.assertFalse(authority["cleanup_authorized"])

    def test_validator_executes(self) -> None:
        spec = importlib.util.spec_from_file_location("live_evidence_validator", VALIDATOR)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.main(), 0)


if __name__ == "__main__":
    unittest.main()
