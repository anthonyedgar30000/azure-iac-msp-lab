from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION = ROOT / ".project/deployment-requests/servicetracer-demo-api-plan-run1.json"
DISPATCHER = ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-dispatcher.yml"
PLANNER = ROOT / ".github/workflows/servicetracer-demo-api-subproject-plan.yml"


class ServiceTracerDemoApiPlanRun1DispatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
        cls.dispatcher = DISPATCHER.read_text(encoding="utf-8")
        cls.planner = PLANNER.read_text(encoding="utf-8")

    def test_authorization_is_exactly_one_non_mutating_observation(self) -> None:
        document = self.authorization
        self.assertEqual(document["schema_version"], "project.servicetracer-demo-api-plan-authorization.v1")
        self.assertEqual(document["attempt_id"], "servicetracer-demo-api-plan-run1")
        self.assertEqual(document["status"], "authorized_pending_dispatch")
        self.assertTrue(document["active"])
        self.assertEqual(document["attempt_limit"], 1)
        self.assertTrue(document["dispatch"]["authorized"])
        self.assertFalse(document["dispatch"]["performed"])
        self.assertFalse(document["dispatch"]["rerun_authorized"])
        self.assertEqual(document["inputs"]["environment"], "dev")
        self.assertEqual(document["inputs"]["location"], "westus2")
        self.assertEqual(document["inputs"]["dns_label"], "st-demo-api-vm-aeg30000")
        self.assertEqual(document["inputs"]["maximum_monthly_cost_cad"], "25.00")
        scope = document["scope"]
        self.assertEqual(scope["github_environment"], "azure-api-payg")
        self.assertEqual(scope["subscription_boundary"], "dual_subscription")
        self.assertTrue(scope["arm_validation_authorized"])
        self.assertTrue(scope["arm_what_if_authorized"])
        for denied in (
            "azure_resource_mutation_authorized",
            "deployment_authorized",
            "rbac_mutation_authorized",
            "provider_registration_authorized",
            "cleanup_authorized",
            "rollback_authorized",
        ):
            self.assertFalse(scope[denied], denied)
        self.assertTrue(document["failure_behavior"]["consume_on_authenticated_attempt"])
        self.assertFalse(document["failure_behavior"]["automatic_retry"])
        self.assertFalse(document["failure_behavior"]["manual_rerun"])

    def test_dispatcher_uses_the_ratified_planner_once(self) -> None:
        workflow = self.dispatcher
        self.assertIn("types: [opened]", workflow)
        self.assertIn("actions: write", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn(".project/deployment-requests/servicetracer-demo-api-plan-run1.json", workflow)
        self.assertIn("trigger/servicetracer-demo-api-plan-run1", workflow)
        self.assertIn("gh workflow run servicetracer-demo-api-subproject-plan.yml", workflow)
        self.assertIn("--ref main", workflow)
        self.assertIn('-f environment="$LAB_ENVIRONMENT"', workflow)
        self.assertIn('-f maximum_monthly_cost_cad="$MAXIMUM_MONTHLY_COST_CAD"', workflow)
        self.assertIn('-f confirmation="$CONFIRMATION"', workflow)
        self.assertIn("authority_consumed:true", workflow)
        self.assertIn("retry_authorized:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)
        for forbidden in (
            "az deployment sub create",
            "az group create",
            "az provider register",
            "az role assignment create",
            "gh run rerun",
        ):
            self.assertNotIn(forbidden, workflow)

    def test_ratified_planner_remains_dual_subscription_and_non_deploying(self) -> None:
        for marker in (
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
