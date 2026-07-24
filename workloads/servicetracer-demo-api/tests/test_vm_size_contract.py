import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml"
BICEP = ROOT / "workloads" / "servicetracer-demo-api" / "infra" / "main.bicep"
RECONCILIATION = ROOT / ".project" / "reconciliations" / "independent-demo-api-westus2-f1alsv7.json"
EXPECTED_LOCATION = "westus2"
EXPECTED_SIZE = "Standard_F1als_v7"


class DemoApiVmSizeContractTests(unittest.TestCase):
    def test_planner_and_bicep_use_evidence_backed_candidate(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        bicep = BICEP.read_text(encoding="utf-8")
        self.assertIn(f"default: {EXPECTED_LOCATION}", workflow)
        self.assertIn(f'[[ "$LOCATION" == \'{EXPECTED_LOCATION}\' ]]', workflow)
        self.assertIn(f"default: {EXPECTED_SIZE}", workflow)
        self.assertIn(f'[[ "$VM_SIZE" == \'{EXPECTED_SIZE}\' ]]', workflow)
        self.assertIn(f"param location string = '{EXPECTED_LOCATION}'", bicep)
        self.assertIn(f"param vmSize string = '{EXPECTED_SIZE}'", bicep)
        for superseded in ("Standard_B1s", "Standard_B2ats_v2", "Standard_F2s_v2"):
            self.assertNotIn(f"default: {superseded}", workflow)
            self.assertNotIn(f"param vmSize string = '{superseded}'", bicep)

    def test_candidate_reconciliation_preserves_evidence_and_authority_boundaries(self):
        record = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        self.assertEqual(
            record["schema_version"],
            "project.independent-demo-api-candidate-reconciliation.v1",
        )
        package = record["selected_read_only_package"]
        self.assertEqual(package["location"], EXPECTED_LOCATION)
        self.assertEqual(package["vm_size"], EXPECTED_SIZE)
        self.assertEqual(package["target_resource_group"], "rg-st-demo-api-dev-westus2")
        evidence = record["interactive_candidate_evidence"]
        self.assertFalse(evidence["protected_artifact"])
        self.assertEqual(evidence["restrictions"], [])
        self.assertEqual(evidence["total_regional_vcpu"], {"current": 0, "limit": 10})
        self.assertEqual(evidence["vm_family_vcpu"], {"current": 0, "limit": 10})
        self.assertEqual(evidence["standard_ipv4_public_ips"], {"current": 0, "limit": 20})
        ownership = record["path_ownership"]
        self.assertFalse(ownership["overlap_with_pr_77"])
        self.assertFalse(ownership["overlapping_project_state_paths_modified"])
        self.assertEqual(record["starting_reality"]["competing_open_pull_request"], 77)
        authority = record["authority"]
        self.assertTrue(authority["repository_increment_authorized"])
        self.assertTrue(authority["pull_request_creation_authorized"])
        for field in (
            "pull_request_merge_authorized",
            "workflow_dispatch_authorized",
            "azure_authentication_authorized",
            "azure_mutations_authorized",
            "deployment_authorized",
            "cleanup_authorized",
            "endpoint_promotion_authorized",
        ):
            self.assertFalse(authority[field])


if __name__ == "__main__":
    unittest.main()
