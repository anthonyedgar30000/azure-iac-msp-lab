from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / ".project/current-reality-v2.json"
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "post-pr214-current-reality-20260729.json"
)

MAIN = "4136a47d9aa80da99e3849fc721bab55a883b20e"
PR214_SOURCE = "afdeaf6e4765ce4819ae3de5782cc5ca57cfcd12"
LEGACY_MAIN = "ca994ce53642587bea370bee1c5a0633faaaece8"


class PostPr214CurrentRealityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))

    def test_authoritative_overlay_advances_repository_state_through_pr214(self) -> None:
        overlay = self.current["authoritative_overlay"]
        repository = self.current[overlay["repository_state_pointer"]]

        self.assertEqual(self.current["schema_version"], "project.current-reality.v7")
        self.assertEqual(repository["observed_main"], MAIN)
        self.assertEqual(repository["latest_merged_pull_request"], 214)
        self.assertEqual(repository["latest_merge_commit"], MAIN)
        self.assertEqual(repository["latest_merged_source_head"], PR214_SOURCE)
        self.assertEqual(repository["open_pull_requests_observed"], [])
        self.assertEqual(
            set(repository["latest_exact_head_ci_runs"]),
            {
                "ci",
                "current_reality_lifecycle_reconciliation",
                "post_merge_pr82_shared_state_reconciliation",
                "azure_mcp_architecture_and_cloud_shell_plan",
            },
        )
        self.assertTrue(
            all(
                item["conclusion"] == "success"
                for item in repository["latest_exact_head_ci_runs"].values()
            )
        )

    def test_legacy_projection_is_preserved_but_not_authoritative(self) -> None:
        overlay = self.current["authoritative_overlay"]
        legacy = self.current["repository_state"]

        self.assertEqual(overlay["legacy_projection_status"], "historical_compatibility_only")
        self.assertEqual(legacy["classification"], "historical_pr185_compatibility_projection")
        self.assertEqual(legacy["observed_main"], LEGACY_MAIN)
        self.assertEqual(legacy["latest_merged_pull_request"], 185)
        self.assertNotEqual(
            legacy["observed_main"],
            self.current[overlay["repository_state_pointer"]]["observed_main"],
        )
        self.assertIn(
            "legacy_projection != current_repository_state",
            self.current["canonical_distinctions"],
        )

    def test_domain_overlay_preserves_evidence_and_uncertainty(self) -> None:
        domain = self.current[
            self.current["authoritative_overlay"]["domain_state_pointer"]
        ]

        factory = domain["azure_lab_factory_lite"]
        self.assertTrue(factory["repository_implementation_merged"])
        self.assertFalse(factory["azure_deployment_verified"])
        self.assertFalse(factory["arm_what_if_verified"])
        self.assertFalse(factory["cleanup_verified"])

        mcp = domain["azure_mcp_current_reality_run1"]
        self.assertEqual(mcp["subscription_name"], "Azure for Students")
        self.assertEqual(mcp["resource_group"], "rg-ai-msp-dev-eastus")
        self.assertEqual(mcp["openai_account"], "oai-msp-anthony-dev-eastus")
        self.assertEqual(mcp["observed_deployment_count"], 0)
        self.assertTrue(mcp["authorization_consumed"])
        self.assertFalse(mcp["rerun_authorized"])
        self.assertFalse(mcp["azure_mutations_performed"])

        runtime = domain["azure_ai_verified_runtime"]
        self.assertEqual(runtime["deployment"], "gpt-5-mini")
        self.assertTrue(runtime["model_response_verified"])
        self.assertFalse(runtime["arm_resource_identity_reconciled"])
        self.assertFalse(runtime["azure_openai_mcp_invocation_verified"])

    def test_reconciliation_is_repository_only_and_non_renewing(self) -> None:
        authority = self.reconciliation["authority"]
        self.assertTrue(authority["branch_creation"])
        self.assertTrue(authority["pull_request_creation"])
        self.assertTrue(authority["ordinary_pull_request_ci"])

        for key in (
            "pull_request_merge",
            "workflow_dispatch_or_rerun",
            "azure_authentication_or_query",
            "arm_what_if",
            "azure_mutation",
            "rbac_mutation",
            "model_call",
            "remote_mcp_deployment",
            "cleanup",
            "rollback",
        ):
            self.assertFalse(authority[key], key)

        boundaries = self.reconciliation["preserved_operational_boundaries"]
        self.assertFalse(boundaries["fresh_azure_query_performed_by_this_increment"])
        self.assertFalse(boundaries["azure_mutation_performed_by_this_increment"])
        self.assertFalse(boundaries["fresh_actual_cost_or_quota_observed"])


if __name__ == "__main__":
    unittest.main()
