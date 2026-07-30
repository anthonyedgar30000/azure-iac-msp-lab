from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LabFactoryReadOnlyPreflightRun1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.request = json.loads(
            (
                ROOT
                / ".project"
                / "deployment-requests"
                / "lab-factory-read-only-preflight-run1.json"
            ).read_text(encoding="utf-8")
        )
        cls.manual_workflow = (
            ROOT / ".github" / "workflows" / "lab-factory-read-only-preflight.yml"
        ).read_text(encoding="utf-8")
        cls.run1_workflow = (
            ROOT
            / ".github"
            / "workflows"
            / "lab-factory-read-only-preflight-run1.yml"
        ).read_text(encoding="utf-8")

    def test_manual_workflow_uses_deployable_parameter_contract(self) -> None:
        self.assertIn(
            "'backendTransactionUrl': 'https://example.invalid/transaction'",
            self.manual_workflow,
        )
        self.assertIn(
            "workloads/servicetracer-demo-api/scripts/install.sh",
            self.manual_workflow,
        )
        self.assertNotIn(
            "'backendTransactionUrl': 'https://example.invalid/api/demo/run'",
            self.manual_workflow,
        )
        self.assertNotIn(
            "workloads/servicetracer-demo-api/install.sh",
            self.manual_workflow,
        )
        self.assertTrue(
            (ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "install.sh").is_file()
        )

    def test_request_allows_one_read_only_attempt_only(self) -> None:
        self.assertEqual(self.request["status"], "active_one_attempt")
        self.assertEqual(self.request["attempt_limit"], 1)
        self.assertEqual(self.request["attempts_observed"], 0)
        authority = self.request["authority"]
        self.assertTrue(authority["one_merge_triggered_preflight"])
        self.assertTrue(authority["azure_authentication"])
        self.assertTrue(authority["azure_read_only_queries"])
        self.assertTrue(authority["arm_validation"])
        self.assertTrue(authority["one_terminal_issue_receipt"])
        for denied in (
            "provider_registration",
            "arm_what_if",
            "azure_mutation",
            "deployment",
            "rbac_mutation",
            "model_call",
            "automatic_retry",
            "manual_rerun",
            "rollback",
            "cleanup",
        ):
            self.assertFalse(authority[denied], denied)

    def test_run1_workflow_is_one_shot_and_exact_commit_bound(self) -> None:
        self.assertIn("name: Lab Factory read-only preflight run 1", self.run1_workflow)
        self.assertIn("push:", self.run1_workflow)
        self.assertIn("branches:\n      - main", self.run1_workflow)
        self.assertNotIn("workflow_dispatch:", self.run1_workflow)
        self.assertIn("id-token: write", self.run1_workflow)
        self.assertIn("issues: write", self.run1_workflow)
        self.assertIn("environment: azure-lab", self.run1_workflow)
        self.assertIn("test \"$GITHUB_RUN_ATTEMPT\" = '1'", self.run1_workflow)
        self.assertIn("ref: ${{ github.sha }}", self.run1_workflow)
        self.assertIn("--environment test", self.run1_workflow)
        self.assertIn("--ttl-hours 8", self.run1_workflow)
        self.assertIn("--cost-ceiling-cad 5.00", self.run1_workflow)
        self.assertIn("gh issue create", self.run1_workflow)

    def test_run1_workflow_contains_no_azure_mutation_path(self) -> None:
        for prohibited in (
            "az provider register",
            "az deployment sub create",
            "az deployment group create",
            "az deployment sub what-if",
            "az group create",
            "az role assignment create",
            "az group delete",
            "az resource delete",
        ):
            self.assertNotIn(prohibited, self.run1_workflow)
        self.assertIn("scripts/run_lab_factory_azure_preflight.py", self.run1_workflow)
        self.assertIn(".execution.azure_mutations_performed == false", self.run1_workflow)
        self.assertIn(".execution.arm_what_if_performed == false", self.run1_workflow)
        self.assertIn(".execution.deployment_authorized == false", self.run1_workflow)

    def test_terminal_issue_is_minimal_and_non_authorizing(self) -> None:
        allowed = self.request["terminal_issue_boundary"]["allowed_fields"]
        self.assertEqual(
            allowed,
            [
                "workflow run ID",
                "run attempt",
                "exact commit",
                "terminal status",
                "next gate",
                "artifact name",
            ],
        )
        self.assertFalse(
            self.request["terminal_issue_boundary"]["secrets_or_raw_Azure_identifiers"]
        )
        self.assertFalse(self.request["terminal_issue_boundary"]["issue_merge_authority"])


if __name__ == "__main__":
    unittest.main()
