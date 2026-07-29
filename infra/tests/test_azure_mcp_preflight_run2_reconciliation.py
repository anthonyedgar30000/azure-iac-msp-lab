from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-mcp-read-only-preflight-run2-success-20260729.json"
)
CONTRACT = ROOT / ".project" / "contracts" / "azure-mcp-template-review-v1.json"
MANIFEST = (
    ROOT
    / "infra"
    / "evidence"
    / "azure-mcp"
    / "azmcp-copilot-studio-aca-mi-20260729.sha256"
)
HANDOFF = ROOT / ".project" / "handoffs" / "post-pr193-mcp-preflight-run2-success.md"


class AzureMcpPreflightRun2ReconciliationTests(unittest.TestCase):
    def test_successful_run_is_recorded_without_mutation_claims(self) -> None:
        state = json.loads(RECONCILIATION.read_text(encoding="utf-8"))

        self.assertEqual(state["workflow_run"]["run_id"], 30418812664)
        self.assertEqual(state["workflow_run"]["run_attempt"], 1)
        self.assertEqual(state["workflow_run"]["conclusion"], "success")
        self.assertEqual(state["workflow_run"]["observation_failures"], 0)
        self.assertFalse(state["workflow_run"]["Azure_mutations_performed"])
        self.assertFalse(state["workflow_run"]["deployment_performed"])
        self.assertFalse(state["workflow_run"]["OpenAI_API_execution_performed"])
        self.assertEqual(
            state["Azure_observations"]["provider_states"]["Microsoft.App"],
            "NotRegistered",
        )
        self.assertEqual(
            state["Azure_observations"]["resource_group"]["observation_status"],
            "not_present",
        )

    def test_artifact_and_manifest_digests_are_exact(self) -> None:
        state = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        self.assertEqual(state["protected_artifact"]["artifact_id"], 8711131933)
        self.assertEqual(
            state["protected_artifact"]["digest"],
            "sha256:4867d34fd9ee64881f27a58ae5f534052de30583d830d9602d5833c4097a826b",
        )

        digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "0667efecb0eded85dc69b87deda2022e73b3dd879f0658659749e13587375b8a",
        )

    def test_template_review_fails_closed_on_unresolved_source(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

        self.assertEqual(
            contract["status"],
            "preflight_passed_content_manifest_pinned_source_commit_unresolved",
        )
        self.assertFalse(contract["template"]["exact_source_equality_verified"])
        self.assertEqual(
            contract["template"]["exact_source_commit_for_downloaded_content"],
            "unknown",
        )
        for decision in contract["approval_state"].values():
            self.assertFalse(decision)

    def test_active_state_index_collision_is_not_introduced(self) -> None:
        state = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        open_pr = state["repository_state"]["open_pull_requests"][0]

        self.assertEqual(open_pr["number"], 194)
        self.assertEqual(
            open_pr["overlapping_path_with_this_increment"],
            ".project/state-index.json",
        )
        self.assertTrue(open_pr["collision_avoided"])
        handoff = HANDOFF.read_text(encoding="utf-8")
        self.assertIn("does not modify `.project/state-index.json`", handoff)


if __name__ == "__main__":
    unittest.main()
