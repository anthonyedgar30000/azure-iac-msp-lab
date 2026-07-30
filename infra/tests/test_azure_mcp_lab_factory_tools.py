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
        self.assertFalse(result["execution"]["azure_queries_performed"])
        self.assertFalse(result["execution"]["azure_mutations_performed"])
        self.assertFalse(result["execution"]["deployment_authorized"])
        self.assertFalse(result["execution"]["cleanup_authorized"])

    def test_prepare_tool_matches_direct_planner(self) -> None:
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
        self.assertEqual(tool_result, direct_result)
        self.assertEqual(tool_result["deployment"]["operation"], "prepare_only")
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
