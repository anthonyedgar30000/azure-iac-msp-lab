from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from lab_factory.catalog import CatalogError, load_catalog, prepare_lab_plan
from lab_factory.planning_binding import (
    enrich_plan_with_planning,
    profile_planning_summary,
)


ROOT = Path(__file__).resolve().parents[2]
PROFILE_ID = "servicetracer-demo-api"
PROFILE_VERSION = "1.0.0"
WORKFLOW = ROOT / ".github/workflows/servicetracer-demo-api-subproject-plan.yml"
PARAMETERS = {
    "dnsLabel": "st-binding-test-001",
    "allowedOrigin": "https://example.invalid",
    "backendTransactionUrl": "https://backend.example.invalid/transaction",
    "adminSshPublicKey": "ssh-ed25519 AAAAC3NzaBindingOnly binding-test",
    "sourceRepository": "https://github.com/example/repository.git",
    "sourceRef": "0123456789abcdef0123456789abcdef01234567",
    "installerUri": (
        "https://raw.githubusercontent.com/example/repository/"
        "0123456789abcdef0123456789abcdef01234567/"
        "workloads/servicetracer-demo-api/scripts/install.sh"
    ),
}


class LabFactoryRatifiedPlannerBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_catalog(repository_root=ROOT)

    def _base_plan(self):
        return prepare_lab_plan(
            self.catalog,
            profile_id=PROFILE_ID,
            version=PROFILE_VERSION,
            environment="dev",
            location="westus2",
            ttl_hours=8,
            parameters=PARAMETERS,
            request_id="lab-binding-001",
            repository_root=ROOT,
        )

    def test_catalog_binds_profile_to_existing_dual_subscription_planner(self):
        self.assertEqual(self.catalog["catalog_version"], "1.1.0")
        summary = profile_planning_summary(
            self.catalog,
            profile_id=PROFILE_ID,
            profile_version=PROFILE_VERSION,
            repository_root=ROOT,
        )
        self.assertTrue(WORKFLOW.is_file())
        self.assertEqual(
            summary["workflow_path"],
            ".github/workflows/servicetracer-demo-api-subproject-plan.yml",
        )
        self.assertEqual(summary["github_environment"], "azure-api-payg")
        self.assertEqual(summary["dispatch_mode"], "manual_only")
        self.assertEqual(summary["subscription_boundary"], "dual_subscription")
        self.assertEqual(summary["provider_validation_level"], "ProviderNoRbac")
        self.assertTrue(summary["includes_arm_validation"])
        self.assertTrue(summary["includes_arm_what_if"])
        self.assertFalse(summary["deployment_command_present"])

    def test_workflow_preserves_dependency_target_and_no_deploy_boundary(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
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
            self.assertIn(marker, workflow)
        self.assertNotIn("az deployment sub create", workflow)

    def test_enriched_plan_is_deterministic_and_contains_no_parameter_values(self):
        first = enrich_plan_with_planning(
            self.catalog,
            self._base_plan(),
            repository_root=ROOT,
        )
        second = enrich_plan_with_planning(
            self.catalog,
            self._base_plan(),
            repository_root=ROOT,
        )
        self.assertEqual(first, second)
        self.assertEqual(first["next_gate"], "preflight_required")
        self.assertEqual(
            first["planning"]["derived_non_secret_inputs"]["dependency_resource_group"],
            "rg-servicetracer-dev-westus2",
        )
        self.assertEqual(
            first["planning"]["confirmation_pattern"],
            "PLAN-DEMO-API-SUBPROJECT:dev:<dns-label>",
        )
        self.assertFalse(first["planning"]["workflow_dispatch_performed"])
        self.assertFalse(first["planning"]["dispatch_authorized"])
        self.assertFalse(first["execution"]["azure_queries_performed"])
        self.assertFalse(first["execution"]["deployment_authorized"])
        serialized = json.dumps(first, sort_keys=True)
        for value in PARAMETERS.values():
            self.assertNotIn(value, serialized)

    def test_wrong_github_environment_is_rejected(self):
        changed = deepcopy(self.catalog)
        changed["profiles"][0]["planning"]["github_environment"] = "azure-lab"
        with self.assertRaisesRegex(CatalogError, "azure-api-payg"):
            profile_planning_summary(
                changed,
                profile_id=PROFILE_ID,
                profile_version=PROFILE_VERSION,
                repository_root=ROOT,
            )

    def test_deployment_capability_is_rejected(self):
        changed = deepcopy(self.catalog)
        changed["profiles"][0]["planning"]["deployment_command_present"] = True
        with self.assertRaisesRegex(CatalogError, "deployment command"):
            profile_planning_summary(
                changed,
                profile_id=PROFILE_ID,
                profile_version=PROFILE_VERSION,
                repository_root=ROOT,
            )


if __name__ == "__main__":
    unittest.main()
