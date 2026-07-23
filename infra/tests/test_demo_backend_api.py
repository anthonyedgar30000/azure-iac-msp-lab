from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import py_compile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "demo_api" / "core.py"
FUNCTION = ROOT / "demo_api" / "function_app.py"
ENTRYPOINT = ROOT / "infra" / "demo-backend-api.bicep"
MODULE = ROOT / "infra" / "modules" / "demo_api.bicep"
WORKFLOW = ROOT / ".github" / "workflows" / "demo-backend-api.yml"
FRONTEND = ROOT / "docs" / "app.js"
SOURCE_CONFIG = ROOT / "docs" / "report-source.json"
CLASSIFIER = ROOT / "infra" / "scripts" / "assert_demo_backend_api_what_if.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DemoBackendApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = load_module(CORE, "demo_api_core")
        cls.classifier = load_module(CLASSIFIER, "demo_api_classifier")

    def test_python_files_compile(self):
        py_compile.compile(str(CORE), doraise=True)
        py_compile.compile(str(FUNCTION), doraise=True)
        py_compile.compile(str(CLASSIFIER), doraise=True)

    def test_core_localizes_failed_backend_without_claiming_root_cause(self):
        transactions = [
            {"backend": "VPN-01", "transaction_status": "successful"},
            {"backend": "VPN-01", "transaction_status": "successful"},
            {"backend": "VPN-02", "transaction_status": "failed"},
            {"backend": "VPN-02", "transaction_status": "failed"},
        ]
        report = self.core.build_handoff_report(transactions)
        self.assertEqual(report["localization"]["suspect_backend"], "VPN-02")
        self.assertEqual(report["localization"]["healthy_comparison_backend"], "VPN-01")
        self.assertFalse(report["investigation_boundary"]["exact_root_cause_claimed"])
        self.assertEqual(report["root_cause"]["status"], "not_determined_by_servicetracer")

    def test_attempts_are_bounded(self):
        self.assertEqual(self.core.normalize_attempts(None), 20)
        self.assertEqual(self.core.normalize_attempts("25"), 25)
        for invalid in (0, 1, 51, True, "nope"):
            with self.assertRaises(ValueError):
                self.core.normalize_attempts(invalid)

    def test_function_target_is_configuration_only(self):
        tree = ast.parse(FUNCTION.read_text(encoding="utf-8"))
        source = FUNCTION.read_text(encoding="utf-8")
        self.assertIn("SERVICETRACER_BACKEND_TRANSACTION_URL", source)
        self.assertNotIn("target_url", source)
        self.assertIn('route="demo/run"', source)
        self.assertIn('route="health"', source)
        self.assertGreater(len(list(ast.walk(tree))), 20)

    def test_bicep_scope_excludes_collector(self):
        entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
        module = MODULE.read_text(encoding="utf-8")
        self.assertIn("existing =", entrypoint)
        self.assertIn("remote_access_backends.bicep", entrypoint)
        self.assertIn("demo_api.bicep", entrypoint)
        self.assertNotIn("operations_collector_vm", entrypoint)
        self.assertNotIn("roleAssignments", entrypoint + module)
        self.assertIn("httpsOnly: true", module)
        self.assertIn("minTlsVersion: '1.2'", module)
        self.assertIn("allowedOrigins: allowedOrigins", module)

    def test_workflow_is_scoped_and_exact_commit_bound(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("reviewed_commit", workflow)
        self.assertIn("DEMO-BACKEND-API:", workflow)
        self.assertIn("infra/demo-backend-api.bicep", workflow)
        self.assertIn("az functionapp deployment source config-zip", workflow)
        self.assertNotIn("resolve_vm_plan.sh", workflow)
        self.assertNotIn("deployOperationsCollector", workflow)
        self.assertNotIn("vm-stcollector", workflow)

    def test_frontend_calls_api_and_retains_fallback(self):
        frontend = FRONTEND.read_text(encoding="utf-8")
        config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
        self.assertIn("live_demo_api_url", config)
        self.assertIn("demoApiUrl", frontend)
        self.assertIn("method: 'POST'", frontend)
        self.assertIn("servicetracer.demo-api-response.v1", frontend)
        self.assertIn("using the controlled fixture", frontend)

    def test_what_if_classifier_rejects_modify(self):
        with self.assertRaises(SystemExit):
            self.classifier.classify(
                {
                    "status": "Succeeded",
                    "error": None,
                    "changes": [
                        {
                            "changeType": "Modify",
                            "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Network/loadBalancers/lb",
                        }
                    ],
                }
            )

    def test_what_if_classifier_accepts_expected_creates(self):
        result = self.classifier.classify(
            {
                "status": "Succeeded",
                "error": None,
                "changes": [
                    {
                        "changeType": "Create",
                        "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Web/sites/f",
                        "after": {"type": "Microsoft.Web/sites"},
                    },
                    {
                        "changeType": "Create",
                        "resourceId": "/subscriptions/x/resourceGroups/y/providers/Microsoft.Compute/virtualMachines/vm-vpn01-mst-dev",
                        "after": {"type": "Microsoft.Compute/virtualMachines"},
                    },
                ],
            }
        )
        self.assertEqual(result["creates"], 2)
        self.assertEqual(result["known_nic_noise_modifies"], [])
        self.assertFalse(result["deployment_authorized"])

    def test_pretty_what_if_parser_accepts_expected_changes(self):
        payload = self.classifier.parse_pretty_what_if(
            """Resource and property changes are indicated with these symbols:
  + Create
  = Nochange
  * Ignore

  + Microsoft.Web/sites/func-demo [2024-04-01]
  = Microsoft.Compute/virtualMachines/vm-vpn01-mst-dev [2024-07-01]
  * Microsoft.Network/loadBalancers/lb-remote-access-mst-dev

Resource changes: 1 to create, 1 no change, 1 to ignore.
"""
        )
        result = self.classifier.classify(payload)
        self.assertEqual(result["creates"], 1)
        self.assertEqual(result["create_types"], {"Microsoft.Web/sites": 1})
        self.assertFalse(result["deployment_authorized"])

    def test_pretty_what_if_parser_accepts_exact_backend_nic_noise(self):
        payload = self.classifier.parse_pretty_what_if(
            """Resource and property changes are indicated with these symbols:
  + Create
  ~ Modify

  + Microsoft.Web/sites/func-demo [2024-04-01]
  ~ Microsoft.Network/networkInterfaces/nic-vpn01-mst-dev [2024-05-01]
    - kind:                                                                      "Regular"
    - properties.allowPort25Out:                                                 false
    - properties.auxiliaryMode:                                                  "None"
    - properties.auxiliarySku:                                                   "None"
    - properties.disableTcpStateTracking:                                        false
    ~ properties.ipConfigurations: [
      ~ 0:
        - properties.privateIPAddressVersion: "IPv4"
      ]

Resource changes: 1 to create, 1 to modify.
"""
        )
        result = self.classifier.classify(payload)
        self.assertEqual(result["creates"], 1)
        self.assertEqual(
            result["known_nic_noise_modifies"],
            ["/providers/Microsoft.Network/networkInterfaces/nic-vpn01-mst-dev"],
        )
        self.assertFalse(result["deployment_authorized"])

    def test_pretty_what_if_parser_rejects_backend_nic_extra_delta(self):
        payload = self.classifier.parse_pretty_what_if(
            """  ~ Microsoft.Network/networkInterfaces/nic-vpn01-mst-dev [2024-05-01]
    - kind: "Regular"
    - properties.allowPort25Out: false
    - properties.auxiliaryMode: "None"
    - properties.auxiliarySku: "None"
    - properties.disableTcpStateTracking: false
    ~ properties.enableIPForwarding: false => true
    ~ properties.ipConfigurations: [
      ~ 0:
        - properties.privateIPAddressVersion: "IPv4"
      ]
Resource changes: 1 to modify.
"""
        )
        with self.assertRaises(SystemExit) as context:
            self.classifier.classify(payload)
        self.assertIn("nic-vpn01-mst-dev", str(context.exception))

    def test_pretty_what_if_parser_preserves_modify_blocker(self):
        payload = self.classifier.parse_pretty_what_if(
            """Resource and property changes are indicated with these symbols:
  + Create
  ~ Modify

  + Microsoft.Web/sites/func-demo [2024-04-01]
  ~ Microsoft.Network/networkInterfaces/nic-vpn01-mst-dev [2024-05-01]

Resource changes: 1 to create, 1 to modify.
"""
        )
        with self.assertRaises(SystemExit) as context:
            self.classifier.classify(payload)
        self.assertIn("nic-vpn01-mst-dev", str(context.exception))

    def test_pretty_what_if_parser_fails_on_summary_mismatch(self):
        with self.assertRaises(SystemExit):
            self.classifier.parse_pretty_what_if(
                """  + Microsoft.Web/sites/func-demo [2024-04-01]
Resource changes: 2 to create.
"""
            )


if __name__ == "__main__":
    unittest.main()
