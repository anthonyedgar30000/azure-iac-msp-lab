from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RETIRED_DISPATCHER = (
    ROOT / ".github" / "workflows" / "correlation-identity-deploy-run1.yml"
)
COLLECTOR_WORKFLOW = ROOT / ".github" / "workflows" / "collector-demo-api.yml"
REQUEST = (
    ROOT
    / ".project"
    / "deployment-requests"
    / "correlation-identity-run1.json"
)
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "correlation-identity-run1-terminal-20260727.json"
)


class CorrelationIdentityReplayQuarantineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = COLLECTOR_WORKFLOW.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.executable_workflow = "\n".join(
            line for line in cls.workflow.splitlines() if not line.lstrip().startswith("#")
        )

    def test_consumed_one_shot_dispatcher_is_retired(self) -> None:
        self.assertFalse(RETIRED_DISPATCHER.exists())

    def test_shared_child_workflow_is_fail_closed_without_cloud_identity(self) -> None:
        self.assertIn("Collector-hosted demo API — quarantined", self.workflow)
        self.assertIn("unauthorized replay of consumed one-shot authority", self.workflow)
        self.assertNotIn("id-token: write", self.executable_workflow)
        self.assertNotIn("environment: azure-lab", self.executable_workflow)
        self.assertNotIn("azure/login", self.executable_workflow)
        self.assertNotIn("az ", self.executable_workflow)
        self.assertIn("exit 1", self.executable_workflow)

    def test_request_is_consumed_and_cannot_authorize_another_attempt(self) -> None:
        self.assertEqual(
            self.request["status"],
            "consumed_with_unauthorized_replay_observed",
        )
        self.assertFalse(self.request["active"])
        authority = self.request["authority"]
        self.assertEqual(authority["attempt_limit"], 1)
        self.assertFalse(authority["renewable"])
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        self.assertEqual(len(self.request["observed_attempts"]), 2)

    def test_attempt_one_was_authorized_and_attempt_two_was_not(self) -> None:
        first, second = self.request["observed_attempts"]
        self.assertEqual(first["authority_classification"], "authorized_consuming_attempt")
        self.assertEqual(first["child_deployment_run"], 30310439500)
        self.assertEqual(
            second["authority_classification"],
            "unauthorized_replay_after_consumption",
        )
        self.assertEqual(second["child_deployment_run"], 30315658677)
        for attempt in (first, second):
            self.assertEqual(attempt["arm_deployment"], "Succeeded")
            self.assertEqual(attempt["vm_extension"], "Succeeded")
            self.assertEqual(attempt["live_api_health"], "verified")
            self.assertEqual(attempt["request_identity"], "verified")
            self.assertEqual(attempt["transactions"], 20)
            self.assertFalse(attempt["rollback_performed"])

    def test_reconciliation_preserves_authority_and_runtime_as_separate_truths(self) -> None:
        self.assertEqual(
            self.reconciliation["root_cause"]["classification"],
            "authorization_consumption_control_failure",
        )
        attempts = self.reconciliation["attempts"]
        self.assertEqual(attempts[0]["classification"], "authorized_consuming_attempt")
        self.assertEqual(
            attempts[1]["classification"],
            "unauthorized_replay_after_consumption",
        )
        self.assertFalse(attempts[1]["authority_valid"])
        self.assertEqual(
            self.reconciliation["containment"]["shared_deployment_workflow"],
            "quarantined_fail_closed",
        )
        self.assertFalse(
            self.reconciliation["containment"]["oidc_permission_present"]
        )
        self.assertFalse(
            self.reconciliation["containment"]["azure_commands_present"]
        )


if __name__ == "__main__":
    unittest.main()
