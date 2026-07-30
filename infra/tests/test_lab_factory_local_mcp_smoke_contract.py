from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/smoke_test_lab_factory_mcp_stdio.py"
WORKFLOW = ROOT / ".github/workflows/lab-factory-mcp-local-smoke.yml"
RUNBOOK = ROOT / "docs/runbooks/lab-factory-local-mcp-smoke.md"
RECONCILIATION = (
    ROOT / ".project/reconciliations/lab-factory-local-mcp-smoke-v1-20260729.json"
)
TERMINAL = (
    ROOT
    / ".project/reconciliations/lab-factory-local-mcp-smoke-run1-terminal-20260729.json"
)
EVIDENCE = ROOT / ".project/evidence/lab-factory-mcp-local-smoke-run1.json"
EVIDENCE_DIGEST = ROOT / ".project/evidence/lab-factory-mcp-local-smoke-run1.sha256"


class LabFactoryLocalMcpSmokeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.runbook = RUNBOOK.read_text(encoding="utf-8")
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.terminal = json.loads(TERMINAL.read_text(encoding="utf-8"))
        cls.evidence_bytes = EVIDENCE.read_bytes()
        cls.evidence = json.loads(cls.evidence_bytes)
        cls.expected_evidence_digest = EVIDENCE_DIGEST.read_text(encoding="utf-8").split()[0]

    def test_reconciliation_preserves_the_bounded_authority(self) -> None:
        document = self.reconciliation
        self.assertEqual(
            document["schema_version"],
            "project.reconciliation.lab-factory-local-mcp-smoke.v1",
        )
        self.assertEqual(document["source_instruction"], "Proceed")
        self.assertEqual(
            document["repository"]["base_commit"],
            "8926a5b48db9bb7cb08523d337e43d20ba7ed69d",
        )
        self.assertEqual(document["status"], "candidate_pending_exact_head_smoke")

        authority = document["authority"]
        self.assertTrue(authority["local_MCP_client_call_to_repository_only_tools_authorized"])
        self.assertTrue(authority["ordinary_exact_head_CI_authorized"])
        for denied in (
            "get_current_reality_execution_authorized",
            "Azure_authentication_or_query_authorized",
            "ARM_What_If_authorized",
            "Azure_mutation_authorized",
            "Azure_deployment_authorized",
            "RBAC_mutation_authorized",
            "model_call_authorized",
            "remote_MCP_deployment_authorized",
            "ChatGPT_connection_authorized",
            "cleanup_authorized",
        ):
            self.assertFalse(authority[denied], denied)

    def test_terminal_reconciliation_records_the_observed_runs(self) -> None:
        terminal = self.terminal
        self.assertEqual(
            terminal["schema_version"],
            "project.reconciliation.lab-factory-local-mcp-smoke-run1-terminal.v1",
        )
        self.assertEqual(terminal["source_instruction"], "Proceed")
        self.assertEqual(
            terminal["status"],
            "passed_evidence_promoted_pending_final_exact_head_CI",
        )
        smoke = terminal["observed_runs"]["local_MCP_smoke"]
        self.assertEqual(smoke["workflow_run_id"], 30505376018)
        self.assertEqual(smoke["conclusion"], "success")
        self.assertEqual(smoke["artifact_id"], 8745096720)
        self.assertEqual(
            smoke["artifact_digest"],
            "sha256:4f87360b534339e402f9d7fa3b9984cefe399194be2db3dcc8a2d85e78edc466",
        )
        ci = terminal["observed_runs"]["repository_CI"]
        self.assertEqual(ci["workflow_run_id"], 30505375909)
        self.assertEqual(ci["conclusion"], "success")

    def test_promoted_receipt_matches_its_digest_and_terminal_record(self) -> None:
        actual = hashlib.sha256(self.evidence_bytes).hexdigest()
        self.assertEqual(actual, self.expected_evidence_digest)
        self.assertEqual(
            self.terminal["promoted_evidence"]["receipt_sha256"],
            self.expected_evidence_digest,
        )
        self.assertEqual(self.evidence["status"], "passed")
        self.assertEqual(
            self.evidence["source_sha"],
            "1aeead3a987dbe2af9af1c46c5ac1e85033991ce",
        )
        self.assertEqual(
            self.evidence["called_tools"],
            ["list_lab_profiles", "prepare_lab_request", "prepare_lab_request"],
        )
        self.assertFalse(self.evidence["get_current_reality_called"])
        self.assertFalse(self.evidence["azure_environment_forwarded_to_server"])
        self.assertFalse(self.evidence["azure_queries_performed"])
        self.assertFalse(self.evidence["azure_mutations_performed"])
        self.assertFalse(self.evidence["deployment_authorized"])
        self.assertFalse(self.evidence["cleanup_authorized"])

    def test_script_calls_only_the_repository_tools(self) -> None:
        self.assertIn('session.call_tool("list_lab_profiles"', self.script)
        self.assertEqual(self.script.count('session.call_tool("prepare_lab_request"'), 2)
        self.assertNotIn('session.call_tool("get_current_reality"', self.script)
        self.assertIn('"get_current_reality_called": False', self.script)
        self.assertIn('"azure_environment_forwarded_to_server": False', self.script)
        self.assertIn('"azure_queries_performed": False', self.script)
        self.assertIn('"azure_mutations_performed": False', self.script)
        self.assertIn('"deployment_authorized": False', self.script)
        self.assertIn('"cleanup_authorized": False', self.script)

    def test_script_reduces_the_child_environment_and_checks_determinism(self) -> None:
        self.assertIn("_safe_server_environment", self.script)
        self.assertNotIn('environment["AZURE_', self.script)
        self.assertNotIn('environment["OPENAI_API_KEY"', self.script)
        self.assertIn('args=["-m", "azure_mcp_reality.server", "--transport", "stdio"]', self.script)
        self.assertIn('first == second', self.script)
        self.assertIn('value not in serialized', self.script)
        self.assertIn('asyncio.wait_for', self.script)

    def test_workflow_has_no_cloud_or_manual_dispatch_authority(self) -> None:
        self.assertIn("contents: read", self.workflow)
        self.assertIn("id-token: none", self.workflow)
        self.assertNotIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("azure/login", self.workflow)
        self.assertNotIn("az ", self.workflow)
        self.assertNotIn("OPENAI_API_KEY: ${{", self.workflow)
        self.assertIn("Check out exact source head", self.workflow)
        self.assertIn("EXPECTED_SOURCE_SHA", self.workflow)
        self.assertIn("Validate promoted run-1 evidence", self.workflow)
        self.assertIn("smoke_test_lab_factory_mcp_stdio.py", self.workflow)
        self.assertIn("lab-factory-mcp-local-smoke-receipt", self.workflow)

    def test_runbook_states_the_evidence_boundary(self) -> None:
        for marker in (
            "local MCP client call verified != ChatGPT connected",
            "prepared request != ARM What-If",
            "get_current_reality",
            "parameter_values_returned: false",
            "azure_queries_performed: false",
            "azure_mutations_performed: false",
            "No Azure rollback or cleanup is required",
        ):
            self.assertIn(marker, self.runbook)


if __name__ == "__main__":
    unittest.main()
