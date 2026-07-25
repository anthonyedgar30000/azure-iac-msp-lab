import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "servicetracer_resource_group_cleanup.py"
SPEC = importlib.util.spec_from_file_location("cleanup", SCRIPT)
cleanup = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cleanup)


class CleanupAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.contract_path = ROOT / ".project" / "contracts" / "servicetracer-resource-group-boundary-cleanup.json"
        self.fixture_path = ROOT / "tests" / "fixtures" / "servicetracer-resource-group-cleanup-sample.json"

    def load_fixture(self):
        return json.loads(self.fixture_path.read_text(encoding="utf-8"))

    def test_contract_preserves_no_mutation_boundary(self):
        contract = cleanup.validate_contract(self.contract_path)
        self.assertFalse(contract["authority"]["azure_resource_delete_authorized"])
        self.assertFalse(contract["authority"]["azure_resource_move_authorized"])
        self.assertTrue(contract["resource_group_model"]["independent_demo_api"]["protected_from_this_cleanup"])

    def test_public_ip_reference_blocks_cleanup(self):
        assessment = cleanup.assess(self.load_fixture())
        public_ip = next(item for item in assessment["candidate_results"] if item["candidate_id"] == "collector-demo-public-ip")
        self.assertEqual(public_ip["cleanup_readiness"], "blocked")
        self.assertIn("public_ip_has_observed_attachment_reference", public_ip["blockers"])

    def test_missing_candidate_remains_not_observed(self):
        assessment = cleanup.assess(self.load_fixture())
        load_balancer = next(item for item in assessment["candidate_results"] if item["candidate_id"] == "collector-demo-load-balancer")
        self.assertEqual(load_balancer["observation_status"], "not_observed")
        self.assertEqual(load_balancer["cleanup_readiness"], "not_determined")

    def test_independent_resource_group_candidate_fails_closed(self):
        payload = self.load_fixture()
        payload["resource_graph_records"].append({
            "recordKind": "candidate",
            "id": "/subscriptions/sub/resourcegroups/rg-st-demo-api-dev-westus2/providers/microsoft.network/publicipaddresses/pip-st-demo-api-vm-mst-dev",
            "name": "pip-st-demo-api-vm-mst-dev",
            "type": "microsoft.network/publicipaddresses",
            "resourceGroup": "rg-st-demo-api-dev-westus2"
        })
        with self.assertRaises(cleanup.CleanupError):
            cleanup.assess(payload)

    def test_truncated_query_fails_closed(self):
        payload = self.load_fixture()
        payload["metadata"]["query_complete"] = False
        with self.assertRaises(cleanup.CleanupError):
            cleanup.assess(payload)

    def test_output_is_deterministic(self):
        payload = self.load_fixture()
        self.assertEqual(cleanup.assess(payload), cleanup.assess(json.loads(json.dumps(payload))))
        self.assertFalse(cleanup.assess(payload)["summary"]["deletion_authorized"])


if __name__ == "__main__":
    unittest.main()
