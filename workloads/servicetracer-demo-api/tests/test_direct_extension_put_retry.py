from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKLOAD = ROOT / "workloads" / "servicetracer-demo-api"
BUILDER = WORKLOAD / "scripts" / "build_vm_extension_payload.py"
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "servicetracer-demo-api-timeout-fix-direct-extension-put.yml"
)
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "servicetracer-demo-api-pr104-deployment-wrapper-failure-20260725.json"
)
FUTURE_MARKER = (
    ROOT
    / ".project"
    / "authorizations"
    / "servicetracer-demo-api-timeout-fix-direct-put-retry-20260725.json"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("extension_payload", BUILDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectExtensionPutRetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()

    def test_payload_targets_only_custom_script_extension_contract(self):
        payload = self.builder.build_payload(
            location="westus2",
            installer_uri="https://raw.example/install.sh",
            source_repository="https://github.com/example/repo.git",
            source_ref="a" * 40,
            public_fqdn="example.westus2.cloudapp.azure.com",
            backend_transaction_url="https://backend.example/transaction",
            allowed_origin="https://example.github.io",
            force_update_tag="retry-123",
        )
        self.assertEqual(payload["location"], "westus2")
        properties = payload["properties"]
        self.assertEqual(properties["publisher"], "Microsoft.Azure.Extensions")
        self.assertEqual(properties["type"], "CustomScript")
        self.assertEqual(properties["typeHandlerVersion"], "2.1")
        self.assertEqual(properties["forceUpdateTag"], "retry-123")
        protected = properties["protectedSettings"]
        self.assertEqual(protected["fileUris"], ["https://raw.example/install.sh"])
        self.assertIn("install.sh", protected["commandToExecute"])
        self.assertIn("a" * 40, protected["commandToExecute"])

    def test_builder_rejects_mutable_source_ref(self):
        with self.assertRaises(ValueError):
            self.builder.build_payload(
                location="westus2",
                installer_uri="https://raw.example/install.sh",
                source_repository="https://github.com/example/repo.git",
                source_ref="main",
                public_fqdn="example.westus2.cloudapp.azure.com",
                backend_transaction_url="https://backend.example/transaction",
                allowed_origin="https://example.github.io",
                force_update_tag="retry-123",
            )

    def test_cli_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "payload.json"
            subprocess.run(
                [
                    "python",
                    str(BUILDER),
                    "--location",
                    "westus2",
                    "--installer-uri",
                    "https://raw.example/install.sh",
                    "--source-repository",
                    "https://github.com/example/repo.git",
                    "--source-ref",
                    "b" * 40,
                    "--public-fqdn",
                    "example.westus2.cloudapp.azure.com",
                    "--backend-transaction-url",
                    "https://backend.example/transaction",
                    "--allowed-origin",
                    "https://example.github.io",
                    "--force-update-tag",
                    "retry-456",
                    "--output",
                    str(output),
                ],
                check=True,
            )
            parsed = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(parsed["properties"]["forceUpdateTag"], "retry-456")

    def test_workflow_preserves_what_if_but_avoids_deployment_wrapper(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("az deployment group validate", source)
        self.assertIn("az deployment group what-if", source)
        self.assertIn("assert_extension_update_what_if.py", source)
        self.assertIn("az rest --method put", source)
        self.assertIn("Microsoft.Compute/virtualMachines", source)
        self.assertIn("extensions/${EXTENSION_NAME}", source)
        self.assertNotIn("az deployment group create", source)
        self.assertNotIn("Microsoft.Resources/deployments/write", source)
        self.assertNotIn("az role assignment create", source)
        self.assertNotIn("/api/demo/run", source)
        self.assertNotIn("az group delete", source)
        self.assertNotIn("az resource delete", source)
        self.assertNotIn("az vm restart", source)

    def test_workflow_marker_is_absent_or_exactly_bounded(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            ".project/authorizations/servicetracer-demo-api-timeout-fix-direct-put-retry-20260725.json",
            source,
        )
        if not FUTURE_MARKER.exists():
            self.assertFalse(FUTURE_MARKER.exists())
            return

        marker = json.loads(FUTURE_MARKER.read_text(encoding="utf-8"))
        self.assertEqual(
            marker["schema_version"],
            "project.azure-deployment-authorization-direct-extension-put.v1",
        )
        self.assertTrue(marker["authorized"])
        self.assertEqual(
            marker["source_binding"]["branch"],
            "fix/pr104-direct-extension-put-remediation",
        )
        self.assertEqual(marker["prior_attempt"]["workflow_run_id"], 30178082566)
        self.assertTrue(marker["prior_attempt"]["authorization_consumed"])
        self.assertFalse(marker["prior_attempt"]["extension_mutation_performed"])
        self.assertTrue(marker["scope"]["only_existing_extension_update"])
        self.assertEqual(marker["scope"]["resource_group"], "rg-st-demo-api-dev-westus2")
        self.assertEqual(marker["scope"]["vm"], "vm-st-demo-api-mst-dev")
        self.assertEqual(marker["scope"]["extension"], "servicetracer-demo-api")
        self.assertEqual(marker["method"]["forward"], "direct_extension_resource_put")
        self.assertEqual(marker["method"]["rollback"], "direct_extension_resource_put")
        authority = marker["authority"]
        self.assertTrue(authority["deployment"])
        self.assertTrue(authority["rollback_on_failed_verification"])
        self.assertFalse(authority["transaction_replay"])
        self.assertFalse(authority["pull_request_merge"])
        self.assertFalse(authority["rbac_mutation"])
        self.assertFalse(authority["network_mutation"])
        self.assertFalse(authority["cleanup"])

    def test_pr104_failure_is_recorded_without_false_runtime_claim(self):
        record = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        self.assertEqual(record["protected_run"]["run_id"], 30178082566)
        self.assertEqual(record["protected_run"]["conclusion"], "failure")
        self.assertTrue(record["preflight"]["arm_validation_succeeded"])
        self.assertTrue(record["preflight"]["extension_only_what_if_accepted"])
        self.assertFalse(record["result"]["extension_mutation_performed"])
        self.assertEqual(
            record["result"]["corrected_runtime_status"], "not_deployed"
        )
        self.assertEqual(record["result"]["post_attempt_health"], "not_observed")
        self.assertEqual(record["authorization"]["status"], "consumed_terminal_failure")
        self.assertFalse(record["authority"]["deployment_retry"])

    def test_python_compiles(self):
        subprocess.run(["python", "-m", "py_compile", str(BUILDER)], check=True)


if __name__ == "__main__":
    unittest.main()
