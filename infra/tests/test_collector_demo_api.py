from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import py_compile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "infra" / "main.bicep"
ISOLATED_ROOT = ROOT / "infra" / "collector-demo-api.bicep"
COLLECTOR_MODULE = ROOT / "infra" / "modules" / "operations_collector_vm.bicep"
INGRESS_MODULE = ROOT / "infra" / "modules" / "collector_demo_api.bicep"
EDGE_LB_MODULE = ROOT / "infra" / "modules" / "edge_load_balancer.bicep"
WORKFLOW = ROOT / ".github" / "workflows" / "collector-demo-api.yml"
INSTALLER = ROOT / "infra" / "scripts" / "install_collector_demo_api.sh"
CLASSIFIER = ROOT / "infra" / "scripts" / "assert_collector_demo_api_what_if.py"
CORE = ROOT / "demo_api" / "core.py"
RUNTIME = ROOT / "demo_api" / "runtime.py"
STANDALONE = ROOT / "demo_api" / "standalone_server.py"
SOURCE_CONFIG = ROOT / "docs" / "report-source.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CollectorDemoApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classifier = load_module(CLASSIFIER, "collector_demo_api_classifier")

    def test_python_files_compile(self):
        for path in (CORE, RUNTIME, STANDALONE, CLASSIFIER):
            py_compile.compile(str(path), doraise=True)

    def test_standalone_api_is_loopback_only_and_bounded(self):
        source = STANDALONE.read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1"', source)
        self.assertIn('"8090"', source)
        self.assertIn("MAX_REQUEST_BYTES = 4096", source)
        self.assertIn('"/api/health"', source)
        self.assertIn('"/api/demo/run"', source)
        self.assertIn("normalize_attempts", source)
        self.assertIn("origin_not_allowed", source)

    def test_installer_uses_systemd_nginx_tls_and_rate_limiting(self):
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("servicetracer-demo-api.service", source)
        self.assertIn("ProtectSystem=strict", source)
        self.assertIn("NoNewPrivileges=true", source)
        self.assertIn("limit_req_zone", source)
        self.assertIn("certbot --nginx", source)
        self.assertIn("https://${PUBLIC_FQDN}/api/health", source)
        self.assertNotIn("Microsoft.Web", source)

    def test_bicep_reuses_private_collector_and_load_balancer(self):
        main = MAIN.read_text(encoding="utf-8")
        isolated = ISOLATED_ROOT.read_text(encoding="utf-8")
        collector = COLLECTOR_MODULE.read_text(encoding="utf-8")
        ingress = INGRESS_MODULE.read_text(encoding="utf-8")
        edge = EDGE_LB_MODULE.read_text(encoding="utf-8")
        combined = main + isolated + collector + ingress

        self.assertIn("deployCollectorDemoApi", main)
        self.assertIn("collector_demo_api.bicep", main)
        self.assertIn("collector_demo_api.bicep", isolated)
        self.assertNotIn("network.bicep", isolated)
        self.assertNotIn("operations_collector_vm.bicep", isolated)
        self.assertNotIn("publicIPAddresses", collector)
        self.assertIn("collectorRemainsPrivate bool = true", ingress)
        self.assertIn("pip-st-demo-api-", ingress)
        self.assertIn("loadBalancers/frontendIPConfigurations", ingress)
        self.assertIn("loadBalancers/backendAddressPools", ingress)
        self.assertIn("servicetracer-demo-api", ingress)
        self.assertIn("Allow-Demo-API-HTTP-From-Internet", ingress)
        self.assertIn("Allow-Demo-API-HTTPS-From-Internet", ingress)
        self.assertIn("publicIpAddress string", edge)
        self.assertNotIn("Microsoft.Web", combined)
        self.assertNotIn("Microsoft.Storage/storageAccounts", combined)

    def test_workflow_is_exact_commit_bound_isolated_and_app_service_free(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("reviewed_commit", workflow)
        self.assertIn("COLLECTOR-DEMO-API:", workflow)
        self.assertIn("--no-pretty-print", workflow)
        self.assertIn("deployment_decision_ready", workflow)
        self.assertIn("assert_collector_demo_api_what_if.py", workflow)
        self.assertIn("--template-file infra/collector-demo-api.bicep", workflow)
        self.assertIn('sourceRef="$REVIEWED_COMMIT"', workflow)
        self.assertNotIn("--template-file infra/main.bicep", workflow)
        self.assertNotIn("deployOperationsCollector=true", workflow)
        self.assertNotIn("COLLECTOR_ADMIN_SSH_PUBLIC_KEY", workflow)
        self.assertNotIn("az functionapp", workflow)
        self.assertNotIn("Microsoft.Web/serverfarms", workflow)

    def test_source_configuration_uses_collector_dns_endpoint(self):
        config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(
            config["live_demo_api_url"],
            "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run",
        )

    def test_classifier_accepts_expected_creates_and_passive_leftovers(self):
        suffix = "mst-dev"
        private_ip = "10.20.40.10"
        payload = {
            "status": "Succeeded",
            "error": None,
            "changes": [
                {
                    "changeType": "Ignore",
                    "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Insights/components/appi-demo-api-mst-dev",
                },
                {
                    "changeType": "Create",
                    "resourceId": f"/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/publicIPAddresses/pip-st-demo-api-{suffix}",
                    "after": {"type": "Microsoft.Network/publicIPAddresses"},
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/loadBalancers/lb-remote-access-mst-dev/frontendIPConfigurations/fe-public-st-demo-api",
                    "after": {"type": "Microsoft.Network/loadBalancers/frontendIPConfigurations"},
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/loadBalancers/lb-remote-access-mst-dev/backendAddressPools/be-st-demo-api",
                    "after": {
                        "type": "Microsoft.Network/loadBalancers/backendAddressPools",
                        "properties": {
                            "loadBalancerBackendAddresses": [
                                {"properties": {"ipAddress": private_ip}}
                            ]
                        },
                    },
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/networkSecurityGroups/nsg-operations-mst-dev/securityRules/Allow-Demo-API-HTTPS-From-Internet",
                    "after": {
                        "type": "Microsoft.Network/networkSecurityGroups/securityRules",
                        "properties": {
                            "destinationAddressPrefix": private_ip,
                            "destinationPortRange": "443",
                        },
                    },
                },
            ],
        }
        result = self.classifier.classify(
            payload,
            suffix=suffix,
            private_ip=private_ip,
        )
        self.assertEqual(result["creates"], 4)
        self.assertEqual(len(result["ignored_managed_leftovers"]), 1)
        self.assertEqual(result["collector_nic_modifications"], [])
        self.assertEqual(result["collector_vm_modifications"], [])
        self.assertEqual(result["base_infrastructure_modifications"], [])
        self.assertFalse(result["deployment_authorized"])

    def test_classifier_rejects_active_managed_web_and_base_mutation(self):
        with self.assertRaises(SystemExit):
            self.classifier.classify(
                {
                    "status": "Succeeded",
                    "error": None,
                    "changes": [
                        {
                            "changeType": "Create",
                            "resourceId": "/subscriptions/x/providers/Microsoft.Web/sites/forbidden",
                            "after": {"type": "Microsoft.Web/sites"},
                        }
                    ],
                },
                suffix="mst-dev",
                private_ip="10.20.40.10",
            )

        with self.assertRaises(SystemExit):
            self.classifier.classify(
                {
                    "status": "Succeeded",
                    "error": None,
                    "changes": [
                        {
                            "changeType": "Ignore",
                            "resourceId": "/subscriptions/x/providers/Microsoft.Insights/components/appi-demo-api-mst-dev",
                        },
                        {
                            "changeType": "Modify",
                            "resourceId": "/subscriptions/x/providers/Microsoft.Compute/virtualMachines/vm-stcollector-mst-dev",
                        },
                    ],
                },
                suffix="mst-dev",
                private_ip="10.20.40.10",
            )

    def test_classifier_rejects_wrong_backend_private_ip(self):
        with self.assertRaises(SystemExit):
            self.classifier.classify(
                {
                    "status": "Succeeded",
                    "error": None,
                    "changes": [
                        {
                            "changeType": "Create",
                            "resourceId": "/subscriptions/x/providers/Microsoft.Network/loadBalancers/lb-remote-access-mst-dev/backendAddressPools/be-st-demo-api",
                            "after": {
                                "type": "Microsoft.Network/loadBalancers/backendAddressPools",
                                "properties": {
                                    "loadBalancerBackendAddresses": [
                                        {"properties": {"ipAddress": "10.20.40.99"}}
                                    ]
                                },
                            },
                        }
                    ],
                },
                suffix="mst-dev",
                private_ip="10.20.40.10",
            )


if __name__ == "__main__":
    unittest.main()
