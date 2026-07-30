from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REQUEST = (
    ROOT
    / ".project"
    / "deployment-requests"
    / "servicetracer-demo-api-subproject-plan-run1.json"
)
DISPATCHER = (
    ROOT
    / ".github"
    / "workflows"
    / "servicetracer-demo-api-subproject-plan-run1-dispatcher.yml"
)
RATIFIED_PLANNER = (
    ROOT
    / ".github"
    / "workflows"
    / "servicetracer-demo-api-subproject-plan.yml"
)


class ServiceTracerDemoApiSubprojectPlanRun1DispatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.dispatcher = DISPATCHER.read_text(encoding="utf-8")
        cls.planner = RATIFIED_PLANNER.read_text(encoding="utf-8")

    def test_request_is_one_shot_read_only_planning_authority(self) -> None:
        request = self.request
        self.assertEqual(
            request["schema_version"],
            "project.servicetracer-demo-api-subproject-plan-request.v1",
        )
        self.assertEqual(request["request_id"], "servicetracer-demo-api-subproject-plan-run1")
        self.assertEqual(request["status"], "authorized_unconsumed")
        self.assertEqual(request["tracking_issue"], 232)
        self.assertEqual(request["source"]["authorized_main"], "1eca6b55e93d7276ada5fb06ffd8707d3895936a")
        self.assertEqual(request["execution"]["workflow"], ".github/workflows/servicetracer-demo-api-subproject-plan.yml")
        self.assertEqual(request["execution"]["environment"], "dev")
        self.assertEqual(request["execution"]["location"], "westus2")
        self.assertEqual(request["execution"]["dns_label"], "st-demo-api-vm-aeg30000")
        self.assertEqual(request["execution"]["maximum_monthly_cost_cad"], 25.0)

        authority = request["authority"]
        self.assertEqual(authority["attempt_limit"], 1)
        self.assertTrue(authority["dependency_subscription_read_only"])
        self.assertTrue(authority["target_subscription_planning_only"])
        self.assertTrue(authority["arm_validation_authorized"])
        self.assertTrue(authority["arm_what_if_authorized"])
        for denied in (
            "provider_registration_authorized",
            "credential_creation_authorized",
            "azure_mutation_authorized",
            "deployment_authorized",
            "rbac_mutation_authorized",
            "automatic_retry_authorized",
            "manual_rerun_authorized",
            "rollback_authorized",
            "cleanup_authorized",
        ):
            self.assertFalse(authority[denied], denied)

    def test_dispatcher_targets_only_the_ratified_manual_planner(self) -> None:
        workflow = self.dispatcher
        self.assertIn("types: [opened]", workflow)
        self.assertIn("actions: write", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("trigger/servicetracer-demo-api-subproject-plan-run1", workflow)
        self.assertIn("gh workflow run servicetracer-demo-api-subproject-plan.yml", workflow)
        self.assertIn("--ref main", workflow)
        self.assertIn('-f environment="$LAB_ENVIRONMENT"', workflow)
        self.assertIn('-f maximum_monthly_cost_cad="$MAXIMUM_MONTHLY_COST_CAD"', workflow)
        self.assertIn('-f confirmation="$CONFIRMATION"', workflow)
        self.assertIn("authority_consumed:true", workflow)
        self.assertIn("retry_authorized:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)
        self.assertNotIn("az deployment sub create", workflow)
        self.assertNotIn("az group create", workflow)
        self.assertNotIn("az role assignment create", workflow)
        self.assertNotIn("az provider register", workflow)

    def test_ratified_planner_remains_dual_subscription_and_non_deploying(self) -> None:
        planner = self.planner
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
            self.assertIn(marker, planner)
        self.assertNotIn("az deployment sub create", planner)
        self.assertNotIn("az role assignment create", planner)


if __name__ == "__main__":
    unittest.main()
