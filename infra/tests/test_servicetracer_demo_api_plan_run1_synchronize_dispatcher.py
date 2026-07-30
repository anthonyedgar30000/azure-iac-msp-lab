from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-synchronize-dispatcher.yml"


class ServiceTracerPlanRun1SynchronizeDispatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_recovery_is_exactly_scoped_to_trigger_pr_synchronize(self) -> None:
        workflow = self.workflow
        self.assertIn("pull_request_target:", workflow)
        self.assertIn("types: [synchronize]", workflow)
        self.assertIn("github.event.pull_request.number == 238", workflow)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", workflow)
        self.assertIn("trigger/servicetracer-demo-api-plan-run1", workflow)
        self.assertIn("trigger_generation == 3", workflow)
        self.assertIn("synchronize_recovery_requested == true", workflow)

    def test_write_token_never_checks_out_pull_request_code(self) -> None:
        workflow = self.workflow
        self.assertIn("ref: ${{ github.event.pull_request.base.sha }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("contents/$TRIGGER_FILE?ref=$TRIGGER_HEAD_SHA", workflow)
        self.assertNotIn("ref: ${{ github.event.pull_request.head.sha }}", workflow)
        self.assertNotIn("refs/pull/", workflow)

    def test_authority_is_consumed_before_child_dispatch_and_cannot_repeat(self) -> None:
        workflow = self.workflow
        marker = "<!-- servicetracer-demo-api-plan-run1-consumed -->"
        consume_step = "Consume the one-shot authority before dispatch"
        dispatch_command = "gh workflow run servicetracer-demo-api-subproject-plan.yml"
        self.assertIn(marker, workflow)
        self.assertIn("issues/232/comments?per_page=100", workflow)
        self.assertIn(consume_step, workflow)
        self.assertIn(dispatch_command, workflow)
        self.assertLess(workflow.index(consume_step), workflow.index(dispatch_command))
        self.assertIn("authority_consumed:true", workflow)
        self.assertIn("retry_authorized:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)

    def test_child_is_the_ratified_non_deploying_planner(self) -> None:
        workflow = self.workflow
        self.assertIn("gh workflow run servicetracer-demo-api-subproject-plan.yml", workflow)
        self.assertIn("--ref main", workflow)
        self.assertIn('-f environment="$LAB_ENVIRONMENT"', workflow)
        self.assertIn('-f maximum_monthly_cost_cad="$MAXIMUM_MONTHLY_COST_CAD"', workflow)
        self.assertIn('-f confirmation="$CONFIRMATION"', workflow)
        for forbidden in (
            "az deployment sub create",
            "az group create",
            "az provider register",
            "az role assignment create",
            "gh run rerun",
        ):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
