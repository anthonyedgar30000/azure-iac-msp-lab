from __future__ import annotations

import json
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / ".project/state-index.json"
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-mcp-read-only-preflight-run1-terminal-20260729.json"
)
HANDOFF = ROOT / ".project/handoffs/post-pr191-mcp-preflight-run1-current-state.md"
CONTRACT = (
    ROOT
    / ".project"
    / "contracts"
    / "azure-mcp-read-only-preflight-workflow-v2.json"
)
SCRIPT = ROOT / "scripts/azure_mcp_cloud_shell_preflight.sh"

MAIN = "bdb337cf5ef10a643933d19c778d765e9f0d330d"
PR191_SOURCE = "e70992960fa15a82a4e131b6e0fb527f5478b8f4"
REVIEWED_COMMIT = "bae07d24c59f7bc02001a168c7c6aac188ff2747"
RECONCILIATION_PATH = (
    ".project/reconciliations/azure-mcp-read-only-preflight-run1-terminal-20260729.json"
)
CURRENT_TOOL_RECONCILIATION_PATH = (
    ".project/reconciliations/azure-mcp-current-reality-tool-20260729.json"
)
CURRENT_TOOL_HANDOFF_PATH = ".project/handoffs/azure-mcp-current-reality-tool.md"
CONTRACT_PATH = ".project/contracts/azure-mcp-read-only-preflight-workflow-v2.json"
DEPLOYMENT_TERMINAL_PATH = (
    ".project/reconciliations/correlation-identity-run1-terminal-20260727.json"
)
REPOSITORY_WATERMARK_PATH = (
    ".project/reconciliations/post-pr185-repository-watermark-20260728.json"
)
AUTHORIZATION_CONTROL_PATH = (
    ".project/reconciliations/post-pr187-authorization-control-reconciliation-20260728.json"
)


