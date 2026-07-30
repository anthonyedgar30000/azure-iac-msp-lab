from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION = ROOT / ".project/deployment-requests/servicetracer-demo-api-plan-run1.json"
BLOCKER_RECONCILIATION = (
    ROOT
    / ".project/reconciliations"
    / "servicetracer-demo-api-plan-run1-connector-event-blocked-20260729.json"
)
TERMINAL_RECONCILIATION = (
    ROOT
    / ".project/reconciliations"
    / "servicetracer-demo-api-plan-run1-terminal-20260730.json"
)
PLANNER = ROOT / ".github/workflows/servicetracer-demo-api-subproject-plan.yml"
REMOVED_WORKFLOWS = (
    ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-dispatcher.yml",
    ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-synchronize-dispatcher.yml",
    ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-merge-dispatcher.yml",
    ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-command-dispatcher.yml",
    ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-command-edit-recovery.yml",
)


class ServiceTracerPlanRun1ManualGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
        cls.blocker = json.loads(BLOCKER_RECONCILIATION.read_text(encoding="utf-8"))
        cls.terminal = json.loads(TERMINAL_RECONCILIATION.read_text(encoding="utf-8"))
        cls.planner = PLANNER.read_text(encoding="utf-8")

    def test_failed_intermediary_dispatchers_are_absent(self) -> None:
        for workflow in REMOVED_WORKFLOWS:
            self.assertFalse(workflow.exists(), str(workflow))

    def test_single_authority_is_consumed_terminal_and_non_deploying(self) -> None:
        authorization = self.authorization
        self.assertEqual(authorization["attempt_id"], "servicetracer-demo-api-plan-run1")
        self.assertEqual(authorization["status"], "consumed_terminal_failure")
        self.assertFalse(authorization["active"])
        self.assertEqual(authorization["attempt_limit"], 1)
        self.assertEqual(authorization["attempts_observed"], 1)
        self.assertTrue(authorization["dispatch"]["authorized"])
        self.assertTrue(authorization["dispatch"]["performed"])
        self.assertEqual(authorization["dispatch"]["accepted_run_id"], 30513630134)
        self.assertFalse(authorization["dispatch"]["rerun_authorized"])
        self.assertFalse(authorization["scope"]["deployment_authorized"])
        self.assertFalse(authorization["scope"]["azure_resource_mutation_authorized"])
        self.assertFalse(authorization["terminal"]["azure_login_started"])
        self.assertFalse(authorization["terminal"]["arm_what_if_performed"])

    def test_blocker_reconciliation_remains_historical_predecessor(self) -> None:
        document = self.blocker
        self.assertEqual(document["schema_version"], "project.execution-blocker-reconciliation.v2")
        self.assertEqual(document["status"], "authorized_pending_direct_manual_workflow_dispatch")
        self.assertEqual(document["authority"]["attempts_consumed"], 0)
        self.assertEqual(document["authority"]["attempts_remaining"], 1)
        self.assertTrue(document["authority"]["direct_manual_workflow_dispatch_authorized"])
        self.assertFalse(document["authority"]["automatic_dispatch_authorized"])
        self.assertFalse(document["authority"]["deployment_authorized"])
        self.assertFalse(document["observed_execution"]["workflow_dispatch_accepted"])
        self.assertFalse(document["observed_execution"]["azure_authentication_or_query"])
        self.assertFalse(document["observed_execution"]["arm_what_if"])
        self.assertEqual(document["exact_manual_dispatch"]["maximum_monthly_cost_cad"], "25.00")

    def test_terminal_reconciliation_records_confirmation_failure_before_azure(self) -> None:
        document = self.terminal
        self.assertEqual(document["status"], "consumed_terminal_failure")
        self.assertEqual(document["workflow"]["run_id"], 30513630134)
        self.assertEqual(document["result"]["failure_classification"], "confirmation_input_mismatch")
        self.assertTrue(document["authority"]["authorization_consumed"])
        self.assertFalse(document["authority"]["workflow_rerun_authorized"])
        self.assertFalse(document["result"]["azure_login_started"])
        self.assertFalse(document["operation_boundary"]["arm_validation_performed"])
        self.assertFalse(document["operation_boundary"]["arm_what_if_performed"])
        self.assertFalse(document["operation_boundary"]["azure_mutations_performed"])
        self.assertFalse(document["operation_boundary"]["deployment_started"])

    def test_canonical_planner_remains_dual_subscription_and_non_deploying(self) -> None:
        for marker in (
            "workflow_dispatch:",
            "environment: azure-api-payg",
            "AZURE_DEPENDENCY_CLIENT_ID",
            "AZURE_TARGET_CLIENT_ID",
            "AZURE_DEPENDENCY_SUBSCRIPTION_ID",
            "AZURE_TARGET_SUBSCRIPTION_ID",
            "ProviderNoRbac",
            "az deployment sub validate",
            "az deployment sub what-if",
        ):
            self.assertIn(marker, self.planner)
        self.assertNotIn("az deployment sub create", self.planner)
        self.assertNotIn("az role assignment create", self.planner)


if __name__ == "__main__":
    unittest.main()
