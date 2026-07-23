from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "infra"
PLAN_VERIFIER_PATH = INFRA / "scripts" / "verify_existing_collector_publication_plan.py"
EXECUTOR_PATH = INFRA / "scripts" / "execute_existing_collector_report_publication.sh"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "existing-collector-report-publication.yml"


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


if __name__ == "__main__":
    unittest.main()
