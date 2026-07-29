from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
REQUEST_PATH = (
    ROOT
    / ".project"
    / "observation-requests"
    / "azure-mcp-current-reality-run1.json"
)
HANDOFF_PATH = ROOT / ".project" / "handoffs" / "azure-mcp-current-reality-run1.md"
INDEX_PATH = ROOT / ".project" / "state-index.json"
SCRIPT_PATH = ROOT / "scripts" / "azure_mcp_current_reality_run1.sh"
CLI_PATH = ROOT / "azure_mcp_reality" / "cli.py"
SERVER_PATH = ROOT / "azure_mcp_reality" / "server.py"
COMPAT_PATH = ROOT / "azure_mcp_reality" / "azure_cli_compat.py"

REQUEST_POINTER = ".project/observation-requests/azure-mcp-current-reality-run1.json"
UUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


class AzureMcpCurrentRealityRun1AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        cls.script = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.handoff = HANDOFF_PATH.read_text(encoding="utf-8")
        cls.cli = CLI_PATH.read_text(encoding="utf-8")
        cls.server = SERVER_PATH.read_text(encoding="utf-8")
        cls.compat = COMPAT_PATH.read_text(encoding="utf-8")

    def test_request_is_one_attempt_and_not_executed(self) -> None:
        self.assertEqual(
            self.request["schema_version"],
            "project.azure-mcp-current-reality-authorization.v1",
        )
        self.assertEqual(self.request["attempt_id"], "azure-mcp-current-reality-run1")
        self.assertTrue(self.request["active"])
        self.assertEqual(self.request["authorized_operation"]["attempt_limit"], 1)
        self.assertFalse(
            self.request["authorized_operation"]["automatic_retry_authorized"]
        )
        self.assertFalse(
            self.request["authorized_operation"]["manual_rerun_authorized"]
        )
        self.assertIsNone(
            self.request["repository_boundary"]["exact_execution_commit"]
        )

    def test_scope_is_exact_and_raw_identity_is_not_persisted(self) -> None:
        scope = self.request["scope"]
        self.assertEqual(scope["subscription_name"], "Azure for Students")
        self.assertEqual(scope["resource_group"], "rg-ai-msp-dev-eastus")
        self.assertEqual(scope["expected_resource_group_location"], "eastus")
        self.assertFalse(scope["raw_subscription_id_persisted"])
        self.assertFalse(scope["raw_tenant_id_persisted"])
        self.assertFalse(scope["cross_subscription_discovery_allowed"])
        self.assertFalse(scope["default_subscription_inference_allowed"])
        self.assertFalse(scope["model_supplied_scope_allowed"])
        self.assertIsNone(UUID_PATTERN.search(json.dumps(self.request)))
        self.assertIsNone(UUID_PATTERN.search(self.handoff))

    def test_state_index_selects_active_authorization_without_claiming_execution(self) -> None:
        self.assertEqual(
            self.index["active_azure_mcp_current_reality_authorization"],
            REQUEST_POINTER,
        )
        self.assertEqual(
            self.index["latest_azure_mcp_current_reality_authorization"],
            REQUEST_POINTER,
        )
        self.assertFalse(
            self.index["azure_mcp_current_reality_local_execution_observed"]
        )
        self.assertFalse(
            self.index["azure_mcp_current_reality_remote_endpoint_deployed"]
        )
        self.assertFalse(self.index["azure_ai_mcp_connected"])
        self.assertIn(
            "authorization_recorded != observation_executed",
            self.index["claim_boundaries"],
        )

    def test_wrapper_uses_exact_confirmation_and_consumes_before_resource_query(self) -> None:
        self.assertIn(
            "OBSERVE-AZURE-MCP-RUN1:${EXPECTED_SUBSCRIPTION_NAME}:${EXPECTED_RESOURCE_GROUP}:${AZURE_MCP_RUN1_REVIEWED_COMMIT}",
            self.script,
        )
        self.assertIn("git rev-parse HEAD", self.script)
        self.assertIn("az account set --subscription", self.script)
        self.assertIn("az account show --output json --only-show-errors", self.script)
        self.assertNotIn("az account show --subscription", self.script)
        self.assertIn(".azure-mcp-current-reality-run1.consumed", self.script)
        marker = self.script.index("set -o noclobber")
        tool_call = self.script.index("-m azure_mcp_reality.cli")
        self.assertLess(marker, tool_call)
        self.assertIn("failure after that point consumes", self.handoff)

    def test_cli_and_server_use_the_compatibility_runner(self) -> None:
        self.assertIn("active_subscription_runner", self.cli)
        self.assertIn("runner=active_subscription_runner", self.cli)
        self.assertIn("active_subscription_runner", self.server)
        self.assertIn("runner=active_subscription_runner", self.server)
        self.assertIn(
            '("az", "account", "show", "--subscription")',
            self.compat,
        )
        self.assertIn(
            'command = (\n                "az",\n                "account",\n                "show",',
            self.compat,
        )

    def test_cloud_and_model_mutations_remain_denied(self) -> None:
        authority = self.request["authority"]
        self.assertTrue(authority["one_local_cloud_shell_observation_authorized"])
        self.assertTrue(
            authority["azure_authentication_and_bounded_read_queries_authorized"]
        )
        for key in (
            "azure_mutation_authorized",
            "rbac_mutation_authorized",
            "remote_mcp_deployment_authorized",
            "azure_openai_model_call_authorized",
            "workflow_dispatch_or_rerun_authorized",
            "cleanup_authorized",
        ):
            self.assertFalse(authority[key], key)

        for forbidden in (
            "az group create",
            "az group delete",
            "az deployment group create",
            "az role assignment create",
            "az role assignment delete",
            "az provider register",
            "az cognitiveservices account keys",
            "az containerapp create",
            "az containerapp update",
            "az containerapp delete",
            "azd up",
        ):
            self.assertNotIn(forbidden, self.script)


if __name__ == "__main__":
    unittest.main()
