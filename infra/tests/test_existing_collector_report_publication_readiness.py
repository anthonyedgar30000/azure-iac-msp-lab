from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "infra"
SCRIPT_PATH = INFRA / "scripts" / "assess_existing_collector_publication_readiness.py"
WORKFLOW_PATH = (
    ROOT
    / ".github"
    / "workflows"
    / "existing-collector-report-publication-readiness.yml"
)
SCRIPT = SCRIPT_PATH.read_text(encoding="utf-8")
WORKFLOW = WORKFLOW_PATH.read_text(encoding="utf-8")


class ExistingCollectorReportPublicationReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(INFRA / "scripts"))
        spec = importlib.util.spec_from_file_location("publication_readiness", SCRIPT_PATH)
        assert spec is not None
        assert spec.loader is not None
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_workflow_and_script_parse(self) -> None:
        self.assertTrue(WORKFLOW_PATH.is_file())
        self.assertTrue(SCRIPT_PATH.is_file())
        py_compile.compile(str(SCRIPT_PATH), doraise=True)
        subprocess.run(
            ["python", "-m", "py_compile", str(SCRIPT_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_workflow_pins_current_planner_evidence(self) -> None:
        for expected in (
            "name: Existing collector report publication readiness",
            "default: '29979955391'",
            "c3a17f8765fc7b9e43ef5f92a490ee43246ef35e",
            "sha256:cb2b3ec7f9563d376e0ac4bae4e089af03a506ee272573445bf6510b946712bc",
            "READINESS-PUBLICATION:${RESOURCE_GROUP}:${collector_vm}",
            "azure_mutations_authorized:false",
            "vm_run_command_authorized:false",
            "deployment_authorized:false",
            "environment: azure-lab",
            "id-token: write",
            "actions: read",
            "assess_existing_collector_publication_readiness.py",
            "verify_existing_collector_publication_plan.py",
        ):
            self.assertIn(expected, WORKFLOW)

    def test_workflow_and_script_have_no_mutation_commands(self) -> None:
        combined = WORKFLOW + "\n" + SCRIPT
        for prohibited in (
            "az deployment group create",
            "az role assignment create",
            "az role assignment delete",
            "az storage account create",
            "az storage account delete",
            "az vm run-command invoke",
            "az vm delete",
            "az resource delete",
            "az group delete",
            "az policy assignment create",
            "az policy assignment delete",
            "az quota update",
        ):
            self.assertNotIn(prohibited, combined)

    def test_workflow_captures_required_read_only_evidence(self) -> None:
        for expected in (
            "Retail Prices",
            "storage-quota",
            "policy",
            "deny",
            "role",
            "--validation-level",
            "ProviderNoRbac",
            "Provider",
            "artifact-manifest.sha256",
            "Publisher guest preflight remains an execution-time gate",
        ):
            self.assertIn(expected, WORKFLOW + "\n" + SCRIPT)

    def test_cost_estimator_selects_conservative_highest_matching_meters(self) -> None:
        rows = []
        for meter, unit, low, high in (
            ("Hot LRS Data Stored", "1 GB/Month", 0.01, 0.02),
            ("Hot LRS Write Operations", "10K", 0.001, 0.002),
            ("Hot LRS Read Operations", "10K", 0.0004, 0.0008),
            ("Hot LRS Other Operations", "10K", 0.0003, 0.0006),
            ("Hot LRS Data Retrieval", "1 GB", 0.001, 0.002),
        ):
            for price in (low, high):
                rows.append(
                    {
                        "productName": "General Block Blob v2",
                        "skuName": "Hot LRS",
                        "meterName": meter,
                        "unitOfMeasure": unit,
                        "retailPrice": price,
                    }
                )
        estimate = self.module.estimate_cost(rows, 10.0)
        self.assertEqual(estimate["status"], "calculated_conservative_retail_estimate")
        self.assertTrue(estimate["under_ceiling"])
        self.assertEqual(
            estimate["selected_meters"]["data_stored"]["retailPrice"], 0.02
        )
        self.assertGreater(estimate["estimated_monthly_cost_cad"], 2.0)

    def test_cost_estimator_fails_closed_when_a_meter_is_missing(self) -> None:
        estimate = self.module.estimate_cost([], 10.0)
        self.assertEqual(estimate["status"], "unresolved_missing_price_meters")
        self.assertFalse(estimate["under_ceiling"])
        self.assertIsNone(estimate["estimated_monthly_cost_cad"])

    def test_role_action_evaluation_respects_not_actions(self) -> None:
        allowed = {
            "permissions": [
                {
                    "actions": ["Microsoft.Authorization/*"],
                    "notActions": [],
                }
            ]
        }
        denied = {
            "permissions": [
                {
                    "actions": ["Microsoft.Authorization/*"],
                    "notActions": ["Microsoft.Authorization/roleAssignments/write"],
                }
            ]
        }
        self.assertTrue(
            self.module.role_grants_action(
                allowed, "Microsoft.Authorization/roleAssignments/write"
            )
        )
        self.assertFalse(
            self.module.role_grants_action(
                denied, "Microsoft.Authorization/roleAssignments/write"
            )
        )

    def test_assignment_scope_must_cover_future_storage_account(self) -> None:
        resource_group = "/subscriptions/s/resourceGroups/rg"
        future_storage = resource_group + "/providers/Microsoft.Storage/storageAccounts/stx"
        self.assertTrue(
            self.module.assignment_scope_applies(resource_group, future_storage)
        )
        self.assertFalse(
            self.module.assignment_scope_applies(
                "/subscriptions/s/resourceGroups/other", future_storage
            )
        )


if __name__ == "__main__":
    unittest.main()
