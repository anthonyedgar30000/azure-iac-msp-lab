from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ASSESSOR = ROOT / "infra" / "scripts" / "assess_collector_demo_api_readiness.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CollectorDemoApiReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assessor = load_module(ASSESSOR, "collector_demo_api_readiness")

    def _inputs(self, *, current="1", limit="3", pip_status="not_present"):
        return {
            "collector_vm": {
                "name": "vm-stcollector-mst-dev",
                "provisioningState": "Succeeded",
                "powerState": "VM running",
                "hardwareProfile": {"vmSize": "Standard_B1ms"},
            },
            "collector_nic": {
                "ipConfigurations": [{"privateIPAddress": "10.20.40.10"}],
            },
            "collector_module_deployment": {
                "properties": {
                    "parameters": {
                        "adminUsername": {"value": "azureadmin"},
                        "dataDiskSizeGb": {"value": 32},
                        "collectorPort": {"value": 8080},
                        "collectorSourceRepository": {"value": "https://example.invalid/repo.git"},
                        "collectorSourceRef": {"value": "main"},
                    }
                }
            },
            "network_usage": [
                {
                    "name": {
                        "value": "PublicIPAddresses",
                        "localizedValue": "Public IP Addresses",
                    },
                    "currentValue": current,
                    "limit": limit,
                    "unit": "Count",
                }
            ],
            "resource_locks": [],
            "demo_api_public_ip_state": {"status": pip_status},
            "prior_demo_api_resources": [],
            "dns_label": "st-demo-api-aeg30000",
            "location": "westus2",
            "expected_private_ip": "10.20.40.10",
        }

    def test_assessor_compiles(self):
        py_compile.compile(str(ASSESSOR), doraise=True)

    def test_accepts_observed_azure_cli_numeric_strings(self):
        assessment = self.assessor.assess_collector_demo_api_readiness(**self._inputs())
        quota = assessment["public_ip_quota"]
        self.assertTrue(assessment["deployment_decision_ready"])
        self.assertEqual(quota["current_raw"], "1")
        self.assertEqual(quota["current_raw_type"], "string")
        self.assertEqual(quota["limit_raw"], "3")
        self.assertEqual(quota["limit_raw_type"], "string")
        self.assertEqual(quota["current"], 1)
        self.assertEqual(quota["limit"], 3)
        self.assertEqual(quota["remaining"], 2)
        self.assertTrue(quota["sufficient"])

    def test_accepts_integer_quota_values(self):
        assessment = self.assessor.assess_collector_demo_api_readiness(
            **self._inputs(current=1, limit=3)
        )
        self.assertTrue(assessment["deployment_decision_ready"])
        self.assertEqual(assessment["public_ip_quota"]["current_raw_type"], "integer")

    def test_rejects_non_numeric_or_fractional_quota_values(self):
        for current, limit in (("unknown", "3"), ("1", None), ("1.5", "3")):
            with self.subTest(current=current, limit=limit):
                assessment = self.assessor.assess_collector_demo_api_readiness(
                    **self._inputs(current=current, limit=limit)
                )
                self.assertFalse(assessment["deployment_decision_ready"])
                self.assertIn("public_ip_quota_invalid", assessment["blockers"])

    def test_blocks_when_public_ip_quota_has_no_headroom(self):
        assessment = self.assessor.assess_collector_demo_api_readiness(
            **self._inputs(current="3", limit="3")
        )
        self.assertFalse(assessment["deployment_decision_ready"])
        self.assertIn("public_ip_quota_insufficient", assessment["blockers"])
        self.assertEqual(assessment["public_ip_quota"]["remaining"], 0)

    def test_existing_public_ip_does_not_require_new_quota(self):
        assessment = self.assessor.assess_collector_demo_api_readiness(
            **self._inputs(current=None, limit=None, pip_status="observed_existing")
        )
        self.assertTrue(assessment["deployment_decision_ready"])
        self.assertEqual(
            assessment["public_ip_quota"]["status"],
            "not_required_existing_public_ip",
        )


if __name__ == "__main__":
    unittest.main()
