from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION = (
    ROOT
    / ".project/reconciliations/lab-factory-preflight-boundary-correction-20260729.json"
)
ACTIVE_WORKFLOW = (
    ROOT / ".github/workflows/servicetracer-demo-api-subproject-plan.yml"
)
SUPERSEDED_PATHS = (
    ROOT / ".github/workflows/lab-factory-read-only-preflight.yml",
    ROOT / ".project/contracts/lab-factory-read-only-preflight-v1.json",
    ROOT / "docs/runbooks/lab-factory-read-only-preflight.md",
    ROOT / "infra/tests/test_lab_factory_azure_preflight.py",
    ROOT / "lab_factory/azure_preflight.py",
    ROOT / "scripts/run_lab_factory_azure_preflight.py",
)


class LabFactoryPreflightBoundaryCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reconciliation = json.loads(
            RECONCILIATION.read_text(encoding="utf-8")
        )
        cls.workflow = ACTIVE_WORKFLOW.read_text(encoding="utf-8")

    def test_duplicate_preflight_path_is_absent(self) -> None:
        for path in SUPERSEDED_PATHS:
            self.assertFalse(path.exists(), str(path))

    def test_existing_single_subscription_planner_is_canonical(self) -> None:
        self.assertTrue(ACTIVE_WORKFLOW.is_file())
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("AZURE_CLIENT_ID", self.workflow)
        self.assertIn("AZURE_SUBSCRIPTION_ID", self.workflow)
        self.assertIn("AZURE_TENANT_ID", self.workflow)
        self.assertIn('subscription_boundary:"single_subscription"', self.workflow)
        self.assertNotIn("AZURE_DEPENDENCY_CLIENT_ID", self.workflow)
        self.assertNotIn("AZURE_TARGET_CLIENT_ID", self.workflow)
        self.assertNotIn("AZURE_DEPENDENCY_SUBSCRIPTION_ID", self.workflow)
        self.assertNotIn("AZURE_TARGET_SUBSCRIPTION_ID", self.workflow)
        self.assertIn("ProviderNoRbac", self.workflow)
        self.assertIn(
            "workloads/servicetracer-demo-api/scripts/install.sh",
            self.workflow,
        )
        self.assertIn("az deployment sub validate", self.workflow)
        self.assertIn("az deployment sub what-if", self.workflow)
        self.assertNotIn("az deployment sub create", self.workflow)

    def test_historical_reconciliation_preserves_closed_cloud_authority(self) -> None:
        document = self.reconciliation
        self.assertEqual(
            document["schema_version"],
            "project.reconciliation.lab-factory-preflight-boundary-correction.v1",
        )
        self.assertEqual(
            document["repository"]["base_main"],
            "2b8477109052278d01c93fc8041cdb6b0ad12389",
        )
        self.assertFalse(document["finding"]["live_workflow_dispatch_observed"])
        authority = document["authority"]
        self.assertTrue(authority["repository_correction"])
        for denied in (
            "workflow_dispatch",
            "Azure_authentication_or_query",
            "ARM_What_If",
            "Azure_mutation",
            "deployment",
            "RBAC_mutation",
            "cleanup",
            "rollback",
            "model_call",
            "remote_MCP_deployment",
            "ChatGPT_connection",
        ):
            self.assertFalse(authority[denied], denied)


if __name__ == "__main__":
    unittest.main()
