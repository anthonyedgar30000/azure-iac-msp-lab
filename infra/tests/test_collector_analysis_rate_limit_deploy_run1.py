from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "collector-analysis-rate-limit-deploy-run1.yml"
)
REQUEST = (
    ROOT
    / ".project"
    / "deployment-requests"
    / "collector-analysis-rate-limit-run1.json"
)


class CollectorAnalysisRateLimitDeployRun1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.request = json.loads(REQUEST.read_text(encoding="utf-8"))

    def test_trigger_is_opened_pull_request_for_exact_nonmerge_trigger(self) -> None:
        for required in (
            "pull_request:",
            "types: [opened]",
            ".project/triggers/collector-analysis-rate-limit-deploy-run1.json",
            "github.event.action == 'opened'",
            "github.base_ref == 'main'",
            "github.head_ref == 'trigger/collector-analysis-rate-limit-deploy-run1'",
            ".merge_authorized == false",
            ".retry_authorized == false",
        ):
            self.assertIn(required, self.workflow)
        self.assertNotIn("push:\n", self.workflow)
        self.assertNotIn("workflow_dispatch:\n", self.workflow)

    def test_request_binds_exact_ci_tested_repair(self) -> None:
        self.assertEqual(
            self.request["source"]["exact_head"],
            "015dd7bb0fbf72dbbe5af9c6c861cab62edd0514",
        )
        self.assertEqual(
            self.request["source"]["merge_commit"],
            "ea34e8cb98ce703552cbccedb4c44d41d6185e86",
        )
        self.assertEqual(self.request["source"]["ci_run_id"], 30307023191)
        self.assertEqual(self.request["source"]["ci_conclusion"], "success")
        self.assertEqual(
            self.request["execution"]["reviewed_commit"],
            self.request["source"]["merge_commit"],
        )

    def test_authority_is_finite_and_nonrenewing(self) -> None:
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

    def test_dispatch_uses_existing_governed_workflow_and_exact_inputs(self) -> None:
        for required in (
            "gh workflow run collector-demo-api.yml",
            "--ref main",
            "-f operation=deploy",
            "-f reviewed_commit=\"$REVIEWED_COMMIT\"",
            "COLLECTOR-DEMO-API:deploy:rg-servicetracer-dev-westus2:st-demo-api-aeg30000",
            "The one-shot grant is now **consumed**",
            "No second dispatch will be issued",
            "No retry or rollback was performed",
        ):
            self.assertIn(required, self.workflow)

    def test_live_verification_separates_health_from_analysis(self) -> None:
        for required in (
            "for attempt in $(seq 1 12)",
            "Access-Control-Request-Headers: Content-Type, X-ServiceTracer-Request-ID",
            "X-ServiceTracer-Request-ID: $request_id",
            "assert payload['request_id'] == request_id",
            "assert len(payload['transactions']) == 20",
            "assert identity['source_ref'] == reviewed_commit",
            "Collector health and Azure identity verified",
            "Controlled demo fixture — live analysis unavailable",
            "browser_render_execution_not_claimed:true",
            "collector-analysis-rate-limit-run1-evidence",
        ):
            self.assertIn(required, self.workflow)

    def test_no_direct_azure_mutation_or_retry_commands(self) -> None:
        for forbidden in (
            "az deployment",
            "az vm",
            "az network",
            "gh run rerun",
            "rerun-failed-jobs",
            "systemctl",
            "nginx -t",
        ):
            self.assertNotIn(forbidden, self.workflow)


if __name__ == "__main__":
    unittest.main()
