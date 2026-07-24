from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKLOAD = ROOT / "workloads" / "servicetracer-demo-api"
MAIN = WORKLOAD / "infra" / "main.bicep"
MODULE = WORKLOAD / "infra" / "modules" / "workload.bicep"
INSTALLER = WORKLOAD / "scripts" / "install.sh"
CLASSIFIER = WORKLOAD / "scripts" / "assert_what_if.py"
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml"
SERVER = ROOT / "demo_api" / "standalone_server.py"
CI = ROOT / ".github" / "workflows" / "ci.yml"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ServiceTracerDemoApiSubprojectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classifier = load_module(CLASSIFIER, "demo_api_subproject_classifier")

    def test_python_and_shell_compile(self):
        py_compile.compile(str(CLASSIFIER), doraise=True)
        py_compile.compile(str(SERVER), doraise=True)
        subprocess.run(["bash", "-n", str(INSTALLER)], check=True)

    def test_infrastructure_has_independent_lifecycle(self):
        source = MAIN.read_text(encoding="utf-8") + MODULE.read_text(encoding="utf-8")
        self.assertIn("targetScope = 'subscription'", source)
        self.assertIn("rg-st-demo-api-", source)
        self.assertIn("vm-st-demo-api-", source)
        self.assertIn("vnet-st-demo-api-", source)
        self.assertIn("pip-st-demo-api-vm-", source)
        self.assertIn("SystemAssigned", source)
        self.assertIn("Allow-HTTP-From-Internet", source)
        self.assertIn("Allow-HTTPS-From-Internet", source)
        self.assertNotIn("destinationPortRange: '22'", source)
        self.assertNotIn("loadBalancers", source)
        for forbidden in (
            "vm-stcollector-",
            "nsg-operations-",
            "vnet-onprem-sim-",
            "lb-remote-access-",
            "operationsNsgName",
            "collectorVmName",
            "collectorPrivateIpAddress",
        ):
            self.assertNotIn(forbidden, source)

    def test_workflow_binds_to_dispatch_sha_and_is_read_only(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("ref: ${{ github.sha }}", source)
        self.assertIn("refs/heads/main", source)
        self.assertIn('"$(git rev-parse HEAD)" == "$GITHUB_SHA"', source)
        self.assertNotIn("reviewed_commit", source)
        self.assertIn("az deployment sub validate", source)
        self.assertIn("az deployment sub what-if", source)
        self.assertNotIn("az deployment sub create", source)
        self.assertNotIn("az group delete", source)
        self.assertNotIn("az resource delete", source)
        self.assertNotIn("az vm run-command", source)
        self.assertIn("azure_mutations_authorized:false", source)

    def test_installer_uses_shared_application_on_dedicated_host(self):
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("SERVICETRACER_HOSTING_MODEL=dedicated_vm_subproject", source)
        self.assertIn("$SOURCE_ROOT/demo_api/core.py", source)
        self.assertIn("NoNewPrivileges=true", source)
        self.assertIn("ProtectSystem=strict", source)
        self.assertIn("certbot --nginx", source)
        self.assertNotIn("collector-hosted", source)

    def test_server_exposes_configurable_hosting_model(self):
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn('HOSTING_MODEL = os.environ.get("SERVICETRACER_HOSTING_MODEL", "collector_vm_systemd")', source)
        self.assertIn('"hosting_model": HOSTING_MODEL', source)

    @staticmethod
    def _valid_payload():
        target = "rg-st-demo-api-dev-westus2"
        suffix = "mst-dev"
        base = f"/subscriptions/x/resourceGroups/{target}/providers"
        return {
            "status": "Succeeded",
            "error": None,
            "changes": [
                {
                    "changeType": "Create",
                    "resourceId": f"/subscriptions/x/resourceGroups/{target}",
                    "after": {"type": "Microsoft.Resources/resourceGroups"},
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{base}/Microsoft.Network/networkSecurityGroups/nsg-st-demo-api-{suffix}",
                    "after": {"type": "Microsoft.Network/networkSecurityGroups"},
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{base}/Microsoft.Network/virtualNetworks/vnet-st-demo-api-{suffix}",
                    "after": {"type": "Microsoft.Network/virtualNetworks"},
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{base}/Microsoft.Network/publicIPAddresses/pip-st-demo-api-vm-{suffix}",
                    "after": {"type": "Microsoft.Network/publicIPAddresses"},
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{base}/Microsoft.Network/networkInterfaces/nic-st-demo-api-{suffix}",
                    "after": {"type": "Microsoft.Network/networkInterfaces"},
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{base}/Microsoft.Compute/virtualMachines/vm-st-demo-api-{suffix}",
                    "after": {"type": "Microsoft.Compute/virtualMachines"},
                },
                {
                    "changeType": "Create",
                    "resourceId": f"{base}/Microsoft.Compute/virtualMachines/vm-st-demo-api-{suffix}/extensions/servicetracer-demo-api",
                    "after": {"type": "Microsoft.Compute/virtualMachines/extensions"},
                },
            ],
        }

    def _classify(self, payload):
        return self.classifier.classify(
            payload,
            target_resource_group="rg-st-demo-api-dev-westus2",
            dependency_resource_group="rg-servicetracer-dev-westus2",
            suffix="mst-dev",
        )

    def test_classifier_accepts_only_dedicated_creates(self):
        result = self._classify(self._valid_payload())
        self.assertEqual(result["status"], "accepted_independent_workload_create_plan")
        self.assertEqual(len(result["active_changes"]), 7)
        self.assertEqual(result["base_infrastructure_modifications"], [])
        self.assertFalse(result["deployment_authorized"])

    def test_classifier_rejects_dependency_mutation(self):
        payload = self._valid_payload()
        payload["changes"].append(
            {
                "changeType": "Modify",
                "resourceId": "/subscriptions/x/resourceGroups/rg-servicetracer-dev-westus2/providers/Microsoft.Network/loadBalancers/lb-remote-access-mst-dev",
                "after": {"type": "Microsoft.Network/loadBalancers"},
            }
        )
        with self.assertRaises(SystemExit):
            self._classify(payload)

    def test_classifier_rejects_modify_delete_replace_and_scope_escape(self):
        for change_type in ("Modify", "Delete", "Replace"):
            payload = self._valid_payload()
            payload["changes"][3]["changeType"] = change_type
            with self.assertRaises(SystemExit):
                self._classify(payload)

        payload = self._valid_payload()
        payload["changes"].append(
            {
                "changeType": "Create",
                "resourceId": "/subscriptions/x/resourceGroups/other/providers/Microsoft.Storage/storageAccounts/escape",
                "after": {"type": "Microsoft.Storage/storageAccounts"},
            }
        )
        with self.assertRaises(SystemExit):
            self._classify(payload)

    def test_ci_runs_workload_tests_and_builds_workload_bicep(self):
        source = CI.read_text(encoding="utf-8")
        self.assertIn("workloads/servicetracer-demo-api/tests", source)
        self.assertIn("workloads/servicetracer-demo-api/infra/main.bicep", source)


if __name__ == "__main__":
    unittest.main()
