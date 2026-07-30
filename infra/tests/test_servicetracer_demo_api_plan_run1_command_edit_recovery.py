from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "servicetracer-demo-api-plan-run1-command-edit-recovery.yml"
)


class ServiceTracerPlanRun1CommandEditRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_event_is_exactly_one_edited_anthony_comment(self) -> None:
        workflow = self.workflow
        self.assertIn("issue_comment:", workflow)
        self.assertIn("types: [edited]", workflow)
        self.assertIn("github.event.issue.number == 232", workflow)
        self.assertIn("github.event.issue.pull_request == null", workflow)
        self.assertIn("github.event.comment.id == 5126207104", workflow)
        self.assertIn(
            "github.event.comment.user.login == 'anthonyedgar30000'",
            workflow,
        )
        self.assertIn(
            "EXECUTE-SERVICETRACER-PLAN-RUN1-EDIT1:",
            workflow,
        )
        self.assertIn(
            "^EXECUTE-SERVICETRACER-PLAN-RUN1-EDIT1:([0-9a-f]{40})$",
            workflow,
        )

    def test_workflow_uses_immutable_main_and_exact_comment_ledger(self) -> None:
        workflow = self.workflow
        self.assertIn("ref: main", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('[[ "$observed_main" == "$command_main" ]]', workflow)
        self.assertIn('[[ "$(git rev-parse HEAD)" == "$command_main" ]]', workflow)
        self.assertIn("edited_count", workflow)
        self.assertIn("consumed_count", workflow)
        self.assertIn("command_comment_id:($command_comment_id|tonumber)", workflow)
        self.assertIn("event:\"issue_comment.edited\"", workflow)

    def test_authority_is_consumed_before_child_dispatch(self) -> None:
        workflow = self.workflow
        marker = "<!-- servicetracer-demo-api-plan-run1-consumed -->"
        consume_step = "Consume the one-shot authority before dispatch"
        dispatch = "gh workflow run servicetracer-demo-api-subproject-plan.yml"
        self.assertIn(marker, workflow)
        self.assertIn(consume_step, workflow)
        self.assertIn(dispatch, workflow)
        self.assertLess(workflow.index(consume_step), workflow.index(dispatch))
        self.assertIn("authority_consumed:true", workflow)
        self.assertIn("retry_authorized:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)

    def test_exact_child_inputs_and_non_mutation_boundary(self) -> None:
        workflow = self.workflow
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
        ):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
