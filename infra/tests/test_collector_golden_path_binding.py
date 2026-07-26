import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run"
INDEPENDENT = "https://st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com/api/demo/run"


class CollectorGoldenPathBindingTests(unittest.TestCase):
    def test_current_frontend_is_bound_to_collector_endpoint(self):
        config = json.loads((ROOT / "docs/report-source.json").read_text(encoding="utf-8"))
        self.assertEqual(config["live_demo_api_url"], COLLECTOR)
        self.assertEqual(config["candidate_demo_api_url"], COLLECTOR)
        self.assertEqual(config["activation_status"], "collector_live_default_pending_github_pages_verification")
        self.assertNotEqual(config["live_demo_api_url"], INDEPENDENT)

    def test_active_validators_cannot_accept_independent_endpoint(self):
        for relative in (
            ".project/validate.py",
            "scripts/verify_frontend_live_default.mjs",
            "infra/tests/test_frontend_live_default_activation.py",
            "infra/tests/test_collector_demo_api.py",
    "infra/tests/test_frontend_api_demo_lab_integration.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(COLLECTOR, text, relative)
            self.assertNotIn(INDEPENDENT, text, relative)

    def test_canonical_state_keeps_independent_api_outside_golden_path(self):
        state = json.loads((ROOT / ".project/current-reality-v2.json").read_text(encoding="utf-8"))
        self.assertEqual(state["collector_demo_api"]["frontend_binding"]["configured_endpoint"], COLLECTOR)
        self.assertTrue(state["collector_demo_api"]["frontend_binding"]["collector_golden_path_required"])
        self.assertFalse(state["independent_demo_api"]["collector_golden_path"])


if __name__ == "__main__":
    unittest.main()
