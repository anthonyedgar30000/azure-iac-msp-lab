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
HANDOFF_PATH = (
    ROOT
    / ".project"
    / "handoffs"
    / "azure-mcp-current-reality-run1-terminal.md"
)
INDEX_PATH = ROOT / ".project" / "state-index.json"
SCRIPT_PATH = ROOT / "scripts" / "azure_mcp_current_reality_run1.sh"
CLI_PATH = ROOT / "azure_mcp_reality" / "cli.py"
SERVER_PATH = ROOT / "azure_mcp_reality" / "server.py"
COMPAT_PATH = ROOT / "azure_mcp_reality" / "azure_cli_compat.py"

REQUEST_POINTER = ".project/observation-requests/azure-mcp-current-reality-run1.json"
TERMINAL_POINTER = (
    ".project/reconciliations/azure-mcp-current-reality-run1-terminal-20260729.json"
)
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

    def test_request_is_consumed_terminal_and_non_retriable(self) -> None:
        self.assertEqual(
            self.request["schema_version"],
            "project.azure-mcp-current-reality-authorization.v1",
        )
        self.assertEqual(self.request["attempt_id"], "azure-mcp-current-reality-run1")
        self.assertEqual(
            self.request["status"],
            "consumed_observation_succeeded_wrapper_epilogue_failed",
        )
        self.assertFalse(self.request["active"])
        self.assertEqual(self.request["authorized_operation"]["attempt_limit"], 1)
        self.assertEqual(self.request["authorized_operation"]["attempts_consumed"], 1)
        self.assertFalse(
            self.request["authorized_operation"]["automatic_retry_authorized"]
        )
        self.assertFalse(
            self.request["authorized_operation"]["manual_rerun_authorized"]
        )
        self.assertEqual(
            self.request["repository_boundary"]["exact_execution_commit"],
            "0e46a99b795558b42f8e88cf7703cb95e87f3eb1",
        )
        self.assertTrue(self.request["terminal_outcome"]["Azure_resource_observation_completed"])
        self.assertFalse(self.request["terminal_outcome"]["wrapper_epilogue_completed"])
        self.assertFalse(self.request["terminal_outcome"]["rerun_authorized"])

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

    def test_state_index_selects_terminal_result_without_active_authority(self) -> None:
        self.assertIsNone(
            self.index["active_azure_mcp_current_reality_authorization"]
        )
        self.assertEqual(
            self.index["latest_azure_mcp_current_reality_authorization"],
            REQUEST_POINTER,
        )
        self.assertEqual(
            self.index["latest_consumed_azure_mcp_current_reality_authorization"],
            TERMINAL_POINTER,
        )
        self.assertEqual(
            self.index["latest_azure_mcp_current_reality_reconciliation"],
            TERMINAL_POINTER,
        )
        self.assertTrue(
            self.index["azure_mcp_current_reality_local_execution_observed"]
        )
        self.assertTrue(
            self.index["azure_mcp_current_reality_receipt_validated"]
        )
        self.assertFalse(
            self.index["azure_mcp_current_reality_run1_wrapper_epilogue_completed"]
        )
        self.assertFalse(
            self.index["azure_mcp_current_reality_run1_rerun_authorized"]
        )
        self.assertFalse(
            self.index["azure_mcp_current_reality_remote_endpoint_deployed"]
        )
        self.assertFalse(self.index["azure_ai_mcp_connected"])
        self.assertIn(
            "authorization_consumed != wrapper_completed",
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
        self.assertIn(
            'CONSUMPTION_MARKER="${HOME}/.${ATTEMPT_ID}.consumed"',
            self.script,
        )
        marker = self.script.index("set -o noclobber")
        tool_call = self.script.index("-m azure_mcp_reality.cli")
        self.assertLess(marker, tool_call)
        self.assertIn("Do not rerun run 1", self.handoff)

    def test_wrapper_validation_names_do_not_collide_with_readonly_variables(self) -> None:
        self.assertIn('readonly RECEIPT_PATH="/tmp/${ATTEMPT_ID}.json"', self.script)
        self.assertIn('RUN1_RECEIPT_PATH="$RECEIPT_PATH"', self.script)
        self.assertIn('os.environ["RUN1_RECEIPT_PATH"]', self.script)
        self.assertNotIn('\nRECEIPT_PATH="$RECEIPT_PATH" \\\n', self.script)
        for name in (
            "RUN1_EXPECTED_COMMIT",
            "RUN1_EXPECTED_SUBSCRIPTION_NAME",
            "RUN1_EXPECTED_RESOURCE_GROUP",
            "RUN1_EXPECTED_LOCATION",
        ):
            self.assertIn(name, self.script)

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
        self.assertFalse(authority["one_local_cloud_shell_observation_authorized"])
        self.assertFalse(
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
