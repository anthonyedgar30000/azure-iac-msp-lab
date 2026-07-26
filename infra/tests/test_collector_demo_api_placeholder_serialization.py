from __future__ import annotations

import unittest

from infra.tests.test_collector_demo_api_load_balancer import (
    CLASSIFIER,
    CollectorDemoApiLoadBalancerRegressionTests,
    load_module,
)


class CollectorDemoApiPlaceholderSerializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classifier = load_module(
            CLASSIFIER,
            "collector_demo_api_placeholder_serialization_classifier",
        )

    @staticmethod
    def _payload():
        return (
            CollectorDemoApiLoadBalancerRegressionTests
            ._payload_with_exact_load_balancer_reconciliation()
        )

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

    @staticmethod
    def _placeholder(payload):
        load_balancer = next(
            item
            for item in payload["changes"]
            if item.get("changeType") == "Modify"
            and str(item.get("resourceId", "")).endswith(
                "/loadBalancers/lb-st-demo-api-mst-dev"
            )
        )
        return load_balancer["after"]["properties"]["backendAddressPools"][0]

    def test_accepts_explicit_empty_parent_pool_properties(self):
        result = self._classify(self._payload())
        self.assertEqual(
            result["target_resource_states"]["/loadBalancers/lb-st-demo-api-mst-dev"],
            "Modify",
        )
        self.assertFalse(result["deployment_authorized"])

    def test_accepts_ARM_omitted_empty_parent_pool_properties(self):
        payload = self._payload()
        del self._placeholder(payload)["properties"]

        result = self._classify(payload)

        self.assertEqual(
            result["target_resource_states"]["/loadBalancers/lb-st-demo-api-mst-dev"],
            "Modify",
        )
        self.assertFalse(result["deployment_authorized"])

    def test_rejects_non_object_or_non_empty_parent_pool_properties(self):
        for properties in (
            None,
            [],
            "empty",
            {"loadBalancerBackendAddresses": []},
            {"virtualNetwork": {"id": "/unexpected"}},
            {"subnet": {"id": "/unexpected"}},
        ):
            with self.subTest(properties=properties):
                payload = self._payload()
                self._placeholder(payload)["properties"] = properties
                with self.assertRaises(SystemExit):
                    self._classify(payload)

    def test_rejects_unexpected_placeholder_sibling_fields(self):
        payload = self._payload()
        placeholder = self._placeholder(payload)
        del placeholder["properties"]
        placeholder["id"] = "/unexpected/parent-pool-decoration"

        with self.assertRaises(SystemExit):
            self._classify(payload)


if __name__ == "__main__":
    unittest.main()
