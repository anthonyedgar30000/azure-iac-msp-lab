from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/one-shot-collector-provenance-run20.yml"
REQUEST = ROOT / ".project/deployment-requests/collector-provenance-run20.json"
INSTALLER = ROOT / "infra/scripts/install_collector_demo_api.sh"
SOURCE = "be7a0215a2ac47dd038b042e6b21e3c2e155d86a"


class OneShotCollectorProvenanceRun20Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.installer = INSTALLER.read_text(encoding="utf-8")

    def test_request_is_exact_finite_and_nonrenewing(self) -> None:
        request = self.request
        self.assertEqual(
            request["schema_version"],
            "project.collector-provenance-deployment-request.v1",
        )
        self.assertEqual(request["request_id"], "collector-provenance-run20")
        self.assertEqual(request["status"], "authorized_unconsumed")
        self.assertEqual(request["tracking_issue"], 140)
        self.assertEqual(request["execution"]["operation"], "deploy")
        self.assertEqual(request["execution"]["reviewed_commit"], SOURCE)
        self.assertEqual(request["authority"]["attempt_limit"], 1)
        self.assertFalse(request["authority"]["renewable"])
        self.assertFalse(request["authority"]["transferable"])
        self.assertFalse(request["authority"]["automatic_retry_authorized"])
        self.assertFalse(request["authority"]["rollback_authorized"])
        self.assertEqual(request["authorized_mutation_scope"]["creates"], 0)
        self.assertEqual(request["authorized_mutation_scope"]["deletes"], 0)
        self.assertEqual(request["authorized_mutation_scope"]["replaces"], 0)
        self.assertEqual(len(request["authorized_mutation_scope"]["modifies"]), 3)

        issued = datetime.fromisoformat(request["issued_at"])
        expires = datetime.fromisoformat(request["valid_until"])
        self.assertLess(issued, expires)

    def test_dispatcher_is_push_bounded_and_contains_no_azure_commands(self) -> None:
        workflow = self.workflow
        self.assertIn("branches: [main]", workflow)
        self.assertIn(
            "'.project/deployment-requests/collector-provenance-run20.json'",
            workflow,
        )
        self.assertIn("actions: write", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("gh workflow run collector-demo-api.yml", workflow)
        self.assertIn("-f operation=deploy", workflow)
        self.assertIn("No second dispatch will be issued", workflow)
        self.assertNotIn("azure/login", workflow)
        self.assertNotIn("az deployment", workflow)
        self.assertNotIn("gh run rerun", workflow)
        self.assertNotIn("rerun_failed", workflow)

    def test_reviewed_source_contains_the_service_restart_repair(self) -> None:
        installer = self.installer
        self.assertIn('systemctl enable "$SERVICE_NAME"', installer)
        self.assertIn('systemctl restart "$SERVICE_NAME"', installer)
        self.assertIn('systemctl is-active --quiet "$SERVICE_NAME"', installer)
        self.assertNotIn('systemctl enable --now "$SERVICE_NAME"', installer)


if __name__ == "__main__":
    unittest.main()
