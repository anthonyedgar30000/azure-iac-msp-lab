from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
REQUEST_PATH = (
    ROOT
    / ".project"
    / "observation-requests"
    / "servicetracer-lab-factory-preflight-run1.json"
)
SCRIPT_PATH = ROOT / "scripts" / "azure_lab_factory_servicetracer_preflight_run1.sh"
RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "servicetracer-lab-factory-preflight-run1.md"
CATALOG_PATH = ROOT / "lab_factory" / "catalog.json"
TEMPLATE_PATH = ROOT / "workloads" / "servicetracer-demo-api" / "infra" / "main.bicep"
MODULE_PATH = ROOT / "workloads" / "servicetracer-demo-api" / "infra" / "modules" / "workload.bicep"

UUID = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


class ServiceTracerLabFactoryPreflightRun1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.script = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")
        cls.module = MODULE_PATH.read_text(encoding="utf-8")

    def test_authorization_is_exact_one_attempt_and_read_only(self) -> None:
        self.assertEqual(
            self.request["schema_version"],
            "project.azure-lab-factory-preflight-authorization.v1",
        )
        self.assertTrue(self.request["active"])
        self.assertEqual(self.request["consumption"]["attempt_limit"], 1)
        self.assertFalse(self.request["consumption"]["retry_authorized"])
        authority = self.request["authority"]
        self.assertTrue(authority["azure_authentication_and_bounded_queries"])
        self.assertTrue(authority["arm_validation"])
        self.assertTrue(authority["arm_what_if"])
        for key in (
            "azure_mutation",
            "deployment",
            "rbac_mutation",
            "model_call",
            "remote_mcp_deployment",
            "chatgpt_connection",
            "cleanup",
            "rollback",
            "retry",
        ):
            self.assertFalse(authority[key], key)

    def test_prepared_request_matches_catalog_and_template(self) -> None:
        profile = self.catalog["profiles"][0]
        prepared = self.request["prepared_request"]
        self.assertEqual(prepared["profile"], f"{profile['id']}@{profile['version']}")
        self.assertEqual(prepared["profile_release_state"], "candidate")
        self.assertEqual(prepared["environment"], "dev")
        self.assertEqual(prepared["location"], profile["default_location"])
        self.assertEqual(prepared["ttl_hours"], profile["ttl"]["default_hours"])
        self.assertEqual(
            prepared["resource_group"],
            profile["resource_group_pattern"].format(
                environment="dev", location=profile["default_location"]
            ),
        )
        self.assertEqual(prepared["template"], profile["template"]["path"])
        self.assertEqual(prepared["vm_size"], profile["parameters"]["defaults"]["vmSize"])
        self.assertEqual(prepared["cost_ceiling_cad"], 5.0)
        self.assertIn("targetScope = 'subscription'", self.template)

    def test_script_fixes_scope_and_consumes_before_azure_observation(self) -> None:
        for expected in (
            'readonly profile_id="servicetracer-demo-api"',
            'readonly profile_version="1.0.0"',
            'readonly environment_name="dev"',
            'readonly location_name="westus2"',
            'readonly ttl_hours="8"',
            'readonly target_resource_group="rg-st-demo-api-dev-westus2"',
            'readonly vm_size="Standard_F1als_v7"',
            'readonly cost_ceiling_cad="5.00"',
        ):
            self.assertIn(expected, self.script)
        marker = self.script.index("set -o noclobber")
        first_account_action = self.script.index("az account set --subscription")
        self.assertLess(marker, first_account_action)
        self.assertIn("git status --porcelain=v1", self.script)
        self.assertIn("repository working tree must be clean", self.script)

    def test_script_contains_required_read_only_checks(self) -> None:
        for command in (
            "az provider show",
            "az vm list-skus",
            "az vm list-usage",
            "az group show",
            "az resource list",
            "https://prices.azure.com/api/retail/prices",
            "Microsoft.CostManagement/query?api-version=2025-03-01",
            "az bicep build",
            "az deployment sub validate",
            "az deployment sub what-if",
            "--result-format ResourceIdOnly",
        ):
            self.assertIn(command, self.script)
        self.assertIn('"what_if_safe":safe', self.script)
        self.assertIn('"outside_authorized_scope_count":len(outside_scope)', self.script)
        self.assertIn('"unexpected_resource_types":sorted(set(unexpected_types))', self.script)

    def test_script_has_no_azure_mutation_or_secret_command(self) -> None:
        forbidden = (
            "az deployment sub create",
            "az deployment group create",
            "az group create",
            "az group delete",
            "az resource create",
            "az resource update",
            "az resource delete",
            "az vm create",
            "az vm delete",
            "az provider register",
            "az role assignment create",
            "az role assignment delete",
            "az network public-ip create",
            "az network vnet create",
            "az cognitiveservices account keys",
            "az keyvault secret show",
            "az vm run-command",
            "azd up",
            "azd provision",
            "azd deploy",
            "azd down",
        )
        for value in forbidden:
            self.assertNotIn(value, self.script, value)
        self.assertIn('azure_mutations_performed":False', self.script)
        self.assertIn('deployment_authorized":False', self.script)
        self.assertIn('secrets_returned":False', self.script)

    def test_private_material_is_ephemeral_and_evidence_is_sanitized(self) -> None:
        self.assertIn("ssh-keygen -q -t ed25519", self.script)
        self.assertIn('rm -rf "$temp_dir"', self.script)
        self.assertIn("parameter_values_persisted:false", self.script)
        self.assertIn("raw_identifiers_persisted:false", self.script)
        self.assertIn("subscription_fingerprint", self.script)
        self.assertIn("tenant_fingerprint", self.script)
        self.assertIsNone(UUID.search(json.dumps(self.request)))
        self.assertIsNone(UUID.search(self.runbook))

    def test_network_source_boundary_is_explicit(self) -> None:
        self.assertIn("destinationPortRange: '80'", self.module)
        self.assertIn("destinationPortRange: '443'", self.module)
        self.assertNotIn("destinationPortRange: '22'", self.module)
        self.assertIn("'10.30.0.0/24'", self.module)
        self.assertIn("'10.30.0.0/27'", self.module)
        self.assertIn("publicIPAllocationMethod: 'Static'", self.module)
        self.assertIn("type: 'SystemAssigned'", self.module)
        self.assertIn("No inbound SSH rule is declared", self.runbook)

    def test_cost_boundary_is_planning_only(self) -> None:
        cost = self.request["cost"]
        self.assertEqual(cost["expected_recurring_Azure_resource_cost_delta_CAD"], 0)
        self.assertEqual(cost["planning_ceiling_CAD"], 5.0)
        self.assertFalse(cost["actual_cost_freshly_observed"])
        self.assertTrue(cost["estimated_cost_is_not_actual_cost"])
        self.assertIn("estimated_cost != actual_cost", self.request["canonical_distinctions"])
        self.assertIn("estimate_complete\":False", self.script)


if __name__ == "__main__":
    unittest.main()
