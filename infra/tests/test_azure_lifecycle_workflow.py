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
            WORKFLOW.index("Run Bicep validation and what-if"),
            WORKFLOW.index("Deploy collector infrastructure"),
        )
        self.assertIn("^[0-9a-fA-F]{40}$", WORKFLOW)
        self.assertIn("collectorAdminSshPublicKey", WORKFLOW)
        self.assertIn("deployOperationsCollector=true", WORKFLOW)
        self.assertIn("if: inputs.operation == 'deploy'", WORKFLOW)

    def test_teardown_has_exact_confirmation_and_narrow_group_name(self) -> None:
        self.assertIn("CONFIRM_TEARDOWN", WORKFLOW)
        self.assertIn('[[ "$CONFIRM_TEARDOWN" == "$RESOURCE_GROUP" ]]', WORKFLOW)
        self.assertIn("^rg-servicetracer-(dev|test)", WORKFLOW)
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
