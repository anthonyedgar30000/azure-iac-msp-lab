from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github" / "workflows" / "azure-lab-lifecycle.yml").read_text(
    encoding="utf-8"
)
VERIFY = (ROOT / "infra" / "scripts" / "verify_collector_deployment.sh").read_text(
    encoding="utf-8"
)


class AzureLifecycleWorkflowTests(unittest.TestCase):
    def test_workflow_is_manual_and_uses_oidc(self) -> None:
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertNotIn("pull_request:", WORKFLOW)
        self.assertNotIn("push:", WORKFLOW)
        self.assertIn("id-token: write", WORKFLOW)
        self.assertIn("uses: azure/login@v2", WORKFLOW)
        self.assertIn("environment: azure-lab", WORKFLOW)

    def test_deployment_is_gated_by_what_if_and_pinned_source(self) -> None:
        self.assertLess(
            WORKFLOW.index("Select VM sizes and run Bicep what-if"),
            WORKFLOW.index("Deploy ServiceTracer infrastructure"),
        )
        self.assertIn("^[0-9a-fA-F]{40}$", WORKFLOW)
        self.assertIn('source_ref="${REQUESTED_SOURCE_REF:-$GITHUB_SHA}"', WORKFLOW)
        self.assertIn("collectorAdminSshPublicKey", WORKFLOW)
        self.assertIn("deployOperationsCollector=true", WORKFLOW)
        self.assertIn("if: inputs.operation == 'deploy'", WORKFLOW)

    def test_capacity_aware_vm_size_selection_is_bounded(self) -> None:
        for expected in (
            "default: auto",
            "az vm list-skus",
            "Standard_B1ms",
            "Standard_B2ms",
            "Standard_D2as_v5",
            "Standard_D2s_v5",
            "sku-validation-attempts.jsonl",
            "SkuNotAvailable",
            "capacity restriction",
            "refusing to hide the error behind SKU fallback",
            "resolved-deployment-plan.json",
        ):
            self.assertIn(expected, WORKFLOW)

    def test_resolved_vm_sizes_are_forwarded_to_deployment(self) -> None:
        for expected in (
            "id: plan",
            "steps.plan.outputs.demo_backend_vm_size",
            "steps.plan.outputs.collector_vm_size",
            "steps.plan.outputs.collector_source_ref",
            'demoBackendVmSize="$DEMO_BACKEND_VM_SIZE"',
            'collectorVmSize="$COLLECTOR_VM_SIZE"',
        ):
            self.assertIn(expected, WORKFLOW)

    def test_demo_compute_and_publication_are_explicit_inputs(self) -> None:
        for expected in (
            "deploy_demo_backends:",
            "demo_backend_vm_size:",
            "deploy_public_report_endpoint:",
            'deployDemoBackends="$DEPLOY_DEMO_BACKENDS"',
            'deployPublicReportEndpoint="$DEPLOY_PUBLIC_REPORT_ENDPOINT"',
            "Verify demo backend inventory",
        ):
            self.assertIn(expected, WORKFLOW)

    def test_existing_resource_group_is_the_guarded_default(self) -> None:
        self.assertIn("default: servicetracer-dev-westus2", WORKFLOW)
        self.assertIn("default: westus2", WORKFLOW)
        self.assertIn("^(rg-)?servicetracer-(dev|test)", WORKFLOW)

    def test_teardown_has_exact_confirmation_and_narrow_group_name(self) -> None:
        self.assertIn("CONFIRM_TEARDOWN", WORKFLOW)
        self.assertIn('[[ "$CONFIRM_TEARDOWN" == "$RESOURCE_GROUP" ]]', WORKFLOW)
        self.assertIn("az group delete --name \"$RESOURCE_GROUP\" --yes", WORKFLOW)

    def test_verification_checks_azure_and_guest_state(self) -> None:
        for expected in (
            "publicIPAddress.id",
            "deleteOption",
            "networkAccessPolicy",
            "publicNetworkAccess",
            "az vm run-command invoke",
            "cloud-init status --wait",
            "mountpoint -q",
            "systemctl restart servicetracer-collector.service",
            "SERVICETRACER_VERIFY_OK",
            "restart_persistence",
        ):
            self.assertIn(expected, VERIFY)

    def test_verification_failure_writes_actionable_evidence(self) -> None:
        for expected in (
            "write_result 'failed'",
            "failure_reason",
            "SERVICETRACER_VERIFY_FAILED",
            "VERIFY_PHASE='cloud-init-wait'",
            "cloud-init status --long",
            "lsblk -f",
            "findmnt",
            "systemctl status servicetracer-collector.service",
            "journalctl -u servicetracer-collector.service",
            "/var/log/cloud-init-output.log",
        ):
            self.assertIn(expected, VERIFY)

    def test_verification_does_not_print_collector_token(self) -> None:
        self.assertIn("source \"\\${TOKEN_FILE}\"", VERIFY)
        self.assertNotIn("echo \"\\${SERVICETRACER_COLLECTOR_TOKEN}", VERIFY)
        self.assertNotIn("set -x", VERIFY)

    def test_non_secret_evidence_is_always_uploaded(self) -> None:
        self.assertIn("Upload lifecycle evidence", WORKFLOW)
        self.assertIn("if: always()", WORKFLOW)
        self.assertIn("actions/upload-artifact@v4", WORKFLOW)
        self.assertIn("azure-context.json", WORKFLOW)
        self.assertIn("collector-verification.json", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
