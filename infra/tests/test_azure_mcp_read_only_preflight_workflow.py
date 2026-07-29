from __future__ import annotations

import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "azure-mcp-read-only-preflight.yml"
SCRIPT_PATH = ROOT / "scripts" / "azure_mcp_cloud_shell_preflight.sh"
CONTRACT_PATH = (
    ROOT
    / ".project"
    / "contracts"
    / "azure-mcp-read-only-preflight-workflow-v2.json"
)


class AzureMcpReadOnlyPreflightWorkflowTests(unittest.TestCase):
    def test_contract_records_consumed_terminal_failure_and_fail_closed_repair(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            contract["schema_version"],
            "project.azure-mcp-read-only-preflight-workflow.v2",
        )
        self.assertEqual(
            contract["status"],
            "first_dispatch_consumed_terminal_failure_repair_pending",
        )
        self.assertTrue(contract["current_authority"]["repository_repair_authorized"])
        self.assertFalse(
            contract["current_authority"]["workflow_dispatch_or_rerun_authorized"]
        )
        self.assertTrue(contract["first_dispatch"]["azure_oidc_authentication_succeeded"])
        self.assertTrue(contract["first_dispatch"]["authorization_consumed"])
        self.assertFalse(contract["first_dispatch"]["azure_mutations_performed"])
        self.assertFalse(contract["first_dispatch"]["deployment_performed"])
        self.assertFalse(contract["first_dispatch"]["openai_api_execution_performed"])
        self.assertTrue(contract["failure_and_rollback"]["failed_run_is_terminal"])

    def test_workflow_is_manual_exact_commit_and_oidc_bounded(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("\npush:", workflow)
        self.assertIn("reviewed_commit:", workflow)
        self.assertIn('[[ "$(git rev-parse HEAD)" == "$REVIEWED_COMMIT" ]]', workflow)
        self.assertIn("OBSERVE-AZURE-MCP:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("environment: azure-lab", workflow)
        self.assertIn("uses: azure/login@v2", workflow)
        self.assertIn("uses: Azure/setup-azd@v2", workflow)

    def test_workflow_uses_existing_secret_boundary_without_exposing_values(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        for secret_name in ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID"):
            self.assertIn(f"secrets.{secret_name}", workflow)
        self.assertNotIn("OPENAI_API_KEY", workflow)
        self.assertNotRegex(
            workflow,
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        )

    def test_account_commands_use_verified_active_subscription_context(self) -> None:
        script = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn('readonly SCRIPT_VERSION="1.1.1"', script)
        self.assertIn('account_json="$(az account show --output json)"', script)
        self.assertIn("az account list-locations", script)
        self.assertNotRegex(
            script,
            r"az account show(?:[ \t]|\\\n)+--subscription\b",
        )
        self.assertNotRegex(
            script,
            r"az account list-locations(?:[ \t]|\\\n)+--subscription\b",
        )
        self.assertIn(
            '[[ "$subscription_id" == "$AZURE_MCP_HOSTING_SUBSCRIPTION_ID" ]]',
            script,
        )
        self.assertIn('[[ "$subscription_state" == "Enabled" ]]', script)

    def test_preflight_is_noninteractive_and_contains_no_mutation_entry_point(self) -> None:
        script = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("AZD_NON_INTERACTIVE=true", script)
        self.assertIn("AZD_SKIP_FIRST_RUN=true", script)
        self.assertIn("--no-prompt", script)
        for command in (
            "az account show",
            "az account list-locations",
            "az provider show",
            "az group show",
            "az resource list",
            "azd init",
        ):
            self.assertIn(command, script)
        for pattern in (
            r"^\s*azd\s+(?:up|provision|deploy|down)\b",
            r"^\s*az\s+provider\s+register\b",
            r"^\s*az\s+group\s+(?:create|delete)\b",
            r"^\s*az\s+role\s+assignment\s+(?:create|delete)\b",
            r"^\s*az\s+containerapp\s+(?:create|update|delete)\b",
        ):
            self.assertIsNone(re.search(pattern, script, flags=re.MULTILINE))

    def test_temporary_stderr_is_not_persisted_in_evidence(self) -> None:
        script = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn('rm -f "$provider_stderr"', script)
        self.assertIn('rm -f "$resource_stderr"', script)
        self.assertIn('"$group_stderr"', script)
        self.assertIn("raw_identifiers_persisted:false", script)
        self.assertGreaterEqual(script.count("stderr_persisted:false"), 2)

    def test_template_remains_explicitly_unpinned_and_not_deployable(self) -> None:
        script = SCRIPT_PATH.read_text(encoding="utf-8")
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn('template_reference_kind:"azure_developer_cli_gallery_alias"', script)
        self.assertIn("template_source_pinned:false", script)
        self.assertIn("deployment_authorized:false", script)
        self.assertIn("template_source_pinned:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)

    def test_workflow_uploads_protected_digest_bearing_evidence(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("artifact-manifest.sha256", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("retention-days: 30", workflow)
        self.assertIn("if: always()", workflow)


if __name__ == "__main__":
    unittest.main()
