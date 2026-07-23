from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ASSESSOR = ROOT / "infra" / "scripts" / "assess_demo_planning_context.py"
WORKFLOW = ROOT / ".github" / "workflows" / "demo-backend-api.yml"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DemoPlanningContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assessor = load_module(ASSESSOR, "demo_planning_context_assessor")

    def test_assessor_compiles(self):
        py_compile.compile(str(ASSESSOR), doraise=True)

    def _assessment(self, *, total_current=2, total_limit=10, family_current=0, family_limit=10):
        return self.assessor.assess_demo_planning_context(
            azure_context={
                "subscriptionId": "00000000-0000-0000-0000-000000000001",
                "tenantId": "00000000-0000-0000-0000-000000000002",
            },
            resource_group={
                "name": "rg-servicetracer-dev-westus2",
                "location": "westus2",
            },
            compute_usage=[
                {
                    "name": {"value": "cores", "localizedValue": "Total Regional vCPUs"},
                    "currentValue": total_current,
                    "limit": total_limit,
                },
                {
                    "name": {"value": "standardBSFamily", "localizedValue": "Standard BS Family vCPUs"},
                    "currentValue": family_current,
                    "limit": family_limit,
                },
            ],
            vm_skus=[
                {
                    "name": "Standard_B1s",
                    "resourceType": "virtualMachines",
                    "locations": ["westus2"],
                    "family": "standardBSFamily",
                    "restrictions": [],
                    "capabilities": [{"name": "vCPUs", "value": "1"}],
                }
            ],
            policy_assignments=[{"name": "policy-1", "enforcementMode": "Default"}],
            role_assignments=[{"roleDefinitionName": "Contributor", "scope": "/subscriptions/x/resourceGroups/y"}],
            deny_assignments=[],
            resource_locks=[],
            retail_prices={
                "Items": [
                    {
                        "currencyCode": "CAD",
                        "retailPrice": 0.02,
                        "armRegionName": "westus2",
                        "meterName": "B1s",
                        "productName": "Virtual Machines BS Series",
                        "unitOfMeasure": "1 Hour",
                        "type": "Consumption",
                        "isPrimaryMeterRegion": True,
                        "armSkuName": "Standard_B1s",
                        "effectiveStartDate": "2026-07-01T00:00:00Z",
                    },
                    {
                        "currencyCode": "CAD",
                        "retailPrice": 0.01,
                        "armRegionName": "westus2",
                        "meterName": "B1s Spot",
                        "productName": "Virtual Machines BS Series",
                        "unitOfMeasure": "1 Hour",
                        "type": "Consumption",
                        "isPrimaryMeterRegion": True,
                        "armSkuName": "Standard_B1s",
                    },
                    {
                        "currencyCode": "CAD",
                        "retailPrice": 0.03,
                        "armRegionName": "westus2",
                        "meterName": "B1s",
                        "productName": "Virtual Machines BS Series Windows",
                        "unitOfMeasure": "1 Hour",
                        "type": "Consumption",
                        "isPrimaryMeterRegion": True,
                        "armSkuName": "Standard_B1s",
                    },
                ]
            },
            resource_group_name="rg-servicetracer-dev-westus2",
            location="westus2",
            backend_vm_size="Standard_B1s",
            backend_vm_count=2,
        )

    def test_assessment_proves_sku_quota_and_cad_retail_estimate(self):
        assessment = self._assessment()
        self.assertEqual(assessment["classification"], "verified_with_limitations")
        self.assertTrue(assessment["planning_context_complete"])
        self.assertTrue(assessment["quota"]["regional_total_sufficient"])
        self.assertTrue(assessment["quota"]["vm_family_sufficient"])
        self.assertEqual(assessment["retail_vm_price"]["currency"], "CAD")
        self.assertEqual(assessment["retail_vm_price"]["hourly_rate_each"], 0.02)
        self.assertEqual(
            assessment["retail_vm_price"]["estimated_730_hour_month_for_all_backends"],
            29.2,
        )
        self.assertFalse(assessment["deployment_decision_ready"])
        self.assertFalse(assessment["azure_mutations_authorized"])
        self.assertIn("remaining_subscription_credit_not_observable", assessment["limitations"])

    def test_assessment_blocks_when_family_quota_is_insufficient(self):
        assessment = self._assessment(family_current=1, family_limit=2)
        self.assertEqual(assessment["classification"], "partially_verified")
        self.assertFalse(assessment["planning_context_complete"])
        self.assertIn("vm_family_quota_not_proven_sufficient", assessment["blockers"])

    def test_assessment_preserves_not_observable_authorization_evidence(self):
        assessment = self.assessor.assess_demo_planning_context(
            azure_context={"subscriptionId": "s", "tenantId": "t"},
            resource_group={"name": "rg-servicetracer-dev-westus2", "location": "westus2"},
            compute_usage=[
                {"name": {"value": "cores"}, "currentValue": 0, "limit": 10},
                {"name": {"value": "standardBSFamily"}, "currentValue": 0, "limit": 10},
            ],
            vm_skus=[
                {
                    "name": "Standard_B1s",
                    "resourceType": "virtualMachines",
                    "locations": ["westus2"],
                    "family": "standardBSFamily",
                    "restrictions": [],
                    "capabilities": [{"name": "vCPUs", "value": "1"}],
                }
            ],
            policy_assignments={"status": "not_observable"},
            role_assignments={"status": "not_observable"},
            deny_assignments={"status": "not_observable"},
            resource_locks={"status": "not_observable"},
            retail_prices={"status": "not_observable"},
            resource_group_name="rg-servicetracer-dev-westus2",
            location="westus2",
            backend_vm_size="Standard_B1s",
        )
        self.assertFalse(assessment["deployment_authorized"])
        self.assertIn("workflow_identity_role_assignments_not_observable", assessment["limitations"])
        self.assertIn("deny_assignments_not_observable", assessment["limitations"])

    def test_workflow_declares_read_only_preflight_evidence(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for expected in (
            "az vm list-usage",
            "az vm list-skus",
            "az policy assignment list",
            "az role assignment list",
            "Microsoft.Authorization/denyAssignments",
            "az lock list",
            "prices.azure.com/api/retail/prices",
            "assess_demo_planning_context.py",
        ):
            self.assertIn(expected, workflow)
        self.assertIn("azure_mutations_authorized:($operation==\"deploy\")", workflow)


if __name__ == "__main__":
    unittest.main()
