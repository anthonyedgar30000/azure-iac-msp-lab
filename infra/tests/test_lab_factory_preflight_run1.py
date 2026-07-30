from __future__ import annotations

import importlib.util
import json
import unittest
from decimal import Decimal
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CAPACITY = _load_module(
    "lab_factory_preflight_capacity",
    REPOSITORY_ROOT / "scripts" / "assess_lab_factory_preflight.py",
)
WHAT_IF = _load_module(
    "lab_factory_preflight_what_if",
    REPOSITORY_ROOT / "scripts" / "assert_lab_factory_preflight_what_if.py",
)


class LabFactoryPreflightRun1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.request = json.loads(
            (
                REPOSITORY_ROOT
                / ".project"
                / "deployment-requests"
                / "lab-factory-preflight-run1.json"
            ).read_text(encoding="utf-8")
        )
        cls.contract = json.loads(
            (
                REPOSITORY_ROOT
                / ".project"
                / "contracts"
                / "lab-factory-preflight-v1.json"
            ).read_text(encoding="utf-8")
        )
        cls.selector = json.loads(
            (REPOSITORY_ROOT / ".project" / "CURRENT.json").read_text(encoding="utf-8")
        )
        cls.workflow = (
            REPOSITORY_ROOT
            / ".github"
            / "workflows"
            / "lab-factory-preflight-run1.yml"
        ).read_text(encoding="utf-8")
        cls.executor = (
            REPOSITORY_ROOT / "scripts" / "lab_factory_preflight_run1.sh"
        ).read_text(encoding="utf-8")

    def test_authority_is_one_attempt_and_read_only(self) -> None:
        self.assertEqual(self.request["status"], "active_one_attempt")
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 0)
        authority = self.request["authority"]
        self.assertTrue(authority["merge_triggered_preflight_authorized"])
        self.assertTrue(authority["azure_authentication_authorized"])
        self.assertTrue(authority["azure_read_only_queries_authorized"])
        self.assertTrue(authority["arm_validation_authorized"])
        self.assertTrue(authority["arm_what_if_authorized"])
        for denied in (
            "provider_registration_authorized",
            "azure_mutation_authorized",
            "deployment_authorized",
            "rbac_mutation_authorized",
            "model_call_authorized",
            "automatic_retry_authorized",
            "manual_rerun_authorized",
            "rollback_authorized",
            "cleanup_authorized",
        ):
            self.assertFalse(authority[denied], denied)

    def test_profile_and_cost_boundary_are_exact(self) -> None:
        profile = self.request["profile"]
        self.assertEqual(profile["id"], "servicetracer-demo-api")
        self.assertEqual(profile["version"], "1.0.0")
        self.assertEqual(profile["environment"], "test")
        self.assertEqual(profile["location"], "westus2")
        self.assertEqual(profile["resource_group"], "rg-st-demo-api-test-westus2")
        self.assertEqual(profile["vm_size"], "Standard_F1als_v7")
        self.assertEqual(profile["ttl_hours"], 8)
        self.assertEqual(profile["cost_ceiling_CAD"], 5.0)

    def test_workflow_is_merge_triggered_once(self) -> None:
        self.assertIn("name: Lab Factory preflight run 1", self.workflow)
        self.assertIn("push:", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn('test "$GITHUB_RUN_ATTEMPT" = "1"', self.workflow)
        self.assertIn("bash scripts/lab_factory_preflight_run1.sh", self.workflow)
        self.assertGreaterEqual(self.workflow.count("if: always()"), 3)

    def test_executor_contains_only_read_only_azure_operations(self) -> None:
        for required in (
            "az account show",
            "az provider show",
            "az network public-ip show",
            "az group exists",
            "az network public-ip check-dns-name",
            "az vm list-skus",
            "az vm list-usage",
            "az network list-usages",
            "az deployment sub validate",
            "az deployment sub what-if",
            "--result-format FullResourcePayloads",
        ):
            self.assertIn(required, self.executor)
        for prohibited in (
            "az provider register",
            "az group create",
            "az deployment sub create",
            "az deployment group create",
            "az role assignment create",
            "az group delete",
            "az resource delete",
        ):
            self.assertNotIn(prohibited, self.executor)
        self.assertIn('DEPENDENCY_IP="$dependency_ip"', self.executor)
        self.assertIn('"<dependency-public-ip>"', self.executor)

    def test_current_selector_advances_to_preflight_candidate(self) -> None:
        self.assertEqual(
            self.selector["authoritative_current_reality"],
            ".project/current-reality-v4.json",
        )
        self.assertEqual(
            self.selector["authoritative_state_index"],
            ".project/state-index-v13.json",
        )
        self.assertEqual(
            self.selector["authoritative_handoff"],
            ".project/handoffs/current-state-v3.md",
        )

    def test_capacity_quota_and_cost_assessment_passes_fixture(self) -> None:
        result = CAPACITY.assess(
            sku_inventory=[
                {
                    "name": "Standard_F1als_v7",
                    "family": "standardFalsv7Family",
                    "restrictions": [],
                    "capabilities": [{"name": "vCPUs", "value": "1"}],
                }
            ],
            compute_usage=[
                {
                    "name": {
                        "value": "standardFalsv7Family",
                        "localizedValue": "Standard Falsv7 Family vCPUs",
                    },
                    "currentValue": 0,
                    "limit": 10,
                },
                {
                    "name": {
                        "value": "cores",
                        "localizedValue": "Total Regional vCPUs",
                    },
                    "currentValue": 2,
                    "limit": 20,
                },
            ],
            network_usage=[
                {
                    "name": {
                        "value": "PublicIPAddresses",
                        "localizedValue": "Standard Public IP Addresses",
                    },
                    "currentValue": 2,
                    "limit": 3,
                }
            ],
            retail_prices={
                "Items": [
                    {
                        "armSkuName": "Standard_F1als_v7",
                        "currencyCode": "CAD",
                        "type": "Consumption",
                        "unitOfMeasure": "1 Hour",
                        "retailPrice": 0.05,
                        "productName": "Virtual Machines Falsv7 Series Linux",
                        "skuName": "F1als v7",
                    }
                ]
            },
            vm_size="Standard_F1als_v7",
            ttl_hours=8,
            cost_ceiling_cad=Decimal("5.00"),
        )
        self.assertTrue(result["preflight_capacity_and_cost_passed"])
        self.assertTrue(result["standard_public_ip_quota"]["sufficient"])
        self.assertTrue(result["cost"]["within_ceiling"])
        self.assertEqual(result["cost"]["currency"], "CAD")

    def test_what_if_accepts_contained_create_only_plan(self) -> None:
        payload = {
            "status": "Succeeded",
            "changes": [
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/<subscription-id>/resourceGroups/rg-st-demo-api-test-westus2",
                    "resourceType": "Microsoft.Resources/resourceGroups",
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/<subscription-id>/resourceGroups/rg-st-demo-api-test-westus2/providers/Microsoft.Resources/deployments/servicetracer-demo-api-test",
                    "resourceType": "Microsoft.Resources/deployments",
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/<subscription-id>/resourceGroups/rg-st-demo-api-test-westus2/providers/Microsoft.Compute/virtualMachines/vm-st-demo-api-mst-test",
                    "resourceType": "Microsoft.Compute/virtualMachines",
                },
            ],
        }
        result = WHAT_IF.assess(payload, resource_group="rg-st-demo-api-test-westus2")
        self.assertTrue(result["what_if_passed"])
        self.assertFalse(result["deletes_observed"])
        self.assertTrue(result["scope_contained"])

    def test_what_if_rejects_delete(self) -> None:
        payload = {
            "changes": [
                {
                    "changeType": "Delete",
                    "resourceId": "/subscriptions/<subscription-id>/resourceGroups/rg-st-demo-api-test-westus2",
                    "resourceType": "Microsoft.Resources/resourceGroups",
                }
            ]
        }
        with self.assertRaisesRegex(WHAT_IF.WhatIfError, "unexpected What-If change type"):
            WHAT_IF.assess(payload, resource_group="rg-st-demo-api-test-westus2")

    def test_contract_stops_before_deployment(self) -> None:
        self.assertEqual(
            self.contract["next_gate"],
            "independent evidence review and fresh explicit deployment authority",
        )
        self.assertIn("ARM_deployment_create", self.contract["prohibited_operations"])
        self.assertIn("resource_mutation", self.contract["prohibited_operations"])
        self.assertIn("preflight_passed != deployment_authorized", self.contract["claim_boundaries"])


if __name__ == "__main__":
    unittest.main()
