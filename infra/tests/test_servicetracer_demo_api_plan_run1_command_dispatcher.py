from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "servicetracer-demo-api-plan-run1-command-dispatcher.yml"
)


class ServiceTracerPlanRun1CommandDispatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_event_is_exactly_scoped_to_anthony_issue_232_command(self) -> None:
        workflow = self.workflow
        self.assertIn("issue_comment:", workflow)
        self.assertIn("types: [created]", workflow)
        self.assertIn("github.event.issue.number == 232", workflow)
        self.assertIn("github.event.issue.pull_request == null", workflow)
        self.assertIn(
            "github.event.comment.user.login == 'anthonyedgar30000'",
            workflow,
        )
        self.assertIn(
            "startsWith(github.event.comment.body, "
            "'EXECUTE-SERVICETRACER-PLAN-RUN1:')",
            workflow,
        )
        self.assertIn(
            "^EXECUTE-SERVICETRACER-PLAN-RUN1:([0-9a-f]{40})$",
            workflow,
        )

    def test_command_targets_immutable_live_main_and_existing_planner(self) -> None:
        workflow = self.workflow
        self.assertIn("ref: main", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('[[ "$observed_main" == "$command_main" ]]', workflow)
        self.assertIn('[[ "$(git rev-parse HEAD)" == "$command_main" ]]', workflow)
        self.assertIn(
            'git cat-file -e "${command_main}:'
            '.github/workflows/servicetracer-demo-api-subproject-plan.yml"',
            workflow,
        )
        self.assertIn(
            'git cat-file -e "${command_main}:'
            '.github/workflows/servicetracer-demo-api-plan-run1-command-dispatcher.yml"',
            workflow,
        )

    def test_exact_comment_is_unique_and_authority_is_consumed_first(self) -> None:
        workflow = self.workflow
        marker = "<!-- servicetracer-demo-api-plan-run1-consumed -->"
        consume_step = "Consume the one-shot authority before dispatch"
        dispatch_command = "gh workflow run servicetracer-demo-api-subproject-plan.yml"
        self.assertIn(marker, workflow)
        self.assertIn("command_count", workflow)
        self.assertIn("command_id_count", workflow)
        self.assertIn("env.COMMAND_BODY", workflow)
        self.assertIn("command_count\" == '1'", workflow)
        self.assertIn("command_id_count\" == '1'", workflow)
        self.assertIn(consume_step, workflow)
        self.assertIn(dispatch_command, workflow)
        self.assertLess(workflow.index(consume_step), workflow.index(dispatch_command))
        self.assertIn("authority_consumed:true", workflow)
        self.assertIn("retry_authorized:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)

    def test_child_inputs_are_exact_and_no_mutating_or_retry_commands_exist(self) -> None:
        workflow = self.workflow
        self.assertIn("gh workflow run servicetracer-demo-api-subproject-plan.yml", workflow)
        self.assertIn("--ref main", workflow)
        self.assertIn('-f environment="$LAB_ENVIRONMENT"', workflow)
        self.assertIn('-f location="$LOCATION"', workflow)
        self.assertIn('-f prefix="$PREFIX"', workflow)
        self.assertIn(
            '-f dependency_resource_group="$DEPENDENCY_RESOURCE_GROUP"',
            workflow,
        )
        self.assertIn('-f dns_label="$DNS_LABEL"', workflow)
        self.assertIn('-f allowed_origin="$ALLOWED_ORIGIN"', workflow)
        self.assertIn('-f vm_size="$VM_SIZE"', workflow)
        self.assertIn(
            '-f maximum_monthly_cost_cad="$MAXIMUM_MONTHLY_COST_CAD"',
            workflow,
        )
        self.assertIn('-f confirmation="$CONFIRMATION"', workflow)
        for forbidden in (
            "az deployment sub create",
            "az group create",
            "az group delete",
            "az provider register",
            "az role assignment create",
            "gh run rerun",
            "rerun_failed_workflow_run_jobs",
        ):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
