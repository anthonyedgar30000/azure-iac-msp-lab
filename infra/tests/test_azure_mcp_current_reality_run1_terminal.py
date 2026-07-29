from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
RECEIPT_PATH = ROOT / ".project/evidence/azure-mcp-current-reality-run1.json"
MANIFEST_PATH = ROOT / ".project/evidence/azure-mcp-current-reality-run1.sha256"
RECONCILIATION_PATH = (
    ROOT
    / ".project/reconciliations/azure-mcp-current-reality-run1-terminal-20260729.json"
)
REQUEST_PATH = (
    ROOT / ".project/observation-requests/azure-mcp-current-reality-run1.json"
)
INDEX_PATH = ROOT / ".project/state-index.json"
HANDOFF_PATH = (
    ROOT / ".project/handoffs/azure-mcp-current-reality-run1-terminal.md"
)

TERMINAL_POINTER = (
    ".project/reconciliations/azure-mcp-current-reality-run1-terminal-20260729.json"
)
RECEIPT_POINTER = ".project/evidence/azure-mcp-current-reality-run1.json"
MANIFEST_POINTER = ".project/evidence/azure-mcp-current-reality-run1.sha256"
EXPECTED_FILE_SHA256 = "2fd80540672dd26b11ee0b1c243cfb85defc0e031f8bd5cdc3d9d8d6813d9686"
EXPECTED_RAW_DIGEST = "sha256:6243ab0f718ad3c0981adf319c1434507eea1be0f9dbc14e4256758c30f0f33c"
EXPECTED_TOOL_DIGEST = "sha256:4f2dc29e7f88fb2f8c3f82ed217608bee83bd28f56ceb878b6c43cbdef2dee82"
EXECUTION_COMMIT = "0e46a99b795558b42f8e88cf7703cb95e87f3eb1"


