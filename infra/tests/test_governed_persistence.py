from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import py_compile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "infra" / "scripts" / "governed_persistence.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GovernedPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = load_module(CONTROLLER, "governed_persistence_controller")

    def test_controller_compiles(self):
        py_compile.compile(str(CONTROLLER), doraise=True)

    def _state(self):
        return self.controller.new_state(
            objective="deploy and verify bounded collector-hosted API",
            success_criteria=["TLS verified", "health verified"],
            authorized_scope=["rg-servicetracer-dev-westus2", "collector demo API resources"],
            retry_budget=2,
            strategy="isolated collector API Bicep root",
            reality_watermark={"reviewed_commit": "a" * 40},
        )

    def test_proceed_preserves_objective_scope_and_authority(self):
        state = self._state()
        transitioned = self.controller.apply_control_message(
            state,
            "proceed",
            observation={"observed_result": "plan accepted", "evidence": ["what-if.json"]},
        )
        self.assertEqual(transitioned["objective"], state["objective"])
        self.assertEqual(transitioned["authorized_scope"], state["authorized_scope"])
        self.assertEqual(transitioned["authority"], state["authority"])
        self.assertEqual(transitioned["phase"], "acting")
        self.assertEqual(transitioned["attempt_number"], 1)
        self.assertEqual(transitioned["next_control_message"], "verify")

    def test_fix_requires_recoverable_failure(self):
        state = self._state()
        with self.assertRaisesRegex(ValueError, "recoverable_failure"):
            self.controller.apply_control_message(
                state,
                "fix",
                observation={"failure_class": "strategy_failure"},
            )

    def test_sync_requires_reality_watermark_and_does_not_mutate_authority(self):
        state = self._state()
        transitioned = self.controller.apply_control_message(
            state,
            "sync_with_reality",
            observation={
                "failure_class": "stale_or_uncertain_state",
                "reality_watermark": {
                    "reviewed_commit": "b" * 40,
                    "azure_observed_at": "2026-07-23T20:00:00Z",
                },
            },
        )
        self.assertEqual(transitioned["phase"], "synchronizing")
        self.assertEqual(transitioned["authority"], state["authority"])
        self.assertEqual(transitioned["next_control_message"], "verify")

    def test_restrategize_preserves_objective(self):
        state = self._state()
        transitioned = self.controller.apply_control_message(
            state,
            "restrategize",
            observation={"strategy": "reuse existing public endpoint"},
        )
        self.assertEqual(transitioned["objective"], state["objective"])
        self.assertEqual(transitioned["strategy_revision"], 1)
        self.assertEqual(transitioned["next_control_message"], "proceed")

    def test_complete_requires_verified_success(self):
        state = self._state()
        with self.assertRaisesRegex(ValueError, "verified success criteria"):
            self.controller.apply_control_message(state, "complete")
        completed = self.controller.apply_control_message(
            state,
            "complete",
            observation={"success_criteria_verified": True, "evidence": ["verification.json"]},
        )
        self.assertEqual(completed["phase"], "completed")
        self.assertTrue(completed["success_criteria_verified"])

    def _evaluate(self, files, *, operation="what-if", conclusion="failure", attempt=1, budget=2):
        with tempfile.TemporaryDirectory() as temp:
            artifact_dir = Path(temp)
            for name, payload in files.items():
                (artifact_dir / name).write_text(json.dumps(payload), encoding="utf-8")
            return self.controller.evaluate_collector_demo_api(
                operation=operation,
                workflow_conclusion=conclusion,
                attempt_number=attempt,
                retry_budget=budget,
                artifact_dir=artifact_dir,
            )

    def test_accepted_what_if_recommends_proceed_but_not_deployment_authority(self):
        result = self._evaluate(
            {
                "request.json": {"operation": "what-if"},
                "readiness-assessment.json": {"blockers": []},
                "what-if-assessment.json": {"status": "accepted_isolated_collector_api_changes"},
            },
            conclusion="success",
        )
        self.assertEqual(result["next_control_message"], "proceed")
        self.assertEqual(result["recommended_next_operation"], "deploy")
        self.assertEqual(result["human_gate_required"], "explicit_deploy_authorization")
        self.assertFalse(result["authority_effects"]["azure_mutation_authorized"])
        self.assertFalse(result["authority_effects"]["workflow_dispatch_authorized"])

    def test_missing_readiness_recommends_sync_with_reality(self):
        result = self._evaluate({"request.json": {"operation": "what-if"}})
        self.assertEqual(result["next_control_message"], "sync_with_reality")
        self.assertEqual(result["failure_class"], "stale_or_uncertain_state")

    def test_quota_shortfall_recommends_restrategize(self):
        result = self._evaluate(
            {
                "request.json": {"operation": "what-if"},
                "readiness-assessment.json": {"blockers": ["public_ip_quota_insufficient"]},
            }
        )
        self.assertEqual(result["next_control_message"], "restrategize")
        self.assertEqual(result["failure_class"], "strategy_failure")

    def test_read_only_lock_escalates(self):
        result = self._evaluate(
            {
                "request.json": {"operation": "deploy"},
                "readiness-assessment.json": {"blockers": ["resource_group_read_only_lock_present"]},
            },
            operation="deploy",
        )
        self.assertEqual(result["next_control_message"], "escalate")
        self.assertEqual(result["failure_class"], "boundary_reached")

    def test_deployment_without_verification_recommends_verify(self):
        result = self._evaluate(
            {
                "request.json": {"operation": "deploy"},
                "readiness-assessment.json": {"blockers": []},
                "what-if-assessment.json": {"status": "accepted_isolated_collector_api_changes"},
                "deployment-result.json": {"properties": {"provisioningState": "Succeeded"}},
            },
            operation="deploy",
            conclusion="failure",
        )
        self.assertEqual(result["next_control_message"], "verify")
        self.assertEqual(result["recommended_next_operation"], "verify")
        self.assertEqual(result["human_gate_required"], "explicit_verify_dispatch")

    def test_verified_service_completes(self):
        result = self._evaluate(
            {
                "request.json": {"operation": "verify"},
                "verification.json": {
                    "tls_verified": True,
                    "health_verified": True,
                    "twenty_correlated_transactions_verified": True,
                    "cors_verified": True,
                    "service_validated": True,
                },
            },
            operation="verify",
            conclusion="success",
        )
        self.assertEqual(result["next_control_message"], "complete")
        self.assertTrue(result["terminal"])
        self.assertTrue(result["success_criteria_verified"])

    def test_retry_budget_exhaustion_escalates(self):
        result = self._evaluate(
            {"request.json": {"operation": "verify"}},
            operation="verify",
            conclusion="failure",
            attempt=3,
            budget=2,
        )
        self.assertEqual(result["next_control_message"], "escalate")
        self.assertEqual(result["failure_class"], "retry_budget_exhausted")


if __name__ == "__main__":
    unittest.main()
