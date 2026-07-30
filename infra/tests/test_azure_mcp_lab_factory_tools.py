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


class AzureMcpLabFactoryToolsTests(unittest.TestCase):
    def _complete_parameters(self) -> dict[str, str]:
        return {
            "dnsLabel": "st-demo-api-mcp-123",
            "allowedOrigin": "https://example.invalid",
            "backendTransactionUrl": "https://backend.example.invalid/transaction",
            "adminSshPublicKey": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestOnlyKey mcp-test",
            "sourceRepository": "https://github.com/anthonyedgar30000/azure-iac-msp-lab.git",
            "sourceRef": "0123456789abcdef0123456789abcdef01234567",
            "installerUri": (
                "https://raw.githubusercontent.com/anthonyedgar30000/"
                "azure-iac-msp-lab/0123456789abcdef0123456789abcdef01234567/"
                "workloads/servicetracer-demo-api/scripts/install.sh"
            ),
        }

    def test_profile_list_includes_canonical_planner_and_is_cloud_free(self) -> None:
        result = list_lab_profiles_payload(repository_root=REPOSITORY_ROOT)
        self.assertEqual(result["schema_version"], "lab-factory.profile-list.v2")
        self.assertEqual(
            [item["id"] for item in result["profiles"]],
            ["servicetracer-demo-api"],
        )
        planner = result["profiles"][0]["planner"]
        self.assertEqual(
            planner["workflow_path"],
            ".github/workflows/servicetracer-demo-api-subproject-plan.yml",
        )
        self.assertRegex(planner["workflow_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(planner["trigger"], "workflow_dispatch")
        self.assertEqual(planner["github_environment"], "azure-api-payg")
        self.assertEqual(planner["subscription_boundary"], "dual_subscription")
        self.assertEqual(planner["provider_validation_level"], "ProviderNoRbac")
        self.assertFalse(planner["deployment_command_available"])
        self.assertFalse(planner["live_dispatch_authorized"])
        self.assertFalse(result["execution"]["azure_queries_performed"])
        self.assertFalse(result["execution"]["azure_mutations_performed"])
        self.assertFalse(result["execution"]["workflow_dispatch_performed"])
        self.assertFalse(result["execution"]["deployment_authorized"])
        self.assertFalse(result["execution"]["cleanup_authorized"])

    def test_prepare_tool_preserves_generic_plan_and_adds_binding(self) -> None:
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

        self.assertEqual(tool_result["request"], direct_result["request"])
        self.assertEqual(tool_result["deployment"], direct_result["deployment"])
        self.assertEqual(tool_result["gates"], direct_result["gates"])
        self.assertEqual(tool_result["deployment"]["operation"], "prepare_only")
        self.assertEqual(direct_result["next_gate"], "preflight_required")
        self.assertEqual(
            tool_result["next_gate"],
            "planner_dispatch_review_required",
        )

        planner = tool_result["planner"]
        self.assertEqual(planner["operation"], "prepare_only")
        self.assertEqual(
            planner["workflow_path"],
            ".github/workflows/servicetracer-demo-api-subproject-plan.yml",
        )
        self.assertEqual(planner["github_environment"], "azure-api-payg")
        self.assertEqual(planner["subscription_boundary"], "dual_subscription")
        self.assertEqual(planner["dependency_subscription_access"], "read_only")
        self.assertEqual(planner["target_subscription_access"], "planning_only")
        self.assertEqual(planner["provider_validation_level"], "ProviderNoRbac")
        self.assertTrue(planner["arm_validation_required"])
        self.assertTrue(planner["arm_what_if_required"])
        self.assertFalse(planner["deployment_command_available"])
        self.assertTrue(planner["ready_for_dispatch_review"])
        self.assertFalse(planner["live_dispatch_authorized"])
        self.assertFalse(planner["parameter_values_returned"])
        self.assertFalse(planner["confirmation_value_returned"])
        self.assertEqual(planner["missing_input_names"], [])
        self.assertRegex(planner["workflow_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(planner["installer_sha256"], r"^sha256:[0-9a-f]{64}$")

        derived = planner["derived_template_parameters"]
        self.assertEqual(
            derived["backendTransactionUrl"],
            "dependency_subscription_public_ip_observation",
        )
        self.assertEqual(derived["sourceRef"], "github.sha")
        self.assertEqual(
            derived["installerUri"],
            "github.repository_and_sha_plus_installer_path",
        )

        self.assertFalse(tool_result["execution"]["azure_queries_performed"])
        self.assertFalse(tool_result["execution"]["azure_mutations_performed"])
        self.assertFalse(tool_result["execution"]["workflow_dispatch_performed"])
        self.assertFalse(tool_result["execution"]["deployment_authorized"])

    def test_incomplete_mcp_request_stops_before_dispatch_review(self) -> None:
        result = prepare_lab_request_payload(
            profile_id="servicetracer-demo-api",
            repository_root=REPOSITORY_ROOT,
        )
        self.assertEqual(result["next_gate"], "parameters_required")
        self.assertFalse(result["planner"]["ready_for_dispatch_review"])
        self.assertFalse(result["planner"]["live_dispatch_authorized"])
        self.assertEqual(
            result["planner"]["missing_input_names"],
            ["allowed_origin", "confirmation", "dns_label"],
        )

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

    def test_planner_binding_matches_ratified_workflow(self) -> None:
        result = prepare_lab_request_payload(
            profile_id="servicetracer-demo-api",
            environment="test",
            parameters=self._complete_parameters(),
            request_id="lab-mcp-workflow-check",
            repository_root=REPOSITORY_ROOT,
        )
        workflow = (
            REPOSITORY_ROOT / result["planner"]["workflow_path"]
        ).read_text(encoding="utf-8")
        self.assertIn("environment: azure-api-payg", workflow)
        self.assertIn("AZURE_DEPENDENCY_CLIENT_ID", workflow)
        self.assertIn("AZURE_TARGET_CLIENT_ID", workflow)
        self.assertIn("AZURE_DEPENDENCY_SUBSCRIPTION_ID", workflow)
        self.assertIn("AZURE_TARGET_SUBSCRIPTION_ID", workflow)
        self.assertIn("ProviderNoRbac", workflow)
        self.assertIn(
            "workloads/servicetracer-demo-api/scripts/install.sh",
            workflow,
        )
        self.assertIn("az deployment sub validate", workflow)
        self.assertIn("az deployment sub what-if", workflow)
        self.assertNotIn("az deployment sub create", workflow)

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