class AzureMcpPreflightRun1TerminalReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.script = SCRIPT.read_text(encoding="utf-8")

    def test_state_index_preserves_run1_as_consumed_preflight_history(self) -> None:
        self.assertEqual(
            self.index["latest_repository_and_mcp_reconciliation"],
            CURRENT_TOOL_RECONCILIATION_PATH,
        )
        self.assertEqual(
            self.index["latest_azure_mcp_tool_reconciliation"],
            CURRENT_TOOL_RECONCILIATION_PATH,
        )
        self.assertEqual(
            self.index["latest_azure_mcp_preflight_reconciliation"],
            RECONCILIATION_PATH,
        )
        self.assertEqual(
            self.index["latest_repository_handoff"],
            CURRENT_TOOL_HANDOFF_PATH,
        )
        self.assertEqual(self.index["azure_mcp_preflight_contract"], CONTRACT_PATH)
        self.assertIsNone(self.index["active_azure_mcp_preflight_authorization"])
        self.assertEqual(
            self.index["latest_consumed_azure_mcp_preflight_authorization"],
            RECONCILIATION_PATH,
        )

        self.assertEqual(
            self.index["latest_terminal_reconciliation"],
            DEPLOYMENT_TERMINAL_PATH,
        )
        self.assertEqual(
            self.index["latest_authorization_resolution"],
            DEPLOYMENT_TERMINAL_PATH,
        )
        self.assertEqual(
            self.index["latest_repository_reconciliation"],
            REPOSITORY_WATERMARK_PATH,
        )
        self.assertEqual(
            self.index["latest_repository_watermark_reconciliation"],
            REPOSITORY_WATERMARK_PATH,
        )
        self.assertEqual(
            self.index["latest_lifecycle_reconciliation"],
            AUTHORIZATION_CONTROL_PATH,
        )
        self.assertEqual(
            self.index["latest_authorization_control_reconciliation"],
            AUTHORIZATION_CONTROL_PATH,
        )

    def test_repository_watermark_advances_through_pr191(self) -> None:
        github = self.reconciliation["github_state"]
        self.assertEqual(github["observed_main"], MAIN)
        self.assertEqual(github["latest_merged_pull_request"], 191)
        self.assertEqual(github["latest_merged_source_head"], PR191_SOURCE)
        self.assertEqual(github["pull_request_191_exact_head_ci_run"], 30410555271)
        self.assertEqual(github["pull_request_191_exact_head_ci_conclusion"], "success")
        self.assertEqual(github["open_pull_requests_observed_before_repair_branch"], [])
        self.assertEqual(github["repair_branch_base"], MAIN)

    def test_run1_is_consumed_terminal_and_non_retriable(self) -> None:
        run = self.reconciliation["workflow_run"]
        authority = self.reconciliation["authorization"]
        failure = self.reconciliation["failure"]

        self.assertEqual(run["run_id"], 30415111776)
        self.assertEqual(run["job_id"], 90459816380)
        self.assertEqual(run["checked_out_reviewed_commit"], REVIEWED_COMMIT)
        self.assertEqual(run["Azure_OIDC_login"], "success")
        self.assertEqual(run["read_only_preflight_step"], "failure")
        self.assertTrue(authority["consumed"])
        self.assertFalse(authority["renewed"])
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertEqual(failure["exit_code"], 2)
        self.assertEqual(failure["Azure_CLI_version"], "2.88.0")
        self.assertFalse(failure["Azure_API_resource_observation_completed"])
        self.assertFalse(failure["template_downloaded"])

    def test_protected_artifact_records_only_the_early_boundary(self) -> None:
        artifact = self.reconciliation["protected_artifact"]
        self.assertEqual(artifact["artifact_id"], 8709858548)
        self.assertEqual(
            artifact["digest"],
            "sha256:7b931ed0a8e08497457f97528f06a018164b93a9b448ff97f612bd2a3468d7e5",
        )
        self.assertTrue(artifact["files"]["request.json"])
        self.assertTrue(artifact["files"]["azure-cli-version.json"])
        self.assertFalse(artifact["files"]["account-context.json"])
        self.assertFalse(artifact["files"]["provider-states.json"])
        self.assertFalse(artifact["files"]["resource-group-state.json"])
        self.assertFalse(artifact["files"]["template-files.sha256"])
        self.assertFalse(artifact["raw_subscription_or_tenant_identifiers_promoted"])

    def test_repair_uses_verified_active_subscription_without_bad_arguments(self) -> None:
        self.assertIn('readonly SCRIPT_VERSION="1.1.1"', self.script)
        self.assertIn('account_json="$(az account show --output json)"', self.script)
        self.assertIn("az account list-locations", self.script)
        self.assertNotRegex(
            self.script,
            r"az account show(?:[ \t]|\\\n)+--subscription\b",
        )
        self.assertNotRegex(
            self.script,
            r"az account list-locations(?:[ \t]|\\\n)+--subscription\b",
        )
        self.assertIn(
            '[[ "$subscription_id" == "$AZURE_MCP_HOSTING_SUBSCRIPTION_ID" ]]',
            self.script,
        )
        self.assertIn('[[ "$subscription_state" == "Enabled" ]]', self.script)

    def test_manual_validation_is_preserved_without_overclaiming_oidc_success(self) -> None:
        manual = self.reconciliation["operator_provided_cloud_shell_validation"]
        self.assertEqual(manual["subscription_name"], "Azure for Students")
        self.assertEqual(manual["subscription_state"], "Enabled")
        self.assertTrue(manual["active_subscription_ID_match"])
        self.assertEqual(manual["principal_type"], "user")
        self.assertTrue(manual["location_available"])
        self.assertFalse(manual["Azure_resource_mutation_performed"])
        self.assertFalse(manual["equivalent_to_GitHub_Actions_OIDC_identity"])
        self.assertFalse(manual["equivalent_to_completed_preflight"])

    def test_contract_and_current_authority_remain_fail_closed(self) -> None:
        self.assertEqual(
            self.contract["status"],
            "first_dispatch_consumed_terminal_failure_repair_pending",
        )
        self.assertTrue(self.contract["first_dispatch"]["authorization_consumed"])
        self.assertFalse(self.contract["first_dispatch"]["azure_mutations_performed"])
        self.assertFalse(self.contract["first_dispatch"]["deployment_performed"])

        authority = self.reconciliation["current_authority"]
        self.assertTrue(authority["repository_only_repair_authorized"])
        self.assertTrue(authority["ordinary_exact_head_pull_request_CI_authorized"])
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_or_rerun_authorized",
            "Azure_authentication_authorized",
            "Azure_query_authorized",
            "Azure_mutation_authorized",
            "deployment_authorized",
            "OpenAI_API_execution_authorized",
            "rollback_authorized",
            "cleanup_authorized",
            "RBAC_mutation_authorized",
            "repository_ruleset_mutation_authorized",
            "live_authorization_claim_authorized",
        ):
            self.assertFalse(authority[key], key)

        azure = self.reconciliation["preserved_Azure_and_runtime_state"]
        self.assertFalse(azure["fresh_Azure_resource_query_after_failed_run"])
        self.assertFalse(azure["actual_cost_freshly_observed"])
        self.assertFalse(azure["quota_freshly_observed"])
        self.assertEqual(azure["expected_recurring_Azure_cost_delta_CAD"], 0)

    def test_handoff_redacts_raw_subscription_and_tenant_identifiers(self) -> None:
        uuid_pattern = re.compile(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
        )
        self.assertIsNone(uuid_pattern.search(self.handoff))
        self.assertIn("Run 1 must not be rerun under that grant", self.handoff)
        self.assertIn("expected recurring Azure cost delta from this repair: CAD $0", self.handoff)


if __name__ == "__main__":
    unittest.main()
