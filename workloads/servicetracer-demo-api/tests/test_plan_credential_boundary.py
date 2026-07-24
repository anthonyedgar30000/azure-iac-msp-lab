from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml"


class ServiceTracerDemoApiPlanCredentialBoundaryTests(unittest.TestCase):
    def test_read_only_planner_creates_no_credentials(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("ssh-keygen", source)
        self.assertNotIn("/tmp/servicetracer-demo-api-plan-key", source)
        self.assertIn("servicetracer-plan-placeholder-no-private-key", source)
        self.assertIn("credential_creation_authorized:false", source)
        self.assertIn("Credential creation authorized: `false`", source)


if __name__ == "__main__":
    unittest.main()
