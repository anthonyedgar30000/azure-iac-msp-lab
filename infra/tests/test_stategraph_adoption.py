from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPABILITY = ROOT / ".project" / "stategraph-capability.json"
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "pre-stategraph-adoption-20260725.json"
)
DOCUMENT = ROOT / "docs" / "architecture" / "stategraph-adoption.md"
LAB_V1_GATE = ROOT / ".project" / "lab-v1-completion-gate.json"


class StategraphAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capability = json.loads(CAPABILITY.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(
            RECONCILIATION.read_text(encoding="utf-8")
        )
        cls.document = DOCUMENT.read_text(encoding="utf-8")
        cls.lab_v1_gate = json.loads(LAB_V1_GATE.read_text(encoding="utf-8"))

    def test_stategraph_is_optional_and_not_build_now(self) -> None:
        current = self.capability["current_classification"]
        self.assertEqual(current["priority"], "Design For")
        self.assertFalse(current["build_now"])
        self.assertIn("optional working capability", self.capability["objective"])
        self.assertIn(
            "faster and with more confidence",
            self.capability["governing_question"],
        )

    def test_existing_bicep_authority_is_preserved(self) -> None:
        reality = self.capability["current_reality"]
        boundaries = self.capability["architecture_boundaries"]
        self.assertEqual(reality["existing_iac_authority"], "Bicep")
        self.assertFalse(reality["terraform_root_present"])
        self.assertFalse(reality["stategraph_runtime_available"])
        self.assertEqual(
            boundaries["existing_servicetracer_resources"]["owner"],
            "Bicep",
        )
        self.assertFalse(
            boundaries["existing_servicetracer_resources"][
                "terraform_import_allowed"
            ]
        )

    def test_standard_terraform_fallback_is_mandatory(self) -> None:
        pilot = self.capability["architecture_boundaries"][
            "first_eligible_pilot"
        ]
        fallback = self.capability["architecture_boundaries"]["fallback"]
        self.assertEqual(pilot["initial_execution_path"], "standard Terraform")
        self.assertEqual(pilot["initial_stategraph_mode"], "advisory shadow")
        self.assertFalse(pilot["stategraph_apply_enabled"])
        self.assertTrue(fallback["required"])
        self.assertEqual(fallback["path"], "standard Terraform")

    def test_lab_v1_gate_remains_controlling(self) -> None:
        self.assertFalse(
            self.lab_v1_gate["scope_control"][
                "parallel_feature_expansion_allowed"
            ]
        )
        self.assertFalse(
            self.reconciliation["lab_v1_gate"][
                "stategraph_build_now_admitted"
            ]
        )
        self.assertEqual(
            self.reconciliation["lab_v1_gate"]["classification"],
            "design_for",
        )

    def test_no_operational_authority_is_created(self) -> None:
        authority = self.capability["authority"]
        for value in authority.values():
            self.assertFalse(value)

        reconciliation_authority = self.reconciliation["authority"]
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_or_rerun_authorized",
            "azure_authentication_authorized",
            "azure_query_authorized",
            "azure_mutation_authorized",
            "terraform_plan_authorized",
            "terraform_apply_authorized",
            "stategraph_apply_authorized",
        ):
            self.assertFalse(reconciliation_authority[key])

    def test_document_preserves_core_boundaries(self) -> None:
        for marker in (
            "Stategraph unavailable",
            "standard Terraform continues",
            "repository_adoption != working_capability",
            "plan_created != apply_authorized",
            "existing ServiceTracer IaC owner = Bicep",
        ):
            self.assertIn(marker, self.document)


if __name__ == "__main__":
    unittest.main()
