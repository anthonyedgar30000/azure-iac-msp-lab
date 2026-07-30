from __future__ import annotations

import json
from pathlib import Path
import unittest

from azure_mcp_reality.lab_factory_tools import prepare_lab_request_payload
from lab_factory.catalog import load_catalog


ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "lab-factory-dual-subscription-planner-binding-20260729.json"
)
RUNBOOK = ROOT / "docs" / "runbooks" / "lab-factory-mcp-planner-binding.md"
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml"


class LabFactoryDualSubscriptionPlannerBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_catalog(repository_root=ROOT)
        cls.profile = cls.catalog["profiles"][0]
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.runbook = RUNBOOK.read_text(encoding="utf-8")

    def _parameters(self) -> dict[str, str]:
        return {
            "dnsLabel": "st-planner-binding-test",
            "allowedOrigin": "https://example.invalid",
            "backendTransactionUrl": "https://dependency.example.invalid/transaction",
            "adminSshPublicKey": "ssh-ed25519 AAAAC3NzaPlannerBindingOnly test",
            "sourceRepository": "https://github.com/anthonyedgar30000/azure-iac-msp-lab.git",
            "sourceRef": "0123456789abcdef0123456789abcdef01234567",
            "installerUri": (
                "https://raw.githubusercontent.com/anthonyedgar30000/"
                "azure-iac-msp-lab/0123456789abcdef0123456789abcdef01234567/"
                "workloads/servicetracer-demo-api/scripts/install.sh"
            ),
        }

    def test_catalog_binds_profile_to_ratified_planner(self) -> None:
        planner = self.profile["planner"]
        self.assertEqual(
            planner["workflow_path"],
            ".github/workflows/servicetracer-demo-api-subproject-plan.yml",
        )
        self.assertEqual(planner["trigger"], "workflow_dispatch")
        self.assertEqual(planner["github_environment"], "azure-api-payg")
        self.assertEqual(planner["subscription_boundary"], "dual_subscription")
        self.assertEqual(planner["dependency_subscription_access"], "read_only")
        self.assertEqual(planner["target_subscription_access"], "planning_only")
        self.assertEqual(planner["provider_validation_level"], "ProviderNoRbac")
        self.assertTrue(planner["arm_validation_required"])
        self.assertTrue(planner["arm_what_if_required"])
        self.assertFalse(planner["deployment_command_available"])
        self.assertEqual(
            planner["installer_path"],
            "workloads/servicetracer-demo-api/scripts/install.sh",
        )

    def test_mcp_output_is_bound_but_non_executing(self) -> None:
        parameters = self._parameters()
        result = prepare_lab_request_payload(
            profile_id="servicetracer-demo-api",
            environment="test",
            location="westus2",
            ttl_hours=8,
            request_id="lab-planner-binding-test",
            parameters=parameters,
            repository_root=ROOT,
        )
        self.assertEqual(result["next_gate"], "planner_dispatch_review_required")
        planner = result["planner"]
        self.assertTrue(planner["ready_for_dispatch_review"])
        self.assertFalse(planner["live_dispatch_authorized"])
        self.assertFalse(planner["parameter_values_returned"])
        self.assertFalse(planner["confirmation_value_returned"])
        self.assertFalse(result["execution"]["workflow_dispatch_performed"])
        self.assertFalse(result["execution"]["azure_queries_performed"])
        self.assertFalse(result["execution"]["azure_mutations_performed"])
        self.assertFalse(result["execution"]["deployment_authorized"])
        serialized = json.dumps(result, sort_keys=True)
        for value in parameters.values():
            self.assertNotIn(value, serialized)

    def test_workflow_preserves_dual_subscription_planning_boundary(self) -> None:
        for marker in (
            "environment: azure-api-payg",
            "AZURE_DEPENDENCY_CLIENT_ID",
            "AZURE_TARGET_CLIENT_ID",
            "AZURE_DEPENDENCY_SUBSCRIPTION_ID",
            "AZURE_TARGET_SUBSCRIPTION_ID",
            "ProviderNoRbac",
            "az deployment sub validate",
            "az deployment sub what-if",
            "workloads/servicetracer-demo-api/scripts/install.sh",
        ):
            self.assertIn(marker, self.workflow)
        self.assertNotIn("az deployment sub create", self.workflow)
        self.assertNotIn("az role assignment create", self.workflow)

    def test_reconciliation_and_runbook_keep_cloud_authority_closed(self) -> None:
        document = self.reconciliation
        self.assertEqual(
            document["schema_version"],
            "project.reconciliation.lab-factory-dual-subscription-planner-binding.v1",
        )
        self.assertEqual(
            document["repository"]["base_main"],
            "ced77a61d278f66f0f1be477164e5167b08fcc7b",
        )
        self.assertEqual(document["cost"]["currency"], "CAD")
        self.assertEqual(document["cost"]["repository_recurring_Azure_cost_delta"], 0)
        authority = document["authority"]
        self.assertTrue(authority["repository_changes"])
        self.assertTrue(authority["local_repository_only_MCP_smoke"])
        for denied in (
            "workflow_dispatch",
            "Azure_authentication_or_query",
            "ARM_validation_or_What_If",
            "Azure_mutation",
            "deployment",
            "RBAC_mutation",
            "model_call",
            "remote_MCP_deployment",
            "ChatGPT_connection",
            "rollback",
            "cleanup",
        ):
            self.assertFalse(authority[denied], denied)

        for marker in (
            "planner_dispatch_review_required",
            "dual-subscription",
            "azure-api-payg",
            "ProviderNoRbac",
            "live_dispatch_authorized: false",
            "planning ceiling != actual billed cost",
            "No Azure rollback or cleanup applies",
        ):
            self.assertIn(marker, self.runbook)


if __name__ == "__main__":
    unittest.main()
