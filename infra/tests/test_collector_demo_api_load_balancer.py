from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "infra" / "modules" / "collector_demo_api.bicep"
WORKFLOW = ROOT / ".github" / "workflows" / "collector-demo-api.yml"


class CollectorDemoApiLoadBalancerRegressionTests(unittest.TestCase):
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

    def test_failed_deploy_always_captures_operations_and_target_inventory(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: always() && inputs.operation == 'deploy'", workflow)
        self.assertIn("az deployment operation group list", workflow)
        self.assertIn("post-deploy-demo-api-load-balancer.json", workflow)
        self.assertIn("post-deploy-legacy-lb-backend-pool.json", workflow)


if __name__ == "__main__":
    unittest.main()
