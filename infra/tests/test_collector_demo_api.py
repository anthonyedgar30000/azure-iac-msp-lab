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

    def test_bicep_uses_dedicated_load_balancer_and_private_collector(self):
        main = MAIN.read_text(encoding="utf-8")
        isolated = ISOLATED_ROOT.read_text(encoding="utf-8")
        collector = COLLECTOR_MODULE.read_text(encoding="utf-8")
        ingress = INGRESS_MODULE.read_text(encoding="utf-8")
        combined = main + isolated + collector + ingress

        self.assertIn("deployCollectorDemoApi", main)
        self.assertIn("collector_demo_api.bicep", main)
        self.assertIn("collector_demo_api.bicep", isolated)
        self.assertNotIn("network.bicep", isolated)
        self.assertNotIn("operations_collector_vm.bicep", isolated)
        self.assertNotIn("param loadBalancerName", isolated)
        self.assertNotIn("publicIPAddresses", collector)
        self.assertIn("collectorRemainsPrivate bool = true", ingress)
        self.assertIn("pip-st-demo-api-", ingress)
        self.assertIn("lb-st-demo-api-", ingress)
        self.assertIn("Microsoft.Network/loadBalancers@2024-05-01", ingress)
        for unsupported_child in (
            "Microsoft.Network/loadBalancers/frontendIPConfigurations@",
            "Microsoft.Network/loadBalancers/backendAddressPools@",
            "Microsoft.Network/loadBalancers/probes@",
            "Microsoft.Network/loadBalancers/loadBalancingRules@",
        ):
            self.assertNotIn(unsupported_child, ingress)
        self.assertEqual(ingress.count("virtualNetwork:"), 1)
        self.assertIn("servicetracer-demo-api", ingress)
        self.assertIn("Allow-Demo-API-HTTP-From-Internet", ingress)
        self.assertIn("Allow-Demo-API-HTTPS-From-Internet", ingress)
        self.assertNotIn("Microsoft.Web", combined)
        self.assertNotIn("Microsoft.Storage/storageAccounts", combined)

    def test_workflow_is_exact_commit_bound_and_captures_failed_deploy_state(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("reviewed_commit", workflow)
        self.assertIn("COLLECTOR-DEMO-API:", workflow)
        self.assertIn("--no-pretty-print", workflow)
        self.assertIn("deployment_decision_ready", workflow)
        self.assertIn("assert_collector_demo_api_what_if.py", workflow)
        self.assertIn("--template-file infra/collector-demo-api.bicep", workflow)
        self.assertIn('sourceRef="$REVIEWED_COMMIT"', workflow)
        self.assertIn("--virtual-network-id", workflow)
        self.assertIn("--dns-label", workflow)
        self.assertIn("post-deploy-parent-operations.json", workflow)
        self.assertIn("post-deploy-nested-operations.json", workflow)
        self.assertIn("legacy-demo-api-lb-frontend.json", workflow)
        self.assertNotIn("loadBalancerName=", workflow)
        self.assertNotIn("--template-file infra/main.bicep", workflow)
        self.assertNotIn("deployOperationsCollector=true", workflow)
        self.assertNotIn("COLLECTOR_ADMIN_SSH_PUBLIC_KEY", workflow)
        self.assertNotIn("az functionapp", workflow)
        self.assertNotIn("Microsoft.Web/serverfarms", workflow)

    def test_source_configuration_withholds_unverified_endpoint(self):
        config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["live_report_url"], "")
        self.assertEqual(config["live_demo_api_url"], "")
        self.assertEqual(config["fallback_report_url"], "technician-handoff-report.json")

    @staticmethod
    def _valid_payload(*, private_ip="10.20.40.10", vnet_id="/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/virtualNetworks/vnet-onprem-sim-mst-dev"):
        suffix = "mst-dev"
        lb_name = f"lb-st-demo-api-{suffix}"
        lb_id = f"/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/loadBalancers/{lb_name}"
        return {
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
                    "after": {
                        "type": "Microsoft.Network/publicIPAddresses",
                        "properties": {
                            "publicIPAllocationMethod": "Static",
                            "dnsSettings": {"domainNameLabel": "st-demo-api-aeg30000"},
                        },
                    },
                },
                {
                    "changeType": "Create",
                    "resourceId": lb_id,
                    "after": {
                        "type": "Microsoft.Network/loadBalancers",
                        "sku": {"name": "Standard"},
                        "properties": {
                            "frontendIPConfigurations": [
                                {
                                    "name": "fe-public-st-demo-api",
                                    "properties": {
                                        "publicIPAddress": {
                                            "id": f"/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/publicIPAddresses/pip-st-demo-api-{suffix}"
                                        }
                                    },
                                }
                            ],
                            "backendAddressPools": [
                                {
                                    "name": "be-st-demo-api",
                                    "properties": {
                                        "loadBalancerBackendAddresses": [
                                            {
                                                "name": "collector",
                                                "properties": {
                                                    "ipAddress": private_ip,
                                                    "virtualNetwork": {"id": vnet_id},
                                                },
                                            }
                                        ]
                                    },
                                }
                            ],
                            "probes": [
                                {
                                    "name": "probe-tcp-80-st-demo-api",
                                    "properties": {"protocol": "Tcp", "port": 80},
                                }
                            ],
                            "loadBalancingRules": [
                                {
                                    "name": "rule-st-demo-api-http",
                                    "properties": {
                                        "frontendIPConfiguration": {"id": f"{lb_id}/frontendIPConfigurations/fe-public-st-demo-api"},
                                        "backendAddressPool": {"id": f"{lb_id}/backendAddressPools/be-st-demo-api"},
                                        "probe": {"id": f"{lb_id}/probes/probe-tcp-80-st-demo-api"},
                                        "protocol": "Tcp",
                                        "frontendPort": 80,
                                        "backendPort": 80,
                                        "disableOutboundSnat": True,
                                    },
                                },
                                {
                                    "name": "rule-st-demo-api-https",
                                    "properties": {
                                        "frontendIPConfiguration": {"id": f"{lb_id}/frontendIPConfigurations/fe-public-st-demo-api"},
                                        "backendAddressPool": {"id": f"{lb_id}/backendAddressPools/be-st-demo-api"},
                                        "probe": {"id": f"{lb_id}/probes/probe-tcp-80-st-demo-api"},
                                        "protocol": "Tcp",
                                        "frontendPort": 443,
                                        "backendPort": 443,
                                        "disableOutboundSnat": True,
                                    },
                                },
                            ],
                        },
                    },
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/networkSecurityGroups/nsg-operations-mst-dev/securityRules/Allow-Demo-API-HTTP-From-Internet",
                    "after": {
                        "type": "Microsoft.Network/networkSecurityGroups/securityRules",
                        "properties": {"destinationAddressPrefix": private_ip, "destinationPortRange": "80"},
                    },
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/networkSecurityGroups/nsg-operations-mst-dev/securityRules/Allow-Demo-API-HTTPS-From-Internet",
                    "after": {
                        "type": "Microsoft.Network/networkSecurityGroups/securityRules",
                        "properties": {"destinationAddressPrefix": private_ip, "destinationPortRange": "443"},
                    },
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Compute/virtualMachines/vm-stcollector-mst-dev/extensions/servicetracer-demo-api",
                    "after": {"type": "Microsoft.Compute/virtualMachines/extensions"},
                },
            ],
        }

    def _classify(self, payload):
        return self.classifier.classify(
            payload,
            suffix="mst-dev",
            private_ip="10.20.40.10",
            virtual_network_id="/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/virtualNetworks/vnet-onprem-sim-mst-dev",
            dns_label="st-demo-api-aeg30000",
        )

    def test_classifier_accepts_dedicated_load_balancer_and_passive_leftovers(self):
        result = self._classify(self._valid_payload())
        self.assertEqual(result["creates"], 5)
        self.assertEqual(result["ingress_strategy"], "dedicated_standard_load_balancer")
        self.assertEqual(len(result["ignored_managed_leftovers"]), 1)
        self.assertEqual(result["base_infrastructure_modifications"], [])
        self.assertFalse(result["deployment_authorized"])

    def test_classifier_rejects_legacy_load_balancer_child_create(self):
        payload = self._valid_payload()
        payload["changes"].append(
            {
                "changeType": "Create",
                "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/loadBalancers/lb-remote-access-mst-dev/probes/probe-tcp-80-st-demo-api",
                "after": {"type": "Microsoft.Network/loadBalancers/probes"},
            }
        )
        with self.assertRaises(SystemExit):
            self._classify(payload)

    def test_classifier_rejects_wrong_backend_private_ip_or_double_vnet(self):
        with self.assertRaises(SystemExit):
            self._classify(self._valid_payload(private_ip="10.20.40.99"))

        payload = self._valid_payload()
        lb = next(item for item in payload["changes"] if item.get("after", {}).get("type") == "Microsoft.Network/loadBalancers")
        pool = lb["after"]["properties"]["backendAddressPools"][0]["properties"]
        pool["virtualNetwork"] = {"id": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/virtualNetworks/vnet-onprem-sim-mst-dev"}
        with self.assertRaises(SystemExit):
            self._classify(payload)

    def test_classifier_rejects_active_managed_web_and_base_mutation(self):
        with self.assertRaises(SystemExit):
            self._classify(
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
                }
            )

        payload = self._valid_payload()
        payload["changes"].append(
            {
                "changeType": "Modify",
                "resourceId": "/subscriptions/x/providers/Microsoft.Compute/virtualMachines/vm-stcollector-mst-dev",
            }
        )
        with self.assertRaises(SystemExit):
            self._classify(payload)


if __name__ == "__main__":
    unittest.main()
