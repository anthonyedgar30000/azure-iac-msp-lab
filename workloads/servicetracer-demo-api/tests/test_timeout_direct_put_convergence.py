from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "servicetracer-demo-api-timeout-fix-direct-extension-put.yml"
)
RECORD = (
    ROOT
    / ".project"
    / "reconciliations"
    / "timeout-direct-put-convergence-20260725.json"
)
FUTURE_MARKER = (
    ROOT
    / ".project"
    / "authorizations"
    / "servicetracer-demo-api-timeout-fix-direct-put-retry-20260725.json"
)
REMOVED_PATHS = [
    ".github/workflows/servicetracer-demo-api-timeout-fix-deploy-after-deployment-submitter-rbac.yml",
    ".project/authorizations/README-timeout-deployment-submitter-rbac.md",
    ".project/reconciliations/timeout-fix-deployment-submitter-rbac-plan-20260725.json",
    "docs/reviews/timeout-deployment-submitter-rbac-and-workflow-repair.md",
    "infra/rbac/servicetracer-demo-api-deployment-submitter-rbac.bicep",
    "scripts/bootstrap_servicetracer_deployment_submitter_rbac.sh",
    "workloads/servicetracer-demo-api/scripts/assert_effective_arm_permissions.py",
    "workloads/servicetracer-demo-api/tests/fixtures/effective-arm-permissions-authorized.json",
    "workloads/servicetracer-demo-api/tests/fixtures/effective-arm-permissions-missing-deployment-write.json",
    "workloads/servicetracer-demo-api/tests/test_timeout_deployment_rbac_and_workflow_repair.py",
]


class TimeoutDirectPutConvergenceTests(unittest.TestCase):
    def test_direct_workflow_remains_bounded_and_inert_or_explicitly_authorized(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("az deployment group validate", source)
        self.assertIn("az deployment group what-if", source)
        self.assertIn("az rest --method put", source)
        self.assertNotIn("az deployment group create", source)
        self.assertNotIn("Microsoft.Resources/deployments/write", source)
        self.assertNotIn("az role assignment create", source)
        self.assertNotIn("/api/demo/run", source)

        if not FUTURE_MARKER.exists():
            self.assertFalse(FUTURE_MARKER.exists())
            return

        marker = json.loads(FUTURE_MARKER.read_text(encoding="utf-8"))
        self.assertEqual(
            marker["schema_version"],
            "project.azure-deployment-authorization-direct-extension-put.v1",
        )
        self.assertTrue(marker["authorized"])
        self.assertEqual(
            marker["source_binding"]["branch"],
            "fix/pr104-direct-extension-put-remediation",
        )
        self.assertTrue(marker["scope"]["only_existing_extension_update"])
        self.assertEqual(marker["method"]["forward"], "direct_extension_resource_put")
        self.assertEqual(marker["method"]["rollback"], "direct_extension_resource_put")
        self.assertFalse(marker["authority"]["rbac_mutation"])
        self.assertFalse(marker["authority"]["transaction_replay"])
        self.assertFalse(marker["authority"]["cleanup"])

    def test_wrapper_rbac_package_is_absent(self):
        for relative_path in REMOVED_PATHS:
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT / relative_path).exists())

    def test_convergence_record_preserves_truth_boundaries(self):
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        terminal = record["terminal_attempt"]
        self.assertEqual(terminal["protected_run_id"], 30178082566)
        self.assertEqual(terminal["protected_run_conclusion"], "failure")
        self.assertTrue(terminal["arm_validation_succeeded"])
        self.assertTrue(terminal["extension_only_what_if_accepted"])
        self.assertFalse(terminal["extension_mutation_performed"])
        self.assertFalse(terminal["corrected_runtime_deployed"])
        self.assertEqual(terminal["post_attempt_health"], "not_observed")
        self.assertEqual(terminal["authorization_status"], "consumed_terminal_failure")

        decision = record["decision"]
        self.assertEqual(decision["selected_method"], "direct_extension_resource_put")
        self.assertTrue(decision["bicep_validation_preserved"])
        self.assertTrue(decision["extension_only_what_if_preserved"])
        self.assertFalse(decision["resource_group_deployment_wrapper_required"])
        self.assertFalse(decision["additional_deployment_submitter_role_required"])
        self.assertTrue(decision["pr106_repository_package_removed"])

        boundary = record["inert_boundary"]
        self.assertFalse(boundary["marker_present"])
        self.assertFalse(boundary["deployment_retry_authorized"])
        self.assertFalse(boundary["azure_mutation_authorized"])
        self.assertFalse(boundary["rbac_mutation_authorized"])
        self.assertFalse(boundary["pull_request_merge_authorized"])


if __name__ == "__main__":
    unittest.main()
