from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from infra.tests.test_collector_demo_api import CollectorDemoApiTests


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "infra" / "modules" / "collector_demo_api.bicep"
WORKFLOW = ROOT / ".github" / "workflows" / "collector-demo-api.yml"
CLASSIFIER = ROOT / "infra" / "scripts" / "assert_collector_demo_api_what_if.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CollectorDemoApiLoadBalancerRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classifier = load_module(CLASSIFIER, "collector_demo_api_public_ip_classifier")

    def test_template_never_declares_existing_load_balancer_children(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("resource demoApiLoadBalancer 'Microsoft.Network/loadBalancers@2024-05-01'", source)
        self.assertIn("name: loadBalancerName", source)
        for child_type in (
            "loadBalancers/frontendIPConfigurations@",
            "loadBalancers/backendAddressPools@",
            "loadBalancers/probes@",
            "loadBalancers/loadBalancingRules@",
        ):
            self.assertNotIn(child_type, source)

    def test_ip_backend_pool_sets_virtual_network_only_on_address(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertEqual(source.count("virtualNetwork:"), 1)
        self.assertIn("loadBalancerBackendAddresses", source)
        self.assertIn("ipAddress: collectorPrivateIpAddress", source)

    def test_public_ip_preserves_observed_platform_properties(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("tier: 'Regional'", source)
        self.assertIn("ddosSettings:", source)
        self.assertIn("protectionMode: 'VirtualNetworkInherited'", source)
        self.assertIn("exposure: 'dedicated-load-balanced-public-https'", source)

    def test_failed_deploy_always_captures_operations_and_target_inventory(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: always() && inputs.operation == 'deploy'", workflow)
        self.assertIn("az deployment operation group list", workflow)
        self.assertIn("post-deploy-demo-api-load-balancer.json", workflow)
        self.assertIn("post-deploy-legacy-lb-backend-pool.json", workflow)

    @staticmethod
    def _payload_with_exact_public_ip_reconciliation():
        payload = CollectorDemoApiTests._valid_payload()
        public_ip = next(
            item
            for item in payload["changes"]
            if str(item.get("resourceId", "")).endswith("/publicIPAddresses/pip-st-demo-api-mst-dev")
        )
        public_ip["changeType"] = "Modify"
        public_ip["after"]["tags"] = {
            "component": "collector-hosted-demo-api",
            "environment": "dev",
            "exposure": "dedicated-load-balanced-public-https",
            "managedBy": "bicep",
            "purpose": "servicetracer-demo",
            "workload": "azure-iac-msp-lab",
        }
        public_ip["before"] = deepcopy(public_ip["after"])
        public_ip["before"]["tags"]["exposure"] = "load-balanced-public-https"
        public_ip["delta"] = [
            {
                "after": "dedicated-load-balanced-public-https",
                "before": "load-balanced-public-https",
                "children": None,
                "path": "tags.exposure",
                "propertyChangeType": "Modify",
            }
        ]
        return payload

    def _classify(self, payload):
        return self.classifier.classify(
            payload,
            suffix="mst-dev",
            private_ip="10.20.40.10",
            virtual_network_id=(
                "/subscriptions/x/resourceGroups/y/providers/"
                "Microsoft.Network/virtualNetworks/vnet-onprem-sim-mst-dev"
            ),
            dns_label="st-demo-api-aeg30000",
        )

    def test_classifier_accepts_only_exact_public_ip_tag_reconciliation(self):
        result = self._classify(self._payload_with_exact_public_ip_reconciliation())
        self.assertEqual(
            result["target_resource_states"]["/publicIPAddresses/pip-st-demo-api-mst-dev"],
            "Modify",
        )
        self.assertEqual(len(result["approved_reconciliations"]), 1)
        self.assertEqual(result["creates"], 4)
        self.assertFalse(result["deployment_authorized"])

    def test_classifier_rejects_public_ip_property_deletion_or_extra_delta(self):
        payload = self._payload_with_exact_public_ip_reconciliation()
        public_ip = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
        public_ip["delta"].append(
            {
                "after": None,
                "before": "Regional",
                "children": None,
                "path": "sku.tier",
                "propertyChangeType": "Delete",
            }
        )
        with self.assertRaises(SystemExit):
            self._classify(payload)


if __name__ == "__main__":
    unittest.main()
