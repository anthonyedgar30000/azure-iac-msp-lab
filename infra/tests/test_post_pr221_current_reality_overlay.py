import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OVERLAY_PATH = ROOT / ".project" / "current-reality-post-pr221.json"
RECONCILIATION_PATH = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr221-current-reality-overlay-20260729.json"
)


class PostPr221CurrentRealityOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(
            RECONCILIATION_PATH.read_text(encoding="utf-8")
        )

    def test_repository_watermark(self) -> None:
        repository = self.overlay["repository_state"]
        self.assertEqual(
            repository["observed_main"],
            "82191482f48ccb81dc50b5966733a9d8ff7f2953",
        )
        self.assertEqual(repository["latest_merged_pull_request"], 221)
        self.assertEqual(repository["open_pull_requests_observed"], [])

    def test_local_mcp_observation_is_bounded(self) -> None:
        observation = self.overlay["local_MCP_observation"]
        self.assertTrue(observation["lab_factory_tools_live_client_call_observed"])
        self.assertEqual(
            observation["called_tools"],
            ["list_lab_profiles", "prepare_lab_request", "prepare_lab_request"],
        )
        self.assertFalse(observation["get_current_reality_called"])
        self.assertFalse(observation["azure_queries_performed"])
        self.assertFalse(observation["azure_mutations_performed"])
        self.assertFalse(observation["deployment_authorized"])
        self.assertFalse(observation["chatgpt_connection_verified"])

    def test_evidence_and_ci_are_exact(self) -> None:
        evidence = self.overlay["evidence"]
        validation = self.overlay["exact_head_validation"]
        self.assertEqual(
            evidence["receipt_sha256"],
            "c7a3243108af9bca860c362c333171fce361baf7f23a56774cc83ae21a4d7fc3",
        )
        self.assertEqual(validation["repository_CI"]["run_id"], 30505701542)
        self.assertEqual(
            validation["lab_factory_local_MCP_smoke"]["run_id"], 30505701531
        )
        self.assertEqual(validation["repository_CI"]["conclusion"], "success")
        self.assertEqual(
            validation["lab_factory_local_MCP_smoke"]["conclusion"], "success"
        )

    def test_no_cloud_authority_is_created(self) -> None:
        boundary = self.overlay["azure_boundary"]
        self.assertTrue(all(value is False for value in boundary.values()))
        authority = self.reconciliation["authority_boundary"]
        self.assertFalse(authority["azure_authentication"])
        self.assertFalse(authority["azure_query"])
        self.assertFalse(authority["ARM_What_If"])
        self.assertFalse(authority["azure_mutation"])
        self.assertFalse(authority["deployment"])
        self.assertFalse(authority["model_call"])
        self.assertFalse(authority["remote_MCP_deployment"])

    def test_historical_projection_is_not_rewritten(self) -> None:
        repair = self.reconciliation["repair"]
        self.assertFalse(repair["historical_projection_rewritten"])
        self.assertIn(
            "Resolve this overlay together with .project/current-reality-v2.json",
            self.overlay["selection_rule"],
        )


if __name__ == "__main__":
    unittest.main()
