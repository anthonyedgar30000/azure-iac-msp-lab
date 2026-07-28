from __future__ import annotations

import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "azure-mcp-read-only-preflight.yml"
SCRIPT_PATH = ROOT / "scripts" / "azure_mcp_cloud_shell_preflight.sh"
CONTRACT_PATH = ROOT / ".project" / "contracts" / "azure-mcp-read-only-preflight-workflow-v1.json"


class AzureMcpReadOnlyPreflightWorkflowTests(unittest.TestCase):
    def test_contract_remains_implementation_only_and_fail_closed(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema_version"], "project.azure-mcp-read-only-preflight-workflow.v1")
        self.assertEqual(contract["status"], "implementation_candidate_not_executed")
        self.assertTrue(contract["repository_implementation_authorized"])
        self.assertFalse(contract["workflow_dispatch_authorized"])
        self.assertFalse(contract["azure_authentication_performed"])
        self.assertFalse(contract["azure_mutation_authorized"])
        self.assertFalse(contract["azure_deployment_authorized"])
        self.assertFalse(contract["openai_api_execution_authorized"])

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
        self.assertNotRegex(workflow, r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

    def test_preflight_is_noninteractive_and_contains_no_mutation_entry_point(self) -> None:
        script = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("AZD_NON_INTERACTIVE=true", script)
        self.assertIn("AZD_SKIP_FIRST_RUN=true", script)
        self.assertIn("--no-prompt", script)
        for command in ("az account show", "az provider show", "az group show", "az resource list", "azd init"):
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
