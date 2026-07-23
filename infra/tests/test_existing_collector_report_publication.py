from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "infra"
TEMPLATE = (INFRA / "report-publication-existing-collector.bicep").read_text(
    encoding="utf-8"
)
MODULE = (INFRA / "modules" / "report_publication.bicep").read_text(
    encoding="utf-8"
)
PLANNER_PATH = INFRA / "scripts" / "plan_existing_collector_report_publication.sh"
PLANNER = PLANNER_PATH.read_text(encoding="utf-8")
DESIGN = (
    INFRA / "workflow-designs" / "existing-collector-report-publication.yml"
).read_text(encoding="utf-8")


class ExistingCollectorReportPublicationTests(unittest.TestCase):
    def test_template_is_decoupled_from_collector_compute(self) -> None:
        self.assertIn("param collectorPrincipalId string", TEMPLATE)
        self.assertIn("module reportPublication './modules/report_publication.bicep'", TEMPLATE)
        self.assertIn("collectorPrincipalId: collectorPrincipalId", TEMPLATE)
        self.assertNotIn("operations_collector_vm", TEMPLATE)
        self.assertNotIn("operationsCollector", TEMPLATE)
        self.assertNotIn("Microsoft.Compute/virtualMachines", TEMPLATE)
        self.assertNotIn("Microsoft.Network/networkInterfaces", TEMPLATE)
        self.assertNotIn("deployOperationsCollector", TEMPLATE)

    def test_template_exports_browser_blob_endpoint_and_role_assignment(self) -> None:
        for expected in (
            "output storageAccountName string",
            "output blobEndpoint string",
            "output staticWebsiteEndpoint string",
            "output publicReportContainerName string",
            "output publicReportUrl string",
            "output collectorWriterRoleAssignmentId string",
        ):
            self.assertIn(expected, TEMPLATE)
        self.assertIn("primaryEndpoints.blob", MODULE)
        self.assertIn("$web/reports/technician-handoff-report.json", MODULE)
        self.assertIn("publicAccess: 'Blob'", MODULE)
        self.assertIn("scope: reportStorage", MODULE)

    def test_planner_has_valid_shell_syntax(self) -> None:
        subprocess.run(
            ["bash", "-n", str(PLANNER_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_planner_is_read_only_and_re_resolves_live_identity(self) -> None:
        for expected in (
            "az account show",
            "az group show",
            "az vm show",
            "identity.principalId",
            "canonical GUID",
            "az storage account list",
            "az role assignment list",
            "visible-resource-group-role-assignments-all.json",
            "visible-report-storage-role-assignments-all.json",
            "visible_collector_role_assignment_count",
            "az deployment group validate",
            "az deployment group what-if",
            "deployment_authorized: false",
            "azure_mutations_performed: false",
        ):
            self.assertIn(expected, PLANNER)

        for prohibited in (
            "az deployment group create",
            "az role assignment create",
            "az storage account create",
            "az vm run-command invoke",
            "az group delete",
            "az resource delete",
        ):
            self.assertNotIn(prohibited, PLANNER)

    def test_planner_preserves_cost_and_freshness_boundaries(self) -> None:
        self.assertIn("Maximum monthly cost ceiling cannot exceed CAD 10.00", PLANNER)
        self.assertIn(
            "unresolved_requires_fresh_region_and_subscription_specific_price_evidence",
            PLANNER,
        )
        self.assertIn("deployment_blocked_until_price_review: true", PLANNER)
        self.assertIn("ARM validation and What-If do not provide", PLANNER)

    def test_candidate_workflow_is_inactive_and_fails_closed(self) -> None:
        self.assertFalse(
            (ROOT / ".github" / "workflows" / "existing-collector-report-publication.yml").exists()
        )
        self.assertIn("intentionally outside .github/workflows", DESIGN)
        self.assertIn("DESIGN ONLY", DESIGN)
        self.assertIn("Fail closed before Azure authentication or mutation", DESIGN)
        self.assertIn("exit 64", DESIGN)
        self.assertIn("if: ${{ false }}", DESIGN)
        self.assertNotIn("id-token: write", DESIGN)
        self.assertNotIn("uses: azure/login@v2", DESIGN)
        self.assertNotIn("az deployment group create", DESIGN)

    def test_candidate_contract_limits_scope_and_requires_reverification(self) -> None:
        for expected in (
            "Re-resolve tenant, subscription, resource group, region, and tags",
            "Re-resolve the existing collector system-assigned principal ID",
            "Classify current and obsolete collector-principal role assignments",
            "Run ARM validation and exact What-If",
            "Require human approval of What-If, cost evidence, and any obsolete-role revocation",
            "Deploy only report Storage configuration and current scoped role assignment",
            "Publish a fresh sanitized envelope through the existing collector identity",
            "Remove only explicitly approved obsolete collector-principal assignments",
            "Verify no obsolete publication role remains",
            "Roll back only the new role assignment and report Storage",
        ):
            self.assertIn(expected, DESIGN)


if __name__ == "__main__":
    unittest.main()
