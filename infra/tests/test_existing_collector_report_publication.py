from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "infra"
MODULE = (INFRA / "modules" / "report_publication.bicep").read_text(
    encoding="utf-8"
)
TEMPLATE = (INFRA / "report-publication-existing-collector.bicep").read_text(
    encoding="utf-8"
)
PLANNER_PATH = INFRA / "scripts" / "plan_existing_collector_report_publication.sh"
PLANNER = PLANNER_PATH.read_text(encoding="utf-8")
PLAN_VERIFIER_PATH = INFRA / "scripts" / "verify_existing_collector_publication_plan.py"
PLAN_VERIFIER = PLAN_VERIFIER_PATH.read_text(encoding="utf-8")
EXECUTOR_PATH = INFRA / "scripts" / "execute_existing_collector_report_publication.sh"
EXECUTOR = EXECUTOR_PATH.read_text(encoding="utf-8")
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "existing-collector-report-publication.yml"
WORKFLOW = WORKFLOW_PATH.read_text(encoding="utf-8")


class ExistingCollectorReportPublicationTests(unittest.TestCase):
    def test_promoted_publication_files_are_present_and_parse(self) -> None:
        self.assertTrue(WORKFLOW_PATH.is_file())
        self.assertTrue(PLAN_VERIFIER_PATH.is_file())
        self.assertTrue(EXECUTOR_PATH.is_file())
        py_compile.compile(str(PLAN_VERIFIER_PATH), doraise=True)
        subprocess.run(
            ["bash", "-n", str(EXECUTOR_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_publication_template_preserves_blob_endpoint_boundary(self) -> None:
        for expected in (
            "allowBlobPublicAccess: true",
            "allowSharedKeyAccess: false",
            "defaultToOAuthAuthentication: true",
            "minimumTlsVersion: 'TLS1_2'",
            "publicAccess: 'Blob'",
            "scope: reportStorage",
            "primaryEndpoints.blob",
            "$web/reports/technician-handoff-report.json",
        ):
            self.assertIn(expected, MODULE)
        self.assertNotIn("publicAccess: 'Container'", MODULE)
        self.assertIn("param collectorPrincipalId string", TEMPLATE)
        self.assertIn("module reportPublication './modules/report_publication.bicep'", TEMPLATE)
        for prohibited in (
            "Microsoft.Compute/virtualMachines",
            "Microsoft.Network/networkInterfaces",
            "deployOperationsCollector",
        ):
            self.assertNotIn(prohibited, TEMPLATE)

    def test_read_only_planner_remains_non_mutating(self) -> None:
        subprocess.run(
            ["bash", "-n", str(PLANNER_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("ProviderNoRbac", PLANNER)
        self.assertIn("deployment_authorized: false", PLANNER)
        self.assertIn("azure_mutations_performed: false", PLANNER)
        for prohibited in (
            "az deployment group create",
            "az role assignment create",
            "az storage account create",
            "az vm run-command invoke",
            "az group delete",
            "az resource delete",
        ):
            self.assertNotIn(prohibited, PLANNER)

    def test_plan_verifier_classifies_exact_four_create_architecture(self) -> None:
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

    def test_workflow_is_pinned_to_current_evidence_and_fails_closed(self) -> None:
        for expected in (
            "default: '29979955391'",
            "c3a17f8765fc7b9e43ef5f92a490ee43246ef35e",
            "sha256:cb2b3ec7f9563d376e0ac4bae4e089af03a506ee272573445bf6510b946712bc",
            "environment: azure-lab",
            "id-token: write",
            "current_price_evidence_id",
            "estimated_monthly_cost_cad",
            "maximum_monthly_cost_cad",
            "PUBLISH:${RESOURCE_GROUP}:${collector_vm}:${PLANNER_RUN_ID}",
            "verify_existing_collector_publication_plan.py",
            "execute_existing_collector_report_publication.sh",
        ):
            self.assertIn(expected, WORKFLOW)
        self.assertNotIn("29974111656", WORKFLOW)
        self.assertNotIn("faed857cbd230e55b206ca6ab05adeeca75c98a9a48b0dc43bb04293cde09333", WORKFLOW)
        self.assertEqual(WORKFLOW.count("azure/login@v2"), 1)
        self.assertNotIn("az deployment group create", WORKFLOW)
        self.assertNotIn("infra/main.bicep", WORKFLOW)

    def test_executor_has_one_deployment_and_bounded_rollback(self) -> None:
        self.assertEqual(EXECUTOR.count("az deployment group create"), 1)
        self.assertLess(
            EXECUTOR.index("rollback_required=true"),
            EXECUTOR.index("az deployment group create"),
        )
        for expected in (
            "reviewed four-create boundary",
            "--validation-level Provider",
            "primaryEndpoints.blob",
            "web-container-postchange.json",
            "SERVICETRACER_PUBLISHER_PREFLIGHT_OK",
            "SERVICETRACER_PUBLICATION_OK",
            "DipAvailability",
            "access-control-allow-origin",
            "az role assignment delete --ids",
            "az storage account delete",
            "collector_compute_changed:false",
            "network_changed:false",
            "artifact-manifest.sha256",
        ):
            self.assertIn(expected, EXECUTOR)
        for prohibited in (
            "infra/main.bicep",
            "az vm delete",
            "az disk delete",
            "az network nic delete",
            "az network vnet delete",
            "az network lb delete",
            "az group delete",
        ):
            self.assertNotIn(prohibited, EXECUTOR)


if __name__ == "__main__":
    unittest.main()
