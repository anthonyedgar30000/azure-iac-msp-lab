from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-go-live-run8.yml"
STATIC_WORKFLOW = ROOT / ".github/workflows/azure-ai-plan.yml"
RUN7_EXECUTOR = ROOT / "scripts/azure_ai_go_live_run7.sh"
RUN8_EXECUTOR = ROOT / "scripts/azure_ai_go_live_run8.sh"
REQUEST = ROOT / ".project/deployment-requests/azure-ai-go-live-run8.json"
CONTRACT = ROOT / ".project/contracts/azure-ai-existing-role-activation-v1.json"
HANDOFF = ROOT / ".project/handoffs/azure-ai-go-live-run8.md"
TEMPLATE = ROOT / "infra/azure-ai-existing-account-model-only.bicep"
RUN7_TERMINAL = ROOT / ".project/reconciliations/azure-ai-go-live-run7-terminal-20260730.json"
SELECTOR = ROOT / ".project/CURRENT.json"

EXPECTED_RUN7_BLOB = "21261d6e563fc3a55eae8cb1dd9306e69cacae5a"


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def derive_run8(run7: str) -> tuple[str, int]:
    text = run7.replace("azure-ai-go-live-run7", "azure-ai-go-live-run8")
    text = text.replace("run7", "run8")
    text = text.replace("RUN 7", "RUN 8")
    text = text.replace("Run 7", "Run 8")
    text = text.replace("run 7", "run 8")
    text = text.replace(
        "Proceed with Azure AI run 8 using the existing account and existing account-scoped inference role.",
        "Fix and proceed",
    )
    pattern = re.compile(
        r'(?m)(^\s+--scope "\$account_id" \\\n)\s+--all \\\n'
    )
    return pattern.subn(r"\1", text)


