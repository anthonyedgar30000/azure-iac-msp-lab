from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION = ROOT / ".project/deployment-requests/servicetracer-demo-api-plan-run1.json"
RECONCILIATION = (
    ROOT
    / ".project/reconciliations"
    / "servicetracer-demo-api-plan-run1-connector-event-blocked-20260729.json"
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
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.planner = PLANNER.read_text(encoding="utf-8")

    def test_failed_intermediary_dispatchers_are_absent(self) -> None:
        for workflow in REMOVED_WORKFLOWS:
            self.assertFalse(workflow.exists(), str(workflow))

    def test_single_authority_remains_unconsumed_and_non_deploying(self) -> None:
        authorization = self.authorization
        self.assertEqual(authorization["attempt_id"], "servicetracer-demo-api-plan-run1")
        self.assertEqual(authorization["status"], "authorized_pending_dispatch")
        self.assertTrue(authorization["active"])
        self.assertEqual(authorization["attempt_limit"], 1)
        self.assertTrue(authorization["dispatch"]["authorized"])
        self.assertFalse(authorization["dispatch"]["performed"])
        self.assertFalse(authorization["dispatch"]["rerun_authorized"])
        self.assertFalse(authorization["scope"]["deployment_authorized"])
        self.assertFalse(authorization["scope"]["azure_resource_mutation_authorized"])

    def test_reconciliation_requires_direct_manual_workflow_dispatch(self) -> None:
        document = self.reconciliation
        self.assertEqual(
            document["schema_version"],
            "project.execution-blocker-reconciliation.v2",
        )
        self.assertEqual(
            document["status"],
            "authorized_pending_direct_manual_workflow_dispatch",
        )
        self.assertEqual(document["authority"]["attempts_consumed"], 0)
        self.assertEqual(document["authority"]["attempts_remaining"], 1)
        self.assertTrue(document["authority"]["direct_manual_workflow_dispatch_authorized"])
        self.assertFalse(document["authority"]["automatic_dispatch_authorized"])
        self.assertFalse(document["authority"]["deployment_authorized"])
        self.assertFalse(document["observed_execution"]["workflow_dispatch_accepted"])
        self.assertFalse(document["observed_execution"]["azure_authentication_or_query"])
        self.assertFalse(document["observed_execution"]["arm_what_if"])
        self.assertEqual(document["exact_manual_dispatch"]["maximum_monthly_cost_cad"], "25.00")

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
