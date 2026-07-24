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

    def _classify(self, *, restricted: bool, family_limit: int):
        compute, network = self._providers()
        return self.assessor.classify(
            vm_size="Standard_B2ats_v2",
            provider_compute=compute,
            provider_network=network,
            sku_records=self._sku(restricted=restricted),
            compute_usage=self._compute_usage(family_limit=family_limit),
            network_usage=self._network_usage(),
            target_resource_group_state={"status": "not_present"},
            existing_target_resources=[],
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
        self.assertFalse(result["azure_mutations_performed"])
        self.assertFalse(result["deployment_authorized"])

    def test_unrestricted_sku_with_quota_is_ready_for_what_if(self) -> None:
        result = self._classify(restricted=False, family_limit=10)
        self.assertEqual(result["status"], "ready_for_arm_what_if")
        self.assertEqual(result["blocking_reasons"], [])
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()
