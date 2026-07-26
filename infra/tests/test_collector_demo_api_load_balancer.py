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

    def test_template_uses_only_the_supported_backend_pool_child(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("resource demoApiLoadBalancer 'Microsoft.Network/loadBalancers@2024-05-01'", source)
        self.assertIn("name: loadBalancerName", source)
        self.assertIn(
            "resource demoApiBackendPool 'Microsoft.Network/loadBalancers/backendAddressPools@2024-05-01'",
            source,
        )
        for unsupported_child in (
            "loadBalancers/frontendIPConfigurations@",
            "loadBalancers/probes@",
            "loadBalancers/loadBalancingRules@",
        ):
            self.assertNotIn(unsupported_child, source)

    def test_ip_backend_pool_sets_virtual_network_only_on_address(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertEqual(source.count("virtualNetwork:"), 1)
        self.assertIn("loadBalancerBackendAddresses", source)
        self.assertIn("ipAddress: collectorPrivateIpAddress", source)
        self.assertIn("parent: demoApiLoadBalancer", source)
        self.assertIn("demoApiBackendPool", source)

    def test_extension_waits_for_backend_pool_convergence(self):
        source = MODULE.read_text(encoding="utf-8")
        dependency_block = source.split("dependsOn: [", 1)[1].split("]", 1)[0]
        self.assertIn("demoApiBackendPool", dependency_block)
        self.assertIn("allowDemoApiHttp", dependency_block)
        self.assertIn("allowDemoApiHttps", dependency_block)

    def test_extension_rerun_is_bound_to_the_reviewed_source_commit(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("forceUpdateTag: sourceRef", source)
        self.assertIn("sourceRef", source)

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

    @staticmethod
    def _payload_with_exact_extension_reconciliation():
        payload = CollectorDemoApiTests._valid_payload()
        extension = next(
            item
            for item in payload["changes"]
            if str(item.get("resourceId", "")).endswith(
                "/virtualMachines/vm-stcollector-mst-dev/extensions/servicetracer-demo-api"
            )
        )
        extension["changeType"] = "Modify"
        extension["before"] = {
            "type": "Microsoft.Compute/virtualMachines/extensions",
            "properties": {
                "publisher": "Microsoft.Azure.Extensions",
                "type": "CustomScript",
                "typeHandlerVersion": "2.1",
                "autoUpgradeMinorVersion": True,
                "forceUpdateTag": "0" * 40,
            },
        }
        extension["after"] = {
            "type": "Microsoft.Compute/virtualMachines/extensions",
            "properties": {
                "publisher": "Microsoft.Azure.Extensions",
                "type": "CustomScript",
                "typeHandlerVersion": "2.1",
                "autoUpgradeMinorVersion": True,
                "forceUpdateTag": "a" * 40,
            },
        }
        return payload

    @staticmethod
    def _payload_with_exact_load_balancer_reconciliation():
        payload = CollectorDemoApiTests._valid_payload()
        load_balancer = next(
            item
            for item in payload["changes"]
            if str(item.get("resourceId", "")).endswith(
                "/loadBalancers/lb-st-demo-api-mst-dev"
            )
        )
        load_balancer["changeType"] = "Modify"
        load_balancer["after"]["sku"]["tier"] = "Regional"
        load_balancer["after"]["tags"] = {
            "workload": "azure-iac-msp-lab",
            "environment": "dev",
            "managedBy": "bicep",
            "purpose": "servicetracer-demo",
            "component": "collector-hosted-demo-api-load-balancer",
            "exposure": "public-https",
        }
        load_balancer["before"] = deepcopy(load_balancer["after"])
        load_balancer["before"]["properties"]["backendAddressPools"][0]["properties"] = {
            "loadBalancerBackendAddresses": [
                {
                    "name": "collector",
                    "properties": {"ipAddress": "10.20.40.10"},
                }
            ]
        }
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
        self.assertEqual(result["creates"], 5)
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

    def test_classifier_accepts_exact_failed_extension_reconciliation(self):
        payload = self._payload_with_exact_extension_reconciliation()
        extension = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
        result = self._classify(payload)
        self.assertEqual(
            result["target_resource_states"][
                "/virtualMachines/vm-stcollector-mst-dev/extensions/servicetracer-demo-api"
            ],
            "Modify",
        )
        self.assertIn(extension["resourceId"], result["approved_reconciliations"])
        self.assertEqual(result["creates"], 5)

    def test_classifier_rejects_unbound_or_wrong_extension_reconciliation(self):
        payload = self._payload_with_exact_extension_reconciliation()
        extension = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
        extension["after"]["properties"]["forceUpdateTag"] = "not-a-reviewed-commit"
        with self.assertRaises(SystemExit):
            self._classify(payload)

        payload = self._payload_with_exact_extension_reconciliation()
        extension = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
        extension["after"]["properties"]["publisher"] = "Unexpected.Publisher"
        with self.assertRaises(SystemExit):
            self._classify(payload)

    def test_classifier_accepts_exact_parent_load_balancer_reconciliation(self):
        payload = self._payload_with_exact_load_balancer_reconciliation()
        load_balancer = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
        result = self._classify(payload)
        self.assertEqual(
            result["target_resource_states"]["/loadBalancers/lb-st-demo-api-mst-dev"],
            "Modify",
        )
        self.assertIn(load_balancer["resourceId"], result["approved_reconciliations"])
        self.assertEqual(result["creates"], 5)
        self.assertFalse(result["deployment_authorized"])

    def test_classifier_rejects_load_balancer_modify_outside_exact_contract(self):
        payload = self._payload_with_exact_load_balancer_reconciliation()
        load_balancer = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
        load_balancer["after"]["tags"]["exposure"] = "unexpected"
        with self.assertRaises(SystemExit):
            self._classify(payload)

        payload = self._payload_with_exact_load_balancer_reconciliation()
        load_balancer = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
        load_balancer["after"]["properties"]["backendAddressPools"][0]["properties"] = {
            "loadBalancerBackendAddresses": []
        }
        with self.assertRaises(SystemExit):
            self._classify(payload)

        payload = self._payload_with_exact_load_balancer_reconciliation()
        load_balancer = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
        load_balancer["after"]["sku"]["tier"] = "Global"
        with self.assertRaises(SystemExit):
            self._classify(payload)

    def test_classifier_still_rejects_load_balancer_replace_or_delete(self):
        for change_type in ("Delete", "Replace"):
            payload = self._payload_with_exact_load_balancer_reconciliation()
            load_balancer = next(item for item in payload["changes"] if item.get("changeType") == "Modify")
            load_balancer["changeType"] = change_type
            with self.assertRaises(SystemExit):
                self._classify(payload)


if __name__ == "__main__":
    unittest.main()