class AzureMcpCurrentRealityRun1TerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt_bytes = RECEIPT_PATH.read_bytes()
        cls.receipt = json.loads(cls.receipt_bytes.decode("utf-8"))
        cls.manifest = MANIFEST_PATH.read_text(encoding="utf-8").strip()
        cls.reconciliation = json.loads(RECONCILIATION_PATH.read_text(encoding="utf-8"))
        cls.request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF_PATH.read_text(encoding="utf-8")

    def test_uploaded_receipt_matches_manifest_exactly(self) -> None:
        actual = hashlib.sha256(self.receipt_bytes).hexdigest()
        declared = self.manifest.split()[0]
        self.assertEqual(actual, EXPECTED_FILE_SHA256)
        self.assertEqual(declared, EXPECTED_FILE_SHA256)
        self.assertEqual(
            self.reconciliation["evidence"]["uploaded_receipt_sha256"],
            EXPECTED_FILE_SHA256,
        )
        self.assertTrue(
            self.reconciliation["evidence"]["receipt_and_manifest_match"]
        )

    def test_receipt_is_bounded_read_only_and_exact_commit(self) -> None:
        self.assertEqual(
            self.receipt["schema_version"],
            "azure-mcp-reality.observation.v1",
        )
        self.assertEqual(self.receipt["observation_status"], "observed")
        self.assertEqual(self.receipt["repository"]["head"], EXECUTION_COMMIT)
        self.assertTrue(self.receipt["repository"]["working_tree_clean"])
        self.assertEqual(self.receipt["repository"]["modified_path_count"], 0)
        self.assertFalse(self.receipt["mutations_performed"])
        self.assertFalse(self.receipt["secrets_returned"])
        self.assertEqual(self.receipt["raw_evidence_digest"], EXPECTED_RAW_DIGEST)
        self.assertEqual(self.receipt["tool_inventory_digest"], EXPECTED_TOOL_DIGEST)
        self.assertEqual(self.receipt["tool_name"], "get_current_reality")
        self.assertEqual(self.receipt["caller_identity_mode"], "existing_azure_cli_session")

    def test_observed_scope_and_resource_inventory_are_exact(self) -> None:
        scope = self.receipt["scope"]
        self.assertEqual(scope["subscription_name"], "Azure for Students")
        self.assertEqual(scope["subscription_state"], "Enabled")
        self.assertEqual(scope["resource_group"], "rg-ai-msp-dev-eastus")
        self.assertFalse(scope["cross_subscription_discovery_allowed"])
        self.assertFalse(scope["default_subscription_inference_allowed"])

        azure = self.receipt["azure"]
        self.assertEqual(azure["resource_count"], 1)
        group = azure["resource_group"]
        self.assertEqual(group["name"], "rg-ai-msp-dev-eastus")
        self.assertEqual(group["location"], "eastus")
        self.assertEqual(group["provisioning_state"], "Succeeded")

        self.assertEqual(len(azure["resources"]), 1)
        resource = azure["resources"][0]
        self.assertEqual(resource["name"], "oai-msp-anthony-dev-eastus")
        self.assertEqual(resource["type"], "Microsoft.CognitiveServices/accounts")
        self.assertEqual(resource["kind"], "OpenAI")
        self.assertEqual(resource["sku_name"], "S0")
        self.assertEqual(resource["location"], "eastus")

        self.assertEqual(
            azure["cognitive_services_accounts"],
            [
                {
                    "account_name": "oai-msp-anthony-dev-eastus",
                    "deployments": [],
                }
            ],
        )

    def test_receipt_contains_no_raw_subscription_or_tenant_uuid(self) -> None:
        text = self.receipt_bytes.decode("utf-8")
        self.assertNotRegex(
            text,
            r"/subscriptions/[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}/",
        )
        self.assertNotIn('"subscription_id"', text.lower())
        self.assertNotIn('"tenant_id"', text.lower())
        self.assertIn("/subscriptions/<subscription>/", text)

    def test_reconciliation_preserves_runtime_identity_uncertainty(self) -> None:
        comparison = self.reconciliation["repository_to_Azure_reconciliation"]
        self.assertEqual(
            comparison["run6_target_deployment"]["classification"],
            "not_present_in_observed_account",
        )
        self.assertEqual(
            comparison["verified_gpt5_runtime"]["classification"],
            "operational_but_ARM_scope_unreconciled",
        )
        self.assertEqual(
            comparison["Azure_AI_MCP_connection"]["classification"],
            "not_established",
        )
        self.assertIn(
            "empty_deployment_inventory_in_observed_account != verified_runtime_absent_globally",
            self.reconciliation["canonical_distinctions"],
        )
        self.assertIn(
            "Do not collapse the successful `gpt-5-mini` runtime",
            self.handoff,
        )

    def test_wrapper_failure_is_terminal_epilogue_not_observation_failure(self) -> None:
        incident = self.reconciliation["wrapper_incident"]
        self.assertEqual(
            incident["stage"],
            "post_observation_epilogue_before_manifest_and_summary",
        )
        self.assertTrue(incident["receipt_write_completed_before_error"])
        self.assertFalse(incident["receipt_validation_inside_wrapper_completed"])
        self.assertFalse(incident["manifest_inside_wrapper_completed"])
        self.assertTrue(incident["manual_manifest_created_from_existing_receipt"])
        self.assertFalse(incident["observation_invalidated"])
        self.assertTrue(incident["authorization_consumed"])
        self.assertFalse(incident["rerun_allowed"])

    def test_state_index_selects_terminal_evidence_and_no_authority(self) -> None:
        self.assertEqual(
            self.index["latest_azure_mcp_current_reality_reconciliation"],
            TERMINAL_POINTER,
        )
        self.assertEqual(
            self.index["latest_azure_mcp_current_reality_receipt"],
            RECEIPT_POINTER,
        )
        self.assertEqual(
            self.index["latest_azure_mcp_current_reality_manifest"],
            MANIFEST_POINTER,
        )
        self.assertIsNone(
            self.index["active_azure_mcp_current_reality_authorization"]
        )
        self.assertTrue(
            self.index["azure_mcp_current_reality_local_execution_observed"]
        )
        self.assertTrue(
            self.index["azure_mcp_current_reality_receipt_validated"]
        )
        self.assertFalse(
            self.index["azure_mcp_current_reality_run1_rerun_authorized"]
        )
        self.assertFalse(self.index["azure_ai_verified_runtime_ARM_scope_reconciled"])
        self.assertFalse(self.index["azure_ai_mcp_connected"])

    def test_authorization_is_consumed_and_cannot_be_replayed(self) -> None:
        self.assertFalse(self.request["active"])
        self.assertEqual(self.request["authorized_operation"]["attempts_consumed"], 1)
        self.assertFalse(
            self.request["authorized_operation"]["manual_rerun_authorized"]
        )
        self.assertFalse(self.request["terminal_outcome"]["rerun_authorized"])
        self.assertFalse(
            self.request["authority"]["azure_authentication_and_bounded_read_queries_authorized"]
        )
        self.assertFalse(self.request["authority"]["azure_mutation_authorized"])


if __name__ == "__main__":
    unittest.main()
