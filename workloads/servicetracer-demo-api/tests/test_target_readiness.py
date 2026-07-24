from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
ASSESSOR = ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "assess_target_readiness.py"


def load_assessor():
    spec = importlib.util.spec_from_file_location("demo_api_target_readiness", ASSESSOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ServiceTracerDemoApiTargetReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assessor = load_assessor()

    @staticmethod
    def _providers():
        return (
            {"namespace": "Microsoft.Compute", "registrationState": "Registered"},
            {"namespace": "Microsoft.Network", "registrationState": "Registered"},
        )

    @staticmethod
    def _sku(*, restricted: bool):
        return [
            {
                "name": "Standard_B2ats_v2",
                "family": "standardBasv2Family",
                "capabilities": [{"name": "vCPUs", "value": "2"}],
                "restrictions": (
                    [{"reasonCode": "NotAvailableForSubscription", "type": "Location"}]
                    if restricted
                    else []
                ),
            }
        ]

    @staticmethod
    def _compute_usage(*, family_limit: int):
        return [
            {"name": {"value": "cores"}, "currentValue": "0", "limit": "10"},
            {
                "name": {"value": "standardBasv2Family"},
                "currentValue": "0",
                "limit": str(family_limit),
            },
        ]

    @staticmethod
    def _network_usage():
        return [
            {
                "name": {"value": "IPv4StandardSkuPublicIpAddresses"},
                "currentValue": "0",
                "limit": "20",
            }
        ]

    def _classify(
        self,
        *,
        restricted: bool,
        family_limit: int,
        resource_group_state: dict | None = None,
        existing_resources=None,
    ):
        compute, network = self._providers()
        return self.assessor.classify(
            vm_size="Standard_B2ats_v2",
            provider_compute=compute,
            provider_network=network,
            sku_records=self._sku(restricted=restricted),
            compute_usage=self._compute_usage(family_limit=family_limit),
            network_usage=self._network_usage(),
            target_resource_group_state=resource_group_state
            or {
                "status": "not_present",
                "error_code": "ResourceGroupNotFound",
                "group_show_exit_status": 3,
                "evidence_authoritative": True,
            },
            existing_target_resources=([] if existing_resources is None else existing_resources),
        )

    def test_current_evidence_becomes_typed_fail_closed_rejection(self) -> None:
        result = self._classify(restricted=True, family_limit=0)
        self.assertEqual(result["status"], "blocked_target_readiness")
        self.assertIn(
            "requested_vm_size_restricted_for_subscription",
            result["blocking_reasons"],
        )
        self.assertIn("vm_family_vcpu_quota_insufficient", result["blocking_reasons"])
        self.assertTrue(result["checks"]["total_regional_vcpu_quota_sufficient"])
        self.assertTrue(result["checks"]["standard_ipv4_public_ip_quota_sufficient"])
        self.assertTrue(result["checks"]["target_resource_group_state_observed"])
        self.assertFalse(result["azure_mutations_performed"])
        self.assertFalse(result["deployment_authorized"])

    def test_explicit_resource_group_absence_can_reach_what_if(self) -> None:
        result = self._classify(restricted=False, family_limit=10)
        self.assertEqual(result["status"], "ready_for_arm_what_if")
        self.assertEqual(result["blocking_reasons"], [])
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["target_resource_group"]["status"], "not_present")
        self.assertTrue(result["target_resource_group"]["resources_authoritative"])
        self.assertEqual(result["target_resource_group"]["existing_resource_count"], 0)

    def test_existing_resource_group_inventory_can_reach_what_if(self) -> None:
        result = self._classify(
            restricted=False,
            family_limit=10,
            resource_group_state={
                "status": "observed_existing",
                "group_show_exit_status": 0,
                "resource_list_exit_status": 0,
                "evidence_authoritative": True,
            },
            existing_resources=[{"id": "/subscriptions/example/resourceGroups/example/providers/x/y"}],
        )
        self.assertEqual(result["status"], "ready_for_arm_what_if")
        self.assertEqual(result["target_resource_group"]["existing_resource_count"], 1)
        self.assertTrue(result["target_resource_group"]["resources_authoritative"])

    def test_unproven_not_present_label_is_not_explicit_absence(self) -> None:
        result = self._classify(
            restricted=False,
            family_limit=10,
            resource_group_state={
                "status": "not_present",
                "group_show_exit_status": 1,
                "error_code": None,
                "evidence_authoritative": False,
            },
            existing_resources=[],
        )
        self.assertEqual(result["status"], "blocked_target_readiness")
        self.assertIn(
            "target_resource_group_observation_failed",
            result["blocking_reasons"],
        )
        self.assertFalse(result["target_resource_group"]["resources_authoritative"])

    def test_group_show_permission_failure_is_not_absence(self) -> None:
        result = self._classify(
            restricted=False,
            family_limit=10,
            resource_group_state={
                "status": "observation_failed",
                "stage": "group_show",
                "group_show_exit_status": 1,
                "error_code": None,
                "evidence_authoritative": False,
            },
            existing_resources={
                "status": "not_observed",
                "resources": None,
                "evidence_authoritative": False,
            },
        )
        self.assertEqual(result["status"], "blocked_target_readiness")
        self.assertIn(
            "target_resource_group_observation_failed",
            result["blocking_reasons"],
        )
        self.assertIn(
            "target_resource_inventory_not_authoritative",
            result["blocking_reasons"],
        )
        self.assertIsNone(result["target_resource_group"]["existing_resource_count"])
        self.assertFalse(result["target_resource_group"]["resources_authoritative"])

    def test_resource_list_failure_blocks_readiness(self) -> None:
        result = self._classify(
            restricted=False,
            family_limit=10,
            resource_group_state={
                "status": "observation_failed",
                "stage": "resource_list",
                "group_show_exit_status": 0,
                "resource_list_exit_status": 1,
                "evidence_authoritative": False,
            },
            existing_resources={
                "status": "not_observed",
                "resources": None,
                "evidence_authoritative": False,
            },
        )
        self.assertEqual(result["status"], "blocked_target_readiness")
        self.assertEqual(result["target_resource_group"]["stage"], "resource_list")
        self.assertIn(
            "target_resource_inventory_not_authoritative",
            result["blocking_reasons"],
        )


if __name__ == "__main__":
    unittest.main()
