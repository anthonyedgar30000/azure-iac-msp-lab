from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
RECEIPT_PATH = ROOT / ".project/evidence/azure-mcp-local-client-probe.json"
MANIFEST_PATH = ROOT / ".project/evidence/azure-mcp-local-client-probe.sha256"
CONTRACT_PATH = ROOT / ".project/contracts/azure-mcp-local-client-probe-v1.json"
RECONCILIATION_PATH = (
    ROOT
    / ".project/reconciliations/azure-mcp-local-client-probe-v1-terminal-20260729.json"
)
HANDOFF_PATH = ROOT / ".project/handoffs/azure-mcp-local-client-probe-v1.md"

EXACT_SOURCE = "d2cd7e68a6dd954d5c114b827817a1d866827ca3"
RECEIPT_SHA256 = "1f1cf91c47fdd347f835894b2ac8a7c9fb37552170cddbee7d1805740d54ab81"
INTERNAL_DIGEST = "sha256:70f236ea8d17b96d8586845a96f2cff09e02fc08888c78554c3d41137a07de8f"
PLAN_DIGEST = "sha256:4e9a858383ab78e2fef896421be4c65f122484394667d332bc6c0dea51e3bb71"
UUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AzureMcpLocalClientProbeTerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt_bytes = RECEIPT_PATH.read_bytes()
        cls.receipt = json.loads(cls.receipt_bytes)
        cls.manifest = MANIFEST_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(RECONCILIATION_PATH.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF_PATH.read_text(encoding="utf-8")

    def test_receipt_hash_and_internal_digest_are_valid(self) -> None:
        self.assertEqual(hashlib.sha256(self.receipt_bytes).hexdigest(), RECEIPT_SHA256)
        self.assertTrue(self.manifest.startswith(RECEIPT_SHA256 + "  "))

        without_digest = dict(self.receipt)
        actual_digest = without_digest.pop("receipt_digest")
        expected_digest = "sha256:" + hashlib.sha256(
            _canonical_json(without_digest).encode("utf-8")
        ).hexdigest()
        self.assertEqual(actual_digest, INTERNAL_DIGEST)
        self.assertEqual(expected_digest, INTERNAL_DIGEST)

    def test_receipt_is_bound_to_exact_source_and_local_stdio(self) -> None:
        self.assertEqual(self.receipt["repository"]["head"], EXACT_SOURCE)
        self.assertTrue(self.receipt["repository"]["working_tree_clean"])
        self.assertEqual(self.receipt["transport"]["type"], "stdio_subprocess")
        self.assertFalse(self.receipt["transport"]["network_listener_created"])
        self.assertFalse(self.receipt["transport"]["remote_endpoint_used"])
        self.assertTrue(self.receipt["protocol"]["initialized"])
        self.assertEqual(
            self.receipt["tool_inventory"],
            [
                "get_current_reality",
                "list_lab_profiles",
                "prepare_lab_request",
            ],
        )

    def test_profile_and_prepare_calls_preserve_all_gates(self) -> None:
        listed = self.receipt["calls"]["list_lab_profiles"]
        self.assertFalse(listed["is_error"])
        self.assertEqual(listed["profile_ids"], ["servicetracer-demo-api"])
        self.assertEqual(listed["release_states"], ["candidate"])

        prepared = self.receipt["calls"]["prepare_lab_request"]
        self.assertFalse(prepared["is_error"])
        self.assertEqual(prepared["operation"], "prepare_only")
        self.assertEqual(prepared["resource_group"], "rg-st-demo-api-test-westus2")
        self.assertEqual(prepared["missing_required_parameters"], [])
        self.assertTrue(prepared["ready_for_preflight"])
        self.assertTrue(prepared["what_if_required"])
        self.assertTrue(prepared["explicit_deployment_authorization_required"])
        self.assertEqual(prepared["next_gate"], "preflight_required")
        self.assertEqual(prepared["plan_digest"], PLAN_DIGEST)

        for execution in (listed["execution"], prepared["execution"]):
            self.assertFalse(execution["azure_queries_performed"])
            self.assertFalse(execution["azure_mutations_performed"])
            self.assertFalse(execution["deployment_authorized"])
            self.assertFalse(execution["cleanup_authorized"])

    def test_negative_evidence_remains_all_false(self) -> None:
        self.assertTrue(self.receipt["negative_evidence"])
        for key, value in self.receipt["negative_evidence"].items():
            self.assertFalse(value, key)

    def test_contract_and_reconciliation_are_terminal(self) -> None:
        self.assertEqual(
            self.contract["status"],
            "terminal_verified_exact_source_evidence_promoted",
        )
        self.assertEqual(
            self.contract["repository"]["exact_probed_source_head"],
            EXACT_SOURCE,
        )
        self.assertEqual(
            self.reconciliation["classification"],
            "terminal_verified_exact_source_local_MCP_protocol_evidence",
        )
        self.assertEqual(self.reconciliation["workflow"]["run_id"], 30505927462)
        self.assertEqual(self.reconciliation["workflow"]["job_id"], 90755550858)
        self.assertEqual(self.reconciliation["artifact"]["artifact_id"], 8745291415)
        self.assertFalse(
            self.reconciliation["repair_history"][2]["first_artifact_promoted"]
        )

    def test_no_sensitive_values_or_azure_identifiers_are_promoted(self) -> None:
        combined = "\n".join(
            (
                self.receipt_bytes.decode("utf-8"),
                self.manifest,
                json.dumps(self.contract, sort_keys=True),
                json.dumps(self.reconciliation, sort_keys=True),
                self.handoff,
            )
        )
        self.assertIsNone(UUID_PATTERN.search(combined))
        for forbidden in (
            "st-demo-api-mcp-probe-001",
            "https://probe.example.invalid",
            "https://backend.example.invalid/api/demo/run",
            "ProtocolProbeOnlyKey",
            "AZURE_OPENAI_API_KEY=",
            "OPENAI_API_KEY=",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
