from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = (
    ROOT / ".github" / "workflows" / "existing-collector-report-publication-plan.yml"
)
WORKFLOW = WORKFLOW_PATH.read_text(encoding="utf-8")
PLANNER = (
    ROOT / "infra" / "scripts" / "plan_existing_collector_report_publication.sh"
).read_text(encoding="utf-8")
ACTIVE_WORK = json.loads(
    (ROOT / ".project" / "active-work.json").read_text(encoding="utf-8")
)


class ExistingCollectorReportPublicationPlanWorkflowTests(unittest.TestCase):
    def test_workflow_is_manual_oidc_and_protected(self) -> None:
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertNotIn("pull_request:", WORKFLOW)
        self.assertNotIn("push:", WORKFLOW)
        self.assertIn("contents: read", WORKFLOW)
        self.assertIn("id-token: write", WORKFLOW)
        self.assertIn("environment: azure-lab", WORKFLOW)
        self.assertIn("uses: azure/login@v2", WORKFLOW)

    def test_workflow_is_pinned_to_exact_reviewed_commit(self) -> None:
        self.assertIn("reviewed_commit:", WORKFLOW)
        self.assertIn("ref: ${{ inputs.reviewed_commit }}", WORKFLOW)
        self.assertIn('[[ "$(git rev-parse HEAD)" == "$REVIEWED_COMMIT" ]]', WORKFLOW)
        self.assertIn("^[0-9a-f]{40}$", WORKFLOW)

    def test_dispatch_requires_exact_read_only_confirmation(self) -> None:
        self.assertIn(
            "PLAN-PUBLICATION:${RESOURCE_GROUP}:${collector_vm}",
            WORKFLOW,
        )
        self.assertIn("azure_authentication_authorized: true", WORKFLOW)
        self.assertIn("azure_mutations_authorized: false", WORKFLOW)
        self.assertIn("maximum_monthly_cost_cad", WORKFLOW)
        self.assertIn("amount <= 10.00", WORKFLOW)

    def test_workflow_runs_only_the_read_only_planner(self) -> None:
        self.assertIn(
            "infra/scripts/plan_existing_collector_report_publication.sh",
            WORKFLOW,
        )
        self.assertIn("az deployment group validate", PLANNER)
        self.assertIn("az deployment group what-if", PLANNER)
        self.assertIn("deployment_authorized: false", PLANNER)
        self.assertIn("azure_mutations_performed: false", PLANNER)

        prohibited = (
            "az deployment group create",
            "az role assignment create",
            "az role assignment delete",
            "az storage account create",
            "az storage account delete",
            "az vm run-command invoke",
            "az vm create",
            "az vm delete",
            "az resource delete",
            "az group create",
            "az group delete",
        )
        for command in prohibited:
            self.assertNotIn(command, WORKFLOW)
            self.assertNotIn(command, PLANNER)

    def test_evidence_is_always_uploaded(self) -> None:
        self.assertIn("if: always()", WORKFLOW)
        self.assertIn("actions/upload-artifact@v4", WORKFLOW)
        self.assertIn("artifact-manifest.sha256", WORKFLOW)
        self.assertIn("retention-days: 30", WORKFLOW)

    def test_project_state_contains_one_bounded_read_only_grant(self) -> None:
        grants = ACTIVE_WORK.get("bounded_authority_grants")
        self.assertIsInstance(grants, list)
        self.assertEqual(len(grants), 1)
        grant = grants[0]
        self.assertEqual(
            grant["workflow_path"],
            ".github/workflows/existing-collector-report-publication-plan.yml",
        )
        self.assertEqual(grant["operation"], "read_only_azure_planning")
        self.assertTrue(grant["active_workflow_authorized"])
        self.assertTrue(grant["dispatch_authorized"])
        self.assertTrue(grant["azure_authentication_authorized"])
        self.assertFalse(grant["azure_mutations_authorized"])
        self.assertEqual(
            grant["required_confirmation"],
            "PLAN-PUBLICATION:<resource-group>:vm-stcollector-<prefix>-<environment>",
        )
        self.assertEqual(grant["state_semantics"], "bounded_exception_to_false_defaults")


if __name__ == "__main__":
    unittest.main()
