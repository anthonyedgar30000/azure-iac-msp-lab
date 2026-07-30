from __future__ import annotations

import json
from pathlib import Path
import unittest

from azure_mcp_reality.lab_factory_tools import (
    CatalogError,
    list_lab_profiles_payload,
    prepare_lab_request_payload,
)
from lab_factory.catalog import load_catalog, prepare_lab_plan


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_WORKFLOW = ".github/workflows/servicetracer-demo-api-subproject-plan.yml"


class AzureMcpLabFactoryToolsTests(unittest.TestCase):
    def _complete_parameters(self) -> dict[str, str]:
        return {
            "dnsLabel": "st-demo-api-mcp-123",
            "allowedOrigin": "https://example.invalid",
            "backendTransactionUrl": "https://backend.example.invalid/api/demo/run",
            "adminSshPublicKey": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestOnlyKey mcp-test",
            "sourceRepository": "https://github.com/anthonyedgar30000/azure-iac-msp-lab.git",
            "sourceRef": "0123456789abcdef0123456789abcdef01234567",
            "installerUri": (
                "https://raw.githubusercontent.com/anthonyedgar30000/"
                "azure-iac-msp-lab/0123456789abcdef0123456789abcdef01234567/"
                "workloads/servicetracer-demo-api/scripts/install.sh"
            ),
        }

    def test_profile_list_matches_catalog_and_is_cloud_free(self) -> None:
        result = list_lab_profiles_payload(repository_root=REPOSITORY_ROOT)
        self.assertEqual(result["schema_version"], "lab-factory.profile-list.v1")
        self.assertEqual([item["id"] for item in result["profiles"]], ["servicetracer-demo-api"])
        profile = result["profiles"][0]
        planning = profile["planning"]
        self.assertEqual(planning["workflow_path"], EXPECTED_WORKFLOW)
        self.assertEqual(planning["github_environment"], "azure-lab")
        self.assertEqual(planning["dispatch_mode"], "manual_only")
        self.assertEqual(planning["subscription_boundary"], "single_subscription")
        self.assertEqual(planning["provider_validation_level"], "ProviderNoRbac")
        self.assertTrue(planning["includes_arm_validation"])
        self.assertTrue(planning["includes_arm_what_if"])
        self.assertFalse(planning["deployment_command_present"])
        self.assertFalse(result["execution"]["azure_queries_performed"])
        self.assertFalse(result["execution"]["azure_mutations_performed"])
        self.assertFalse(result["execution"]["workflow_dispatch_performed"])
        self.assertFalse(result["execution"]["deployment_authorized"])
        self.assertFalse(result["execution"]["cleanup_authorized"])

    def test_prepare_tool_preserves_direct_planner_and_adds_binding(self) -> None:
        parameters = self._complete_parameters()
        tool_result = prepare_lab_request_payload(
            profile_id="servicetracer-demo-api",
            environment="test",
            location="westus2",
            ttl_hours=6,
            request_id="lab-mcp-001",
            parameters=parameters,
            repository_root=REPOSITORY_ROOT,
        )
        direct_result = prepare_lab_plan(
            load_catalog(repository_root=REPOSITORY_ROOT),
            profile_id="servicetracer-demo-api",
            environment="test",
            location="westus2",
            ttl_hours=6,
            request_id="lab-mcp-001",
            parameters=parameters,
            repository_root=REPOSITORY_ROOT,
        )

        self.assertEqual(tool_result["base_plan_digest"], direct_result["plan_digest"])
        for key in (
            "schema_version",
            "request",
            "resolved_profile",
            "deployment",
            "gates",
            "execution",
            "next_gate",
            "claim_boundaries",
        ):
            self.assertEqual(tool_result[key], direct_result[key], key)

        self.assertEqual(tool_result["deployment"]["operation"], "prepare_only")
        planning = tool_result["planning"]
        self.assertEqual(planning["workflow_path"], EXPECTED_WORKFLOW)
        self.assertEqual(planning["github_environment"], "azure-lab")
        self.assertEqual(planning["dispatch_mode"], "manual_only")
        self.assertFalse(planning["workflow_dispatch_performed"])
        self.assertEqual(planning["subscription_boundary"], "single_subscription")
        self.assertEqual(
            planning["dependency_subscription_role"],
            "azure_for_students_existing_dependency",
        )
        self.assertEqual(
            planning["target_subscription_role"],
            "azure_for_students_planning_target",
        )
        self.assertEqual(planning["provider_validation_level"], "ProviderNoRbac")
        self.assertTrue(planning["includes_arm_validation"])
        self.assertTrue(planning["includes_arm_what_if"])
        self.assertFalse(planning["deployment_command_present"])
        self.assertEqual(
            planning["derived_non_secret_inputs"],
            {
                "environment": "test",
                "location": "westus2",
                "prefix": "mst",
                "dependency_resource_group": "rg-servicetracer-test-westus2",
                "vm_size": "Standard_F1als_v7",
            },
        )
        self.assertEqual(
            planning["required_human_input_names"],
            ["dns_label", "allowed_origin", "maximum_monthly_cost_cad"],
        )
        self.assertEqual(
            planning["confirmation_pattern"],
            "PLAN-DEMO-API-SUBPROJECT:test:<dns-label>",
        )
        self.assertFalse(planning["live_subscription_state_observed"])
        self.assertFalse(planning["dispatch_authorized"])
        self.assertFalse(tool_result["execution"]["azure_queries_performed"])
        self.assertFalse(tool_result["execution"]["azure_mutations_performed"])
        self.assertFalse(tool_result["execution"]["deployment_authorized"])

    def test_prepare_tool_does_not_echo_parameter_values(self) -> None:
        parameters = self._complete_parameters()
        result = prepare_lab_request_payload(
            profile_id="servicetracer-demo-api",
            parameters=parameters,
            request_id="lab-mcp-002",
            repository_root=REPOSITORY_ROOT,
        )
        serialized = json.dumps(result, sort_keys=True)
        for value in parameters.values():
            self.assertNotIn(value, serialized)

    def test_identical_request_produces_identical_digest(self) -> None:
        parameters = self._complete_parameters()
        kwargs = {
            "profile_id": "servicetracer-demo-api",
            "parameters": parameters,
            "request_id": "lab-mcp-003",
            "repository_root": REPOSITORY_ROOT,
        }
        first = prepare_lab_request_payload(**kwargs)
        second = prepare_lab_request_payload(**kwargs)
        self.assertEqual(first["plan_digest"], second["plan_digest"])
        self.assertEqual(first, second)

    def test_unknown_profile_is_rejected(self) -> None:
        with self.assertRaisesRegex(CatalogError, "unknown profile"):
            prepare_lab_request_payload(
                profile_id="unknown-profile",
                repository_root=REPOSITORY_ROOT,
            )

    def test_ttl_above_profile_ceiling_is_rejected(self) -> None:
        with self.assertRaisesRegex(CatalogError, "ttl_hours is outside"):
            prepare_lab_request_payload(
                profile_id="servicetracer-demo-api",
                ttl_hours=25,
                repository_root=REPOSITORY_ROOT,
            )

    def test_location_outside_profile_allowlist_is_rejected(self) -> None:
        with self.assertRaisesRegex(CatalogError, "location is not allowed"):
            prepare_lab_request_payload(
                profile_id="servicetracer-demo-api",
                location="eastus",
                repository_root=REPOSITORY_ROOT,
            )


if __name__ == "__main__":
    unittest.main()
