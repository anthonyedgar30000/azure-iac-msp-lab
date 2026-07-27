from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "correlation-identity-deploy-run1.yml"
REQUEST = (
    ROOT
    / ".project"
    / "deployment-requests"
    / "correlation-identity-run1.json"
)


class CorrelationIdentityDeployRun1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))

    def test_trigger_is_exact_opened_pull_request_and_not_merge_driven(self) -> None:
        for required in (
            "pull_request:",
            "types: [opened]",
            ".project/triggers/correlation-identity-deploy-run1.json",
            "github.event.action == 'opened'",
            "github.base_ref == 'main'",
            "github.head_ref == 'trigger/correlation-identity-deploy-run1'",
            ".merge_authorized == false",
            ".retry_authorized == false",
        ):
            self.assertIn(required, self.workflow)
        self.assertNotIn("push:\n", self.workflow)
        self.assertNotIn("workflow_dispatch:\n", self.workflow)

    def test_request_binds_exact_ci_tested_fix(self) -> None:
        self.assertEqual(self.request["tracking_issue"], 179)
        self.assertEqual(self.request["source"]["repair_pull_request"], 178)
        self.assertEqual(
            self.request["source"]["exact_head"],
            "0b6b5322f25b3d0289f6c0febdcfd800ea4b909a",
        )
        self.assertEqual(
            self.request["source"]["merge_commit"],
            "e2b0aee4c4f9e0042036042d7892b7d51ec17e2e",
        )
        self.assertEqual(self.request["source"]["ci_run_id"], 30309238071)
        self.assertEqual(self.request["source"]["ci_conclusion"], "success")
        self.assertEqual(
            self.request["execution"]["reviewed_commit"],
            self.request["source"]["exact_head"],
        )

    def test_authority_is_one_attempt_nonrenewing_and_zero_create(self) -> None:
        authority = self.request["authority"]
        self.assertEqual(authority["attempt_limit"], 1)
        self.assertFalse(authority["renewable"])
        self.assertFalse(authority["transferable"])
        self.assertFalse(authority["automatic_retry_authorized"])
        self.assertFalse(authority["rollback_authorized"])
        scope = self.request["authorized_mutation_scope"]
        self.assertEqual(scope["creates"], 0)
        self.assertEqual(scope["deletes"], 0)
        self.assertEqual(scope["replaces"], 0)
        self.assertEqual(len(scope["modifies"]), 3)

    def test_dispatch_uses_existing_governed_workflow_once(self) -> None:
        for required in (
            "gh workflow run collector-demo-api.yml",
            "--ref main",
            "-f operation=deploy",
            '-f reviewed_commit="$REVIEWED_COMMIT"',
            "The one-shot grant is now **consumed**",
            "No second dispatch will be issued",
            "No retry or rollback was performed",
        ):
            self.assertIn(required, self.workflow)
        self.assertNotIn("gh run rerun", self.workflow)
        self.assertNotIn("rerun-failed-jobs", self.workflow)

    def test_independent_verification_is_source_and_identity_bound(self) -> None:
        for required in (
            "gh run watch \"$run_id\" --interval 10",
            "observed_source",
            "for attempt in $(seq 1 12)",
            "Access-Control-Request-Headers: Content-Type, X-ServiceTracer-Request-ID",
            "X-ServiceTracer-Request-ID: $request_id",
            "assert post_headers['x-servicetracer-request-id'] == request_id",
            "assert payload['request_id'] == request_id",
            "assert payload['hosting_model'] == 'collector_vm_systemd'",
            "assert payload['azure_host']['source_ref'] == reviewed_commit",
            "assert len(payload['transactions']) == 20",
            "exact_root_cause_claimed'] is False",
            "workflow_conclusion != live_service_truth",
        ):
            self.assertIn(required, self.workflow)
        self.assertNotIn("gh run watch \"$run_id\" --exit-status", self.workflow)

    def test_served_frontend_requires_separate_diagnostics(self) -> None:
        for required in (
            "Request header identity mismatch · evidence rejected",
            "Request body identity mismatch · evidence rejected",
            "Collector identity mismatch · evidence rejected",
            "request and collector identity verified",
            "! grep -F 'Request or collector identity mismatch'",
            "browser_render_execution_not_claimed:true",
            "correlation-identity-run1-evidence",
        ):
            self.assertIn(required, self.workflow)

    def test_wrapper_contains_no_direct_azure_mutation(self) -> None:
        for forbidden in (
            "az deployment",
            "az vm",
            "az network",
            "systemctl",
            "nginx -t",
        ):
            self.assertNotIn(forbidden, self.workflow)


if __name__ == "__main__":
    unittest.main()
