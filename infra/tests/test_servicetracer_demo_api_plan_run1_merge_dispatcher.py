from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-merge-dispatcher.yml"
PLANNER = ROOT / ".github/workflows/servicetracer-demo-api-subproject-plan.yml"
AUTHORIZATION = ROOT / ".project/deployment-requests/servicetracer-demo-api-plan-run1.json"


class ServiceTracerPlanRun1MergeDispatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.planner = PLANNER.read_text(encoding="utf-8")
        cls.authorization = AUTHORIZATION.read_text(encoding="utf-8")

    def test_only_exact_merge_trigger_path_activates_dispatcher(self) -> None:
        workflow = self.workflow
        self.assertIn("push:", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("servicetracer-demo-api-plan-run1-merge.json", workflow)
        self.assertIn("parent_count", workflow)
        self.assertIn("[[ \"$parent_count\" == '2' ]]", workflow)
        self.assertIn("git diff --name-status", workflow)
        self.assertIn("merge_authorized == true", workflow)

    def test_authority_is_consumed_durably_before_dispatch(self) -> None:
        workflow = self.workflow
        marker = "<!-- servicetracer-demo-api-plan-run1-consumed -->"
        consume_step = "Consume the one-shot authority before child dispatch"
        dispatch = "gh workflow run servicetracer-demo-api-subproject-plan.yml"
        self.assertIn(marker, workflow)
        self.assertIn("issues/232/comments?per_page=100", workflow)
        self.assertIn(consume_step, workflow)
        self.assertIn(dispatch, workflow)
        self.assertLess(workflow.index(consume_step), workflow.index(dispatch))
        self.assertIn("consume_on_authenticated_attempt == true", workflow)
        self.assertIn("authority_consumed:true", workflow)
        self.assertIn("retry_authorized:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)

    def test_exact_planner_inputs_and_no_mutation_commands(self) -> None:
        workflow = self.workflow
        for marker in (
            '--ref main',
            '-f environment="$LAB_ENVIRONMENT"',
            '-f location="$LOCATION"',
            '-f dependency_resource_group="$DEPENDENCY_RESOURCE_GROUP"',
            '-f vm_size="$VM_SIZE"',
            '-f maximum_monthly_cost_cad="$MAXIMUM_MONTHLY_COST_CAD"',
            '-f confirmation="$CONFIRMATION"',
        ):
            self.assertIn(marker, workflow)
        for forbidden in (
            "az deployment sub create",
            "az group create",
            "az provider register",
            "az role assignment create",
            "gh run rerun",
        ):
            self.assertNotIn(forbidden, workflow)

    def test_child_planner_and_authorization_remain_read_only(self) -> None:
        for marker in (
            "environment: azure-api-payg",
            "AZURE_DEPENDENCY_CLIENT_ID",
            "AZURE_TARGET_CLIENT_ID",
            "ProviderNoRbac",
            "az deployment sub validate",
            "az deployment sub what-if",
        ):
            self.assertIn(marker, self.planner)
        self.assertNotIn("az deployment sub create", self.planner)
        self.assertIn('"deployment_authorized": false', self.authorization)
        self.assertIn('"azure_resource_mutation_authorized": false', self.authorization)
        self.assertIn('"planning_ceiling_cad": "25.00"', self.authorization)


if __name__ == "__main__":
    unittest.main()
