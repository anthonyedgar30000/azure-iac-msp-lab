from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml"
BICEP = ROOT / "workloads" / "servicetracer-demo-api" / "infra" / "main.bicep"
EXPECTED_SIZE = "Standard_B2ats_v2"


class DemoApiVmSizeContractTests(unittest.TestCase):
    def test_planner_and_bicep_use_proven_vm_size(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        bicep = BICEP.read_text(encoding="utf-8")
        self.assertIn(f"default: {EXPECTED_SIZE}", workflow)
        self.assertIn(f"param vmSize string = '{EXPECTED_SIZE}'", bicep)
        self.assertNotIn("default: Standard_B1s", workflow)
        self.assertNotIn("param vmSize string = 'Standard_B1s'", bicep)


if __name__ == "__main__":
    unittest.main()
