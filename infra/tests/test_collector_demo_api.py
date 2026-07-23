from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import py_compile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "infra" / "main.bicep"
COLLECTOR_MODULE = ROOT / "infra" / "modules" / "operations_collector_vm.bicep"
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
        self.assertIn('MAX_REQUEST_BYTES = 4096', source)
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

    def test_bicep_reuses_collector_and_excludes_app_service(self):
        main = MAIN.read_text(encoding="utf-8")
        module = COLLECTOR_MODULE.read_text(encoding="utf-8")
        edge = EDGE_LB_MODULE.read_text(encoding="utf-8")
        combined = main + module
        self.assertIn("deployCollectorDemoApi", main)
        self.assertIn("operationsNsgName", main)
        self.assertIn("pip-st-demo-api-", module)
        self.assertIn("servicetracer-demo-api", module)
        self.assertIn("Allow-Demo-API-HTTP-From-Internet", module)
        self.assertIn("Allow-Demo-API-HTTPS-From-Internet", module)
        self.assertIn("publicIpAddress string", edge)
        self.assertNotIn("Microsoft.Web", combined)
        self.assertNotIn("Microsoft.Storage/storageAccounts", combined)

    def test_workflow_is_exact_commit_bound_and_app_service_free(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("reviewed_commit", workflow)
        self.assertIn("COLLECTOR-DEMO-API:", workflow)
        self.assertIn("--no-pretty-print", workflow)
        self.assertIn("deployment_decision_ready", workflow)
        self.assertIn("assert_collector_demo_api_what_if.py", workflow)
        self.assertIn("collectorDemoApiSourceRef=\"$REVIEWED_COMMIT\"", workflow)
        self.assertNotIn("az functionapp", workflow)
        self.assertNotIn("Microsoft.Web/serverfarms", workflow)

    def test_source_configuration_uses_collector_dns_endpoint(self):
        config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(
            config["live_demo_api_url"],
            "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run",
        )

    def test_classifier_accepts_only_expected_collector_changes(self):
        suffix = "mst-dev"
        payload = {
            "status": "Succeeded",
            "error": None,
            "changes": [
                {
                    "changeType": "Create",
                    "resourceId": f"/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/publicIPAddresses/pip-st-demo-api-{suffix}",
                    "after": {"type": "Microsoft.Network/publicIPAddresses"},
                },
                {
                    "changeType": "Create",
                    "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/networkSecurityGroups/nsg-operations-mst-dev/securityRules/Allow-Demo-API-HTTPS-From-Internet",
                    "after": {"type": "Microsoft.Network/networkSecurityGroups/securityRules"},
                },
                {
                    "changeType": "Modify",
                    "resourceId": f"/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/networkInterfaces/nic-stcollector-{suffix}",
                    "before": {
                        "properties": {
                            "enableAcceleratedNetworking": False,
                            "ipConfigurations": [
                                {
                                    "properties": {
                                        "privateIPAddress": "10.20.40.10",
                                        "privateIPAllocationMethod": "Static",
                                        "subnet": {"id": "/subscriptions/x/subnets/snet-operations"},
                                    }
                                }
                            ],
                        }
                    },
                    "after": {
                        "properties": {
                            "enableAcceleratedNetworking": False,
                            "ipConfigurations": [
                                {
                                    "properties": {
                                        "privateIPAddress": "10.20.40.10",
                                        "privateIPAllocationMethod": "Static",
                                        "subnet": {"id": "/subscriptions/x/subnets/snet-operations"},
                                        "publicIPAddress": {
                                            "id": f"/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/publicIPAddresses/pip-st-demo-api-{suffix}"
                                        },
                                    }
                                }
                            ],
                        }
                    },
                },
            ],
        }
        result = self.classifier.classify(
            payload,
            suffix=suffix,
            private_ip="10.20.40.10",
        )
        self.assertEqual(result["creates"], 2)
        self.assertEqual(len(result["accepted_collector_nic_modifies"]), 1)
        self.assertFalse(result["deployment_authorized"])

    def test_classifier_rejects_microsoft_web_and_other_vm_changes(self):
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
                            "changeType": "Modify",
                            "resourceId": "/subscriptions/x/providers/Microsoft.Compute/virtualMachines/vm-stcollector-mst-dev",
                        }
                    ],
                },
                suffix="mst-dev",
                private_ip="10.20.40.10",
            )


if __name__ == "__main__":
    unittest.main()
