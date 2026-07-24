from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RECONCILIATION = ROOT / ".project" / "reconciliations" / "post-merge-pr75-pr77.json"
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml"
BICEP = ROOT / "workloads" / "servicetracer-demo-api" / "infra" / "main.bicep"
ACTIVE_WORK = ROOT / ".project" / "active-work.json"
ENVIRONMENT_STATE = ROOT / ".project" / "environment-state.json"


class PostMergeRealitySynchronizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.bicep = BICEP.read_text(encoding="utf-8")
        cls.active_work = json.loads(ACTIVE_WORK.read_text(encoding="utf-8"))
        cls.environment_state = json.loads(ENVIRONMENT_STATE.read_text(encoding="utf-8"))

    def test_exact_post_merge_watermark_is_recorded(self) -> None:
        repository = self.record["repository_reality"]
        self.assertEqual(
            repository["main_commit"],
            "0d364dac63fb948c4912e04a2f420df4451189cb",
        )
        self.assertEqual(repository["open_pull_requests_observed"], [])
        merges = {item["pull_request"]: item for item in repository["merged_pull_requests"]}
        self.assertEqual(
            merges[75]["merge_commit"],
            "1ae445831668131f495f39f4d887822885fc1ec0",
        )
        self.assertEqual(
            merges[77]["merge_commit"],
            "0d364dac63fb948c4912e04a2f420df4451189cb",
        )
        self.assertTrue(all(run["conclusion"] == "success" for item in merges.values() for run in item["exact_head_ci"]))

    def test_current_workflow_and_bicep_use_selected_package(self) -> None:
        declaration = self.record["current_repository_declaration"]
        self.assertEqual(declaration["location"], "westus2")
        self.assertEqual(declaration["vm_size"], "Standard_F1als_v7")
        self.assertIn("default: westus2", self.workflow)
        self.assertIn("default: Standard_F1als_v7", self.workflow)
        self.assertIn("param location string = 'westus2'", self.bicep)
        self.assertIn("param vmSize string = 'Standard_F1als_v7'", self.bicep)
        self.assertNotIn("az deployment sub create", self.workflow)

    def test_historical_project_state_is_preserved_as_a_typed_conflict(self) -> None:
        architecture = self.active_work["architecture_baseline"]
        self.assertEqual(architecture["repository_default_location"], "eastus")
        self.assertEqual(architecture["approved_default_vm_size"], "Standard_B2ats_v2")
        facts = {fact["fact_id"]: fact for fact in self.environment_state["facts"]}
        self.assertIn("Standard_B2ats_v2", facts["independent-demo-api-vm-size"]["value"])
        observation = self.record["shared_project_state_observation"]
        self.assertEqual(observation["status"], "conflicting_with_current_repository_declaration")
        self.assertFalse(self.record["resolution"]["shared_project_state_fully_reconciled"])
        self.assertEqual(self.record["resolution"]["verification_status"], "conflicting")

    def test_operational_authority_remains_fail_closed(self) -> None:
        authority = self.record["authority"]
        for field in (
            "pull_request_merge_authorized",
            "workflow_dispatch_authorized",
            "azure_authentication_authorized",
            "azure_what_if_authorized",
            "azure_mutations_authorized",
            "deployment_authorized",
            "cleanup_authorized",
            "endpoint_promotion_authorized",
        ):
            self.assertFalse(authority[field], field)
        boundary = self.record["azure_evidence_boundary"]
        self.assertFalse(boundary["protected_westus2_f1alsv7_evidence"])
        self.assertFalse(boundary["current_cost_verified"])
        self.assertFalse(boundary["arm_validation_performed_for_selected_package"])
        self.assertFalse(boundary["what_if_performed_for_selected_package"])
        self.assertFalse(boundary["deployed"])
        self.assertFalse(boundary["service_verified"])

    def test_exact_future_dispatch_inputs_are_bounded(self) -> None:
        gate = self.record["next_gate"]
        self.assertTrue(gate["required_main_refresh_after_merge"])
        self.assertEqual(
            gate["required_exact_confirmation"],
            "PLAN-DEMO-API-SUBPROJECT:dev:st-demo-api-vm-aeg30000",
        )
        inputs = gate["required_inputs"]
        self.assertEqual(inputs["location"], "westus2")
        self.assertEqual(inputs["vm_size"], "Standard_F1als_v7")
        self.assertEqual(inputs["target_resource_group"], "rg-st-demo-api-dev-westus2")
        self.assertEqual(inputs["maximum_monthly_cost_cad"], "25.00")


if __name__ == "__main__":
    unittest.main()
