from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = ROOT / ".project" / "stategraph-adoption.json"
STRATEGY_PATH = ROOT / "docs" / "designs" / "stategraph-optional-adoption-strategy.md"


class StategraphAdoptionStrategyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.decision = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
        self.strategy = STRATEGY_PATH.read_text(encoding="utf-8")

    def test_capability_is_optional_and_design_for(self) -> None:
        decision = self.decision["decision"]
        operating_model = self.decision["operating_model"]

        self.assertEqual(decision["capability"], "Stategraph")
        self.assertEqual(decision["build_priority"], "Design For")
        self.assertTrue(operating_model["optional"])
        self.assertTrue(operating_model["non_authoritative_until_explicitly_promoted"])

    def test_governing_question_is_exact(self) -> None:
        expected = (
            "Does Stategraph help push the MSP demo lab forward faster "
            "and with more confidence?"
        )
        self.assertEqual(self.decision["decision"]["governing_question"], expected)
        self.assertIn(expected, self.strategy)

    def test_current_bicep_path_is_not_rewritten_for_the_experiment(self) -> None:
        boundary = self.decision["current_boundary"]

        self.assertEqual(boundary["active_iac_path"], "Bicep")
        self.assertFalse(boundary["terraform_state_available_for_adoption"])
        self.assertFalse(boundary["stategraph_in_current_deployment_path"])
        self.assertFalse(boundary["duplicate_bicep_to_terraform_translation_authorized"])

    def test_standard_terraform_or_opentofu_fallback_is_mandatory(self) -> None:
        operating_model = self.decision["operating_model"]

        self.assertTrue(operating_model["standard_terraform_or_opentofu_fallback_required"])
        self.assertFalse(operating_model["stategraph_failure_blocks_standard_fallback"])
        self.assertIn("Standard Terraform/OpenTofu remains the fallback", self.strategy)

    def test_no_stategraph_or_azure_execution_is_authorized(self) -> None:
        authority = self.decision["authority"]

        for field in (
            "pull_request_merge",
            "workflow_dispatch_or_rerun",
            "stategraph_account_creation",
            "stategraph_installation_or_authentication",
            "stategraph_import_export_plan_or_apply",
            "terraform_or_opentofu_state_access_or_migration",
            "azure_authentication_or_query",
            "azure_mutation_or_deployment",
            "rbac_network_policy_monitoring_or_cleanup_mutation",
        ):
            self.assertFalse(authority[field], field)

    def test_adoption_is_staged_and_reversible(self) -> None:
        phases = self.decision["phases"]

        self.assertEqual([phase["phase"] for phase in phases], [0, 1, 2, 3])
        self.assertEqual(phases[0]["name"], "capability_check")
        self.assertFalse(phases[0]["state_import_authorized_by_this_record"])
        self.assertFalse(phases[0]["apply_authorized_by_this_record"])
        self.assertIn("standard_fallback_resume_test", phases[1]["required_proof"])
        self.assertFalse(phases[2]["stategraph_plan_is_accepted_plan"])
        self.assertEqual(phases[3]["first_execution_scope"], "one_low_risk_real_increment")

    def test_lab_v1_scope_admission_remains_fail_closed(self) -> None:
        alignment = self.decision["lab_v1_alignment"]

        self.assertFalse(alignment["parallel_feature_expansion_allowed"])
        self.assertTrue(alignment["must_not_delay_higher_priority_criterion"])
        self.assertEqual(
            alignment["current_disposition"],
            "design_for_until_admitted_real_increment",
        )

    def test_canonical_boundaries_are_preserved(self) -> None:
        boundaries = set(self.decision["canonical_boundaries"])
        expected = {
            "Bicep_current_path != Terraform_state_available",
            "strategy_accepted != execution_authorized",
            "Design_For != Build_Now",
            "optional_capability != operational_authority",
            "Stategraph_plan != accepted_plan",
            "plan_agreement != deployment_authority",
            "Stategraph_record != Azure_reality",
        }

        self.assertTrue(expected.issubset(boundaries))
        for marker in expected:
            self.assertIn(marker, self.strategy)


if __name__ == "__main__":
    unittest.main()
