from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/servicetracer-demo-api-plan-run1-synchronize-dispatcher.yml"


class ServiceTracerPlanRun1SynchronizeDispatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_recovery_is_one_synchronize_event_only(self) -> None:
        workflow = self.workflow
        self.assertIn("types: [synchronize]", workflow)
        self.assertIn("trigger/servicetracer-demo-api-plan-run1", workflow)
        self.assertIn("synchronize_recovery_requested == true", workflow)
        self.assertIn("gh workflow run servicetracer-demo-api-subproject-plan.yml", workflow)
        self.assertIn("--ref main", workflow)
        self.assertIn("authority_consumed:true", workflow)
        self.assertIn("retry_authorized:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)
        for forbidden in (
            "az deployment sub create",
            "az group create",
            "az provider register",
            "az role assignment create",
            "gh run rerun",
        ):
            self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
