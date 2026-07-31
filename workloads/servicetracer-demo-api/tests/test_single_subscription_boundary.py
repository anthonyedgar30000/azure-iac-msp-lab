from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml"
README = ROOT / "workloads" / "servicetracer-demo-api" / "README.md"
RUNBOOK = ROOT / "docs" / "runbooks" / "servicetracer-demo-api-student-subscription-boundary.md"
ASSESSOR = ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "assess_target_readiness.py"
CAPTURE_SCRIPT = ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "capture_target_readiness.sh"


class ServiceTracerDemoApiSingleSubscriptionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.capture_script = CAPTURE_SCRIPT.read_text(encoding="utf-8")

    def test_planner_uses_existing_azure_lab_environment(self) -> None:
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertNotIn("environment: azure-api-payg", self.workflow)

    def test_one_identity_and_subscription_are_explicit(self) -> None:
        for marker in ("AZURE_CLIENT_ID", "AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID"):
            self.assertIn(marker, self.workflow)
        for marker in (
            "AZURE_DEPENDENCY_CLIENT_ID",
            "AZURE_TARGET_CLIENT_ID",
            "AZURE_DEPENDENCY_SUBSCRIPTION_ID",
            "AZURE_TARGET_SUBSCRIPTION_ID",
        ):
            self.assertNotIn(marker, self.workflow)
        self.assertEqual(self.workflow.count("uses: azure/login@v2"), 1)
        self.assertIn('subscription_boundary:"single_subscription"', self.workflow)

    def test_dependency_is_read_before_target_planning(self) -> None:
        login = self.workflow.index("Log in to Azure for Students")
        dependency_capture = self.workflow.index("read-only dependency state")
        target_capture = self.workflow.index("provider, policy, quota, SKU, and target resource state")
        what_if = self.workflow.index("Validate and capture Azure for Students What-If")
        self.assertLess(login, dependency_capture)
        self.assertLess(dependency_capture, target_capture)
        self.assertLess(target_capture, what_if)

    def test_provider_no_rbac_preserves_planning_only_boundary(self) -> None:
        self.assertEqual(self.workflow.count("--validation-level ProviderNoRbac"), 2)
        self.assertIn("dependency_resource_group_read_only:true", self.workflow)
        self.assertIn("target_resource_group_planning_only:true", self.workflow)
        self.assertNotIn("az deployment sub create", self.workflow)
        self.assertNotIn("az role assignment create", self.workflow)
        self.assertNotIn("az group delete", self.workflow)
        self.assertNotIn("az resource delete", self.workflow)

    def test_typed_readiness_fails_closed_after_complete_inventory(self) -> None:
        self.assertTrue(ASSESSOR.is_file())
        self.assertTrue(CAPTURE_SCRIPT.is_file())
        self.assertIn("capture_target_readiness.sh", self.workflow)
        self.assertIn("target-readiness-assessment.json", self.capture_script)
        self.assertIn("blocked_target_readiness", ASSESSOR.read_text(encoding="utf-8"))
        target_inventory = self.capture_script.index('az group show --name "$target_resource_group"')
        readiness_assessment = self.capture_script.index("assess_target_readiness.py")
        self.assertLess(target_inventory, readiness_assessment)
        capture_step = self.workflow.index("capture_target_readiness.sh")
        what_if = self.workflow.index("Validate and capture Azure for Students What-If")
        self.assertLess(capture_step, what_if)
        self.assertIn('.status=="ready_for_arm_what_if"', self.capture_script)
        self.assertIn(".blocking_reasons", self.capture_script)
        self.assertIn("exit 1", self.capture_script)

    def test_resource_group_absence_is_not_inferred_from_generic_failure(self) -> None:
        self.assertIn("existing-target-resource-group.error.txt", self.capture_script)
        self.assertIn("group_show_exit_status", self.capture_script)
        self.assertIn("ResourceGroupNotFound", self.capture_script)
        self.assertIn("observation_failed", self.capture_script)
        self.assertIn("resource_list_exit_status", self.capture_script)
        assessor = ASSESSOR.read_text(encoding="utf-8")
        self.assertIn("target_resource_group_observation_failed", assessor)
        self.assertIn("target_resource_inventory_not_authoritative", assessor)

    def test_diagnostic_capture_preserves_command_failures(self) -> None:
        for marker in (
            "azure-inspection-diagnostics.json",
            "provider-compute.error.txt",
            "provider-network.error.txt",
            "target-policy-assignments.error.txt",
            "compute-usage.error.txt",
            "network-usage.error.txt",
            "vm-size-availability.error.txt",
            "exit_status",
            "succeeded",
        ):
            self.assertIn(marker, self.capture_script)

    def test_documentation_preserves_manual_setup_boundary(self) -> None:
        readme = README.read_text(encoding="utf-8")
        runbook = RUNBOOK.read_text(encoding="utf-8")
        for marker in ("azure-lab", "ProviderNoRbac", "single_subscription"):
            self.assertIn(marker, runbook)
        self.assertIn("Azure for Students", readme)
        self.assertIn("does not create GitHub environments", runbook)
        self.assertIn("does not create Azure role assignments", runbook)


if __name__ == "__main__":
    unittest.main()
