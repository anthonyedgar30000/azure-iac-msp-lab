from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / ".project" / "handoffs" / "current-state.md"
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr212-canonical-handoff-20260729.json"
)
STATE_INDEX = ROOT / ".project" / "state-index.json"

EXPECTED_PATHS = {
    ".project/handoffs/current-state.md",
    ".project/reconciliations/post-pr212-canonical-handoff-20260729.json",
    "infra/tests/test_post_pr212_current_handoff.py",
}


class PostPr212CurrentHandoffTests(unittest.TestCase):
    def test_handoff_uses_post_pr212_repository_watermark(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")

        self.assertIn(
            "observed main: f8f29d8601666646d354ffc450a85348e891483f",
            text,
        )
        self.assertIn("latest merged PR: #212", text)
        self.assertIn(
            "PR #212 merge commit: f8f29d8601666646d354ffc450a85348e891483f",
            text,
        )
        self.assertNotIn("latest merged PR: #185", text)
        self.assertNotIn("Draft PR #186 is concurrently open", text)

    def test_handoff_classifies_lab_factory_without_cloud_overclaim(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")

        self.assertIn(
            "Azure Lab Factory Lite v1: merged repository implementation and exact-source CI verified",
            text,
        )
        self.assertIn("Azure Lab Factory deployment or operational use: not established", text)
        self.assertIn("merged planner != deployment authority", text)
        self.assertIn("cleanup definition != cleanup verified", text)

    def test_handoff_preserves_superseded_attempt_and_authority_boundaries(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")

        self.assertIn("Draft PR #213", text)
        self.assertIn("PR #213 merged: false", text)
        self.assertIn("PR #213 authority inherited by this branch: false", text)
        self.assertIn("MCP run-1 rerun authorized: false", text)
        self.assertIn("Azure authentication or query authorized: false", text)
        self.assertIn("Azure mutation authorized: false", text)
        self.assertIn("pull-request merge authorized by this handoff: false", text)

    def test_handoff_preserves_mcp_identity_uncertainty(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")

        self.assertIn("deployments in observed account: 0", text)
        self.assertIn("deployment: gpt-5-mini", text)
        self.assertIn("verified runtime ARM scope reconciled: false", text)
        self.assertIn("Azure OpenAI called MCP tool: false", text)
        self.assertIn("remote MCP endpoint deployed: false", text)

    def test_reconciliation_contract_is_bounded(self) -> None:
        data = json.loads(RECONCILIATION.read_text(encoding="utf-8"))

        self.assertEqual(set(data["permitted_paths"]), EXPECTED_PATHS)
        self.assertEqual(data["superseded_attempt"]["state"], "closed_unmerged")
        self.assertFalse(data["superseded_attempt"]["authority_transferred"])
        self.assertFalse(data["authority"]["pull_request_merge"])
        self.assertFalse(data["authority"]["workflow_dispatch_or_rerun"])
        self.assertFalse(data["authority"]["azure_authentication_or_query"])
        self.assertFalse(data["authority"]["arm_what_if"])
        self.assertFalse(data["authority"]["azure_mutation"])
        self.assertFalse(data["authority"]["model_call"])
        self.assertFalse(data["authority"]["remote_mcp_deployment"])

    def test_state_index_matches_terminal_authority_boundary(self) -> None:
        state = json.loads(STATE_INDEX.read_text(encoding="utf-8"))

        self.assertIsNone(state["active_deployment_authorization"])
        self.assertIsNone(state["active_azure_mcp_preflight_authorization"])
        self.assertIsNone(state["active_azure_mcp_current_reality_authorization"])
        self.assertIsNone(state["active_azure_ai_activation_authorization"])
        self.assertFalse(state["azure_mcp_current_reality_run1_rerun_authorized"])
        self.assertFalse(state["azure_mcp_current_reality_remote_endpoint_deployed"])
        self.assertFalse(state["azure_ai_mcp_connected"])
        self.assertFalse(state["azure_ai_verified_runtime_ARM_scope_reconciled"])


if __name__ == "__main__":
    unittest.main()