class AzureAiGoLiveRun8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.static_workflow = STATIC_WORKFLOW.read_text(encoding="utf-8")
        cls.run7_bytes = RUN7_EXECUTOR.read_bytes()
        cls.run7 = cls.run7_bytes.decode("utf-8")
        cls.wrapper = RUN8_EXECUTOR.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.template = TEMPLATE.read_text(encoding="utf-8")
        cls.run7_terminal = json.loads(RUN7_TERMINAL.read_text(encoding="utf-8"))
        cls.selector = json.loads(SELECTOR.read_text(encoding="utf-8"))
        cls.derived, cls.repair_count = derive_run8(cls.run7)

    def test_request_is_fresh_single_attempt_authority(self) -> None:
        self.assertEqual(self.request["attempt_id"], "azure-ai-go-live-run8")
        self.assertEqual(self.request["status"], "active_one_attempt")
        self.assertTrue(self.request["active"])
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 0)
        self.assertEqual(self.request["source_instruction"], "Fix and proceed")
        self.assertIn("exactly one new bounded", self.request["normalized_intent"])
        self.assertEqual(self.request["predecessor"]["attempt_id"], "azure-ai-go-live-run7")
        self.assertFalse(self.request["predecessor"]["azure_mutations_performed"])

    def test_run7_is_consumed_and_not_reactivated(self) -> None:
        self.assertEqual(self.run7_terminal["status"], "consumed_terminal_failure")
        self.assertTrue(self.run7_terminal["authorization"]["consumed"])
        self.assertFalse(self.run7_terminal["authorization"]["manual_rerun_authorized"])
        self.assertFalse(self.run7_terminal["terminal_result"]["azure_mutations_performed"])
        self.assertIn("does not reactivate or rerun consumed run 7", self.handoff)

    def test_historical_executor_is_pinned_and_unchanged(self) -> None:
        self.assertEqual(git_blob_sha(self.run7_bytes), EXPECTED_RUN7_BLOB)
        self.assertIn(f'EXPECTED_SOURCE_BLOB="{EXPECTED_RUN7_BLOB}"', self.wrapper)
        self.assertIn('git hash-object "$SOURCE_EXECUTOR"', self.wrapper)
        self.assertIn("historical run-7 executor blob changed", self.wrapper)

    def test_exact_cli_repair_is_applied(self) -> None:
        self.assertEqual(self.repair_count, 3)
        self.assertIsNone(
            re.search(r'--scope "\$account_id" \\\n\s+--all', self.derived)
        )
        self.assertIn('--assignee "$AZURE_CLIENT_ID" --all', self.derived)
        self.assertIn("expected exactly 3 scoped --all repairs", self.wrapper)
        self.assertIn("invalid scoped --all combination remains", self.wrapper)

    def test_derived_executor_is_bound_to_run8(self) -> None:
        self.assertIn('ATTEMPT_ID="azure-ai-go-live-run8"', self.derived)
        self.assertIn(
            'REQUEST_FILE=".project/deployment-requests/azure-ai-go-live-run8.json"',
            self.derived,
        )
        self.assertIn('--arg instruction "Fix and proceed"', self.derived)
        self.assertIn("Reply with exactly: AZURE AI RUN 8 LIVE", self.derived)
        self.assertNotIn("azure-ai-go-live-run7", self.derived)
        self.assertEqual(self.derived.count("az deployment group create"), 1)
        self.assertEqual(self.derived.count("az resource update"), 1)
        self.assertEqual(self.derived.count("curl --silent --show-error"), 1)
        self.assertNotIn("az role assignment create", self.derived)

    def test_workflow_is_single_merge_trigger(self) -> None:
        self.assertIn("name: Azure AI go live run 8", self.workflow)
        self.assertIn("branches:\n      - main", self.workflow)
        self.assertIn("'.github/workflows/azure-ai-go-live-run8.yml'", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn("bash scripts/azure_ai_go_live_run8.sh", self.workflow)
        self.assertIn("if: always()", self.workflow)

    def test_template_cannot_create_account_group_or_role(self) -> None:
        self.assertIn("targetScope = 'resourceGroup'", self.template)
        self.assertIn("Microsoft.CognitiveServices/accounts@2024-10-01' existing", self.template)
        self.assertIn("Microsoft.CognitiveServices/accounts/deployments@2024-10-01", self.template)
        self.assertNotIn("Microsoft.Resources/resourceGroups", self.template)
        self.assertNotIn("Microsoft.Authorization/roleAssignments", self.template)
        architecture = self.contract["architecture"]
        self.assertFalse(architecture["resource_group_creation_available"])
        self.assertFalse(architecture["account_creation_available"])
        self.assertFalse(architecture["role_assignment_creation_available"])

    def test_security_cost_and_failure_boundaries(self) -> None:
        authority = self.request["authority"]
        self.assertTrue(authority["one_model_deployment_authorized"])
        self.assertTrue(authority["one_account_hardening_update_authorized"])
        self.assertTrue(authority["one_model_request_authorized"])
        self.assertFalse(authority["role_assignment_creation_authorized"])
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["manual_rerun_authorized"])
        self.assertFalse(self.request["security"]["api_keys_permitted"])
        self.assertEqual(self.request["cost_and_quota"]["deployment_capacity"], 1)
        self.assertEqual(self.request["cost_and_quota"]["model_request_count"], 1)
        self.assertIn("GitHub Re-run is unauthorized", self.request["failure_behavior"]["retry"])

    def test_selector_and_static_validation_cover_run8(self) -> None:
        self.assertEqual(
            self.selector["active_azure_ai_activation_authorization"],
            ".project/deployment-requests/azure-ai-go-live-run8.json",
        )
        self.assertEqual(
            self.selector["latest_azure_ai_terminal_reconciliation"],
            ".project/reconciliations/azure-ai-go-live-run7-terminal-20260730.json",
        )
        self.assertIn("infra.tests.test_azure_ai_go_live_run8", self.static_workflow)
        self.assertIn("bash -n scripts/azure_ai_go_live_run8.sh", self.static_workflow)
        self.assertIn("id-token: none", self.static_workflow)


if __name__ == "__main__":
    unittest.main()
