import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_COLLECTOR = "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run"
INDEPENDENT = "https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/demo/run"


class CollectorGoldenPathBindingTests(unittest.TestCase):
    def test_current_frontend_is_bound_to_independent_endpoint(self):
        config = json.loads((ROOT / "docs/report-source.json").read_text(encoding="utf-8"))
        self.assertEqual(config["live_demo_api_url"], INDEPENDENT)
        self.assertEqual(config["candidate_demo_api_url"], INDEPENDENT)
        self.assertEqual(
            config["activation_status"],
            "independent_demo_api_live_default_pending_github_pages_verification",
        )
        self.assertNotEqual(config["live_demo_api_url"], HISTORICAL_COLLECTOR)
        self.assertEqual(
            config["expected_azure_host"],
            {
                "resource_group": "rg-st-demo-api-dev-westus2",
                "vm_name": "vm-st-demo-api-mst-dev",
                "location": "westus2",
                "hosting_model": "dedicated_vm_subproject",
            },
        )

    def test_active_validators_accept_only_current_independent_endpoint(self):
        for relative in (
            ".project/validate_current.py",
            "scripts/verify_frontend_live_default.mjs",
            "infra/tests/test_frontend_live_default_activation.py",
            "infra/tests/test_frontend_api_demo_lab_integration.py",
            "infra/tests/test_frontend_azure_provenance_monitor.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(INDEPENDENT, text, relative)

    def test_historical_collector_golden_path_record_is_not_rewritten(self):
        state = json.loads((ROOT / ".project/current-reality-v2.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state["collector_demo_api"]["frontend_binding"]["configured_endpoint"],
            HISTORICAL_COLLECTOR,
        )
        self.assertTrue(
            state["collector_demo_api"]["frontend_binding"]["collector_golden_path_required"]
        )
        self.assertFalse(state["independent_demo_api"]["collector_golden_path"])


if __name__ == "__main__":
    unittest.main()
