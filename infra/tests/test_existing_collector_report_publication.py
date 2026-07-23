from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
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
PLAN_VERIFIER_PATH = INFRA / "scripts" / "verify_existing_collector_publication_plan.py"
PLAN_VERIFIER = PLAN_VERIFIER_PATH.read_text(encoding="utf-8")
EXECUTOR_PATH = INFRA / "scripts" / "execute_existing_collector_report_publication.sh"
EXECUTOR = EXECUTOR_PATH.read_text(encoding="utf-8")
DESIGN = (
    INFRA / "workflow-designs" / "existing-collector-report-publication.yml"
).read_text(encoding="utf-8")
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "existing-collector-report-publication.yml"
WORKFLOW = WORKFLOW_PATH.read_text(encoding="utf-8")


class ExistingCollectorReportPublicationTests(unittest.TestCase):
    def test_template_is_decoupled_from_collector_compute(self) -> None:
        self.assertIn("param collectorPrincipalId string", TEMPLATE)
        self.assertIn("module reportPublication './modules/report_publication.bicep'", TEMPLATE)
        self.assertIn("collectorPrincipalId: collectorPrincipalId", TEMPLATE)
        for prohibited in (
            "operations_collector_vm",
            "operationsCollector",
            "Microsoft.Compute/virtualMachines",
            "Microsoft.Network/networkInterfaces",
            "deployOperationsCollector",
        ):
            self.assertNotIn(prohibited, TEMPLATE)

    def test_template_exports_blob_browser_endpoint_and_scoped_role(self) -> None:
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
        self.assertIn("allowBlobPublicAccess: true", MODULE)
        self.assertIn("allowSharedKeyAccess: false", MODULE)
        self.assertIn("defaultToOAuthAuthentication: true", MODULE)
        self.assertIn("publicAccess: 'Blob'", MODULE)
        self.assertNotIn("publicAccess: 'Container'", MODULE)
        self.assertIn("scope: reportStorage", MODULE)

    def test_read_only_planner_remains_read_only(self) -> None:
        subprocess.run(
            ["bash", "-n", str(PLANNER_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )
        for expected in (
            "az account show",
            "az group show",
            "az vm show",
            "az storage account list",
            "az role assignment list",
            "az deployment group validate",
            "az deployment group what-if",
            "ProviderNoRbac",
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

    def test_plan_verifier_accepts_only_four_reviewed_creates(self) -> None:
        py_compile.compile(str(PLAN_VERIFIER_PATH), doraise=True)
        for expected in (
            "Expected exactly four Create changes",
            "Microsoft.Storage/storageAccounts/blobServices/containers",
            "$web container is not scoped",
            "publicAccess",
            "allowBlobPublicAccess",
            "allowSharedKeyAccess",
            "Storage Blob Data Contributor",
            "ProviderNoRbac",
            "Microsoft.Compute/",
            "Microsoft.Network/",
            "Microsoft.OperationalInsights/",
        ):
            self.assertIn(expected, PLAN_VERIFIER)

    def test_plan_verifier_classifies_four_create_blob_architecture(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "publication_plan_verifier", PLAN_VERIFIER_PATH
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        storage_id = "/subscriptions/example/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/streportexample"
        principal = "684dcdd6-d61e-4a2e-9f3c-63a5648e76fc"
        origin = "https://anthonyedgar30000.github.io"
        payload = {
            "status": "Succeeded",
            "error": None,
            "changes": [
                {
                    "changeType": "Create",
                    "resourceId": storage_id,
                    "after": {
                        "type": "Microsoft.Storage/storageAccounts",
                        "kind": "StorageV2",
                        "sku": {"name": "Standard_LRS"},
                        "properties": {
                            "allowBlobPublicAccess": True,
                            "allowSharedKeyAccess": False,
                            "defaultToOAuthAuthentication": True,
                            "minimumTlsVersion": "TLS1_2",
                            "publicNetworkAccess": "Enabled",
                            "supportsHttpsTrafficOnly": True,
                        },
                    },
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{storage_id}/blobServices/default",
                    "after": {
                        "type": "Microsoft.Storage/storageAccounts/blobServices",
                        "properties": {
                            "cors": {
                                "corsRules": [
                                    {
                                        "allowedOrigins": [origin],
                                        "allowedMethods": ["GET", "HEAD", "OPTIONS"],
                                    }
                                ]
                            },
                            "isVersioningEnabled": True,
                            "deleteRetentionPolicy": {"enabled": True, "days": 7},
                        },
                    },
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{storage_id}/blobServices/default/containers/$web",
                    "after": {
                        "type": "Microsoft.Storage/storageAccounts/blobServices/containers",
                        "properties": {"publicAccess": "Blob"},
                    },
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{storage_id}/providers/Microsoft.Authorization/roleAssignments/example",
                    "after": {
                        "type": "Microsoft.Authorization/roleAssignments",
                        "properties": {
                            "principalId": principal,
                            "roleDefinitionId": "/subscriptions/example/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe",
                        },
                    },
                },
            ],
        }
        creates, classified_storage_id = module.classify_what_if(
            payload,
            expected_origin=origin,
            expected_collector_principal=principal,
        )
        self.assertEqual(len(creates), 4)
        self.assertEqual(classified_storage_id, storage_id)

    def test_promoted_workflow_pins_current_plan_and_authority(self) -> None:
        self.assertTrue(WORKFLOW_PATH.exists())
        for expected in (
            "name: Existing collector report publication",
            "workflow_dispatch:",
            "actions: read",
            "contents: read",
            "id-token: write",
            "environment: azure-lab",
            "Check out exact reviewed execution state",
            "default: '29974111656'",
            "d181c48bf718c65015f83e04e1bbf9a7bcf152f4",
            "sha256:faed857cbd230e55b206ca6ab05adeeca75c98a9a48b0dc43bb04293cde09333",
            "current_price_evidence_id",
            "estimated_monthly_cost_cad",
            "maximum_monthly_cost_cad",
            "ceiling <= 10.00",
            "PUBLISH:${RESOURCE_GROUP}:${collector_vm}:${PLANNER_RUN_ID}",
            "one $web container Blob-only access configuration",
            "two bounded VM Run Command guest executions",
            "azure/login@v2",
            "verify_existing_collector_publication_plan.py",
            "execute_existing_collector_report_publication.sh",
        ):
            self.assertIn(expected, WORKFLOW)
        self.assertNotIn("infra/main.bicep", WORKFLOW)
        self.assertNotIn("az deployment group create", WORKFLOW)

    def test_executor_has_one_bounded_deployment_and_four_create_guard(self) -> None:
        subprocess.run(
            ["bash", "-n", str(EXECUTOR_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(EXECUTOR.count("az deployment group create"), 1)
        for expected in (
            "infra/report-publication-existing-collector.bicep",
            "--validation-level Provider",
            "reviewed four-create boundary",
            "containers/$web",
            "publicAccess",
            "allowBlobPublicAccess == true",
            "primaryEndpoints.blob",
            "blob.core.windows.net",
            "web-container-postchange.json",
            "Collector managed-identity principal changed after planning",
            "A report Storage account already exists",
            "Current collector Storage role is missing or ambiguous",
        ):
            self.assertIn(expected, EXECUTOR)
        for prohibited in (
            "infra/main.bicep",
            "deployOperationsCollector",
            "az vm delete",
            "az disk delete",
            "az network nic delete",
            "az network vnet delete",
            "az network lb delete",
            "az group delete",
        ):
            self.assertNotIn(prohibited, EXECUTOR)

    def test_executor_uses_real_evidence_and_managed_identity(self) -> None:
        for expected in (
            "DipAvailability",
            "servicetracer.azure_demo",
            "live-transactions.json",
            "servicetracer.collector_cli ingest",
            "--report-view technician-handoff",
            "servicetracer-publish-report",
            "az vm run-command invoke",
            "servicetracer.public-report.v1",
            "access-control-allow-origin",
            "blob_endpoint_verified:true",
            "web_container_blob_public_access_verified:true",
            "real_azure_probe_metrics:true",
            "real_frontend_transactions:true",
            "collector_managed_identity_publication:true",
            "SERVICETRACER_PUBLISHER_PREFLIGHT_OK",
            "SERVICETRACER_PUBLICATION_OK",
            "default_frontend_source_committed:false",
        ):
            self.assertIn(expected, EXECUTOR)

    def test_executor_rolls_back_only_new_publication_resources(self) -> None:
        for expected in (
            "rollback_publication",
            "rollback_required=true",
            "az role assignment delete --ids",
            "az storage account delete",
            "collector_compute_changed:false",
            "network_changed:false",
        ):
            self.assertIn(expected, EXECUTOR)
        self.assertLess(
            EXECUTOR.index("rollback_required=true"),
            EXECUTOR.index("az deployment group create"),
        )

    def test_evidence_manifests_use_portable_relative_paths(self) -> None:
        for source in (WORKFLOW, EXECUTOR):
            self.assertIn("-printf '%P\\0'", source)
            self.assertIn("artifact-manifest.sha256", source)

    def test_design_artifact_remains_fail_closed_history(self) -> None:
        self.assertIn("intentionally outside .github/workflows", DESIGN)
        self.assertIn("DESIGN ONLY", DESIGN)
        self.assertIn("Fail closed before Azure authentication or mutation", DESIGN)
        self.assertIn("exit 64", DESIGN)
        self.assertIn("if: ${{ false }}", DESIGN)
        self.assertNotIn("id-token: write", DESIGN)
        self.assertNotIn("uses: azure/login@v2", DESIGN)
        self.assertNotIn("az deployment group create", DESIGN)


if __name__ == "__main__":
    unittest.main()
