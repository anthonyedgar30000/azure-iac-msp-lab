from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml"
README = ROOT / "workloads" / "servicetracer-demo-api" / "README.md"
RUNBOOK = ROOT / "docs" / "runbooks" / "servicetracer-demo-api-payg-subscription-boundary.md"


class ServiceTracerDemoApiDualSubscriptionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_planner_uses_isolated_github_environment(self) -> None:
        self.assertIn("environment: azure-api-payg", self.workflow)
        self.assertNotIn("environment: azure-lab", self.workflow)

    def test_dependency_and_target_identities_are_explicit_and_distinct(self) -> None:
        required = (
            "AZURE_DEPENDENCY_CLIENT_ID",
            "AZURE_DEPENDENCY_SUBSCRIPTION_ID",
            "AZURE_TARGET_CLIENT_ID",
            "AZURE_TARGET_SUBSCRIPTION_ID",
            "AZURE_TENANT_ID",
        )
        for marker in required:
            self.assertIn(marker, self.workflow)
        self.assertNotIn("secrets.AZURE_SUBSCRIPTION_ID", self.workflow)
        self.assertEqual(self.workflow.count("uses: azure/login@v2"), 2)
        self.assertIn('[[ "$DEPENDENCY_CLIENT_ID" != "$TARGET_CLIENT_ID" ]]', self.workflow)
        self.assertIn('[[ "$DEPENDENCY_SUBSCRIPTION_ID" != "$TARGET_SUBSCRIPTION_ID" ]]', self.workflow)

    def test_dependency_is_read_before_target_planning_login(self) -> None:
        dependency_login = self.workflow.index("Log in to dependency subscription")
        dependency_capture = self.workflow.index("Capture read-only ServiceTracer dependency state")
        target_login = self.workflow.index("Log in to target Azure Plan subscription")
        target_capture = self.workflow.index("Capture target provider, policy, quota, SKU, and resource state")
        what_if = self.workflow.index("Validate and capture target-subscription What-If")
        self.assertLess(dependency_login, dependency_capture)
        self.assertLess(dependency_capture, target_login)
        self.assertLess(target_login, target_capture)
        self.assertLess(target_capture, what_if)

    def test_provider_no_rbac_preserves_read_only_planner(self) -> None:
        self.assertEqual(self.workflow.count("--validation-level ProviderNoRbac"), 2)
        self.assertIn("dependency_subscription_read_only:true", self.workflow)
        self.assertIn("target_subscription_planning_only:true", self.workflow)
        self.assertNotIn("az deployment sub create", self.workflow)
        self.assertNotIn("az role assignment create", self.workflow)
        self.assertNotIn("az group delete", self.workflow)
        self.assertNotIn("az resource delete", self.workflow)

    def test_quota_and_sku_fail_closed_before_what_if(self) -> None:
        self.assertIn("vm-size-assessment.json", self.workflow)
        self.assertIn("compute-quota-assessment.json", self.workflow)
        self.assertIn(".unrestricted_records>0", self.workflow)
        self.assertIn(".sufficient==true", self.workflow)

    def test_documentation_preserves_manual_setup_boundary(self) -> None:
        readme = README.read_text(encoding="utf-8")
        runbook = RUNBOOK.read_text(encoding="utf-8")
        for marker in ("azure-api-payg", "ProviderNoRbac", "dual-subscription"):
            self.assertIn(marker, readme)
            self.assertIn(marker, runbook)
        self.assertIn("does not create GitHub environments", runbook)
        self.assertIn("does not create Azure role assignments", runbook)


if __name__ == "__main__":
    unittest.main()
