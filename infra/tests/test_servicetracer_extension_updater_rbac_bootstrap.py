from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BICEP = ROOT / "infra/rbac/servicetracer-demo-api-extension-updater-rbac.bicep"
ASSIGNMENT_MODULE = ROOT / "infra/rbac/modules/servicetracer-demo-api-extension-role-assignment.bicep"
BOOTSTRAP = ROOT / "scripts/bootstrap_servicetracer_extension_updater_rbac.sh"
ASSERTION = ROOT / "scripts/assert_servicetracer_extension_updater_rbac_what_if.py"
AUTH = ROOT / ".project/authorizations/servicetracer-demo-api-extension-updater-rbac-bootstrap-20260725.json"
RECONCILIATION = ROOT / ".project/reconciliations/servicetracer-demo-api-extension-updater-rbac-bootstrap.json"

ROLE_GUID = "a94875a8-373d-531e-bfe0-b213fd936082"
ACTION = "Microsoft.Compute/virtualMachines/extensions/write"


class ExtensionUpdaterRbacBootstrapTests(unittest.TestCase):
    def test_role_is_exact_and_non_wildcard(self) -> None:
        source = BICEP.read_text(encoding="utf-8")
        self.assertIn(ACTION, source)
        self.assertIn(ROLE_GUID, source)
        self.assertNotIn("Microsoft.Compute/*", source)
        self.assertNotIn("Microsoft.Compute/virtualMachines/*", source)
        self.assertNotIn("Microsoft.Authorization/roleAssignments/write", source)
        self.assertNotIn("Microsoft.Network/", source)
        self.assertRegex(source, r"assignableScopes:\s*\[\s*targetResourceGroup\.id\s*\]")

    def test_cross_scope_resources_are_composed_through_module(self) -> None:
        main_source = BICEP.read_text(encoding="utf-8")
        module_source = ASSIGNMENT_MODULE.read_text(encoding="utf-8")
        self.assertIn("targetScope = 'subscription'", main_source)
        self.assertIn("targetScope = 'resourceGroup'", module_source)
        self.assertIn("./modules/servicetracer-demo-api-extension-role-assignment.bicep", main_source)
        self.assertRegex(main_source, r"module\s+extensionUpdaterAssignment[\s\S]+scope:\s*targetResourceGroup")
        self.assertRegex(module_source, r"scope:\s*targetExtension")
        self.assertNotIn("scope: targetExtension", main_source)

    def test_bootstrap_is_what_if_gated_and_does_not_deploy_workload(self) -> None:
        source = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("az deployment sub what-if", source)
        self.assertIn("assert_servicetracer_extension_updater_rbac_what_if.py", source)
        self.assertIn('MODE" == "--plan"', source)
        self.assertNotIn("az vm extension set", source)
        self.assertNotIn("az vm run-command", source)
        self.assertNotIn("az deployment group create", source)
        self.assertNotIn("/api/demo/run", source)
        self.assertNotIn("az group delete", source)
        self.assertNotIn("az role assignment delete", source)

    def test_scoped_role_assignment_queries_do_not_use_all(self) -> None:
        source = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('--scope "$rg_id"', source)
        self.assertIn('--scope "$extension_id"', source)
        self.assertIn("--include-inherited", source)
        self.assertNotIn("--all", source)

    def test_principal_resolution_is_unique_and_existing(self) -> None:
        source = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("ServiceTracer Demo API What-If Planner v1", source)
        self.assertIn('principalType == "ServicePrincipal"', source)
        self.assertIn('"${#principal_ids[@]}" -eq 1', source)
        self.assertIn("--include-inherited", source)

    def test_what_if_assertion_allows_only_two_rbac_types(self) -> None:
        source = ASSERTION.read_text(encoding="utf-8")
        self.assertIn('"Microsoft.Authorization/roleDefinitions"', source)
        self.assertIn('"Microsoft.Authorization/roleAssignments"', source)
        self.assertIn("expected at most two mutating RBAC resources", source)
        self.assertIn("prohibited change type", source)
        self.assertIn("role assignment escaped extension scope", source)

    def test_what_if_assertion_accepts_full_resource_payload_shape(self) -> None:
        subscription = "/subscriptions/00000000-0000-0000-0000-000000000000"
        extension_scope = (
            f"{subscription}/resourceGroups/rg-st-demo-api-dev-westus2"
            "/providers/Microsoft.Compute/virtualMachines/vm-st-demo-api-mst-dev"
            "/extensions/servicetracer-demo-api"
        )
        role_definition_id = (
            f"{subscription}/providers/Microsoft.Authorization/roleDefinitions/{ROLE_GUID}"
        )
        role_assignment_id = (
            f"{extension_scope}/providers/Microsoft.Authorization/roleAssignments/"
            "11111111-1111-1111-1111-111111111111"
        )
        payload = {
            "status": "Succeeded",
            "changes": [
                {
                    "resourceId": role_definition_id,
                    "changeType": "Create",
                    "after": {"type": "Microsoft.Authorization/roleDefinitions"},
                },
                {
                    "resourceId": role_assignment_id,
                    "changeType": "Create",
                    "after": {"type": "Microsoft.Authorization/roleAssignments"},
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            what_if = temp / "what-if.json"
            output = temp / "assessment.json"
            what_if.write_text(json.dumps(payload), encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(ASSERTION),
                    str(what_if),
                    "--role-definition-guid",
                    ROLE_GUID,
                    "--extension-scope",
                    extension_scope,
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            assessment = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(assessment["status"], "accepted_bounded_rbac_bootstrap")
            self.assertEqual(len(assessment["mutating_changes"]), 2)

    def test_authorization_remains_bounded(self) -> None:
        record = json.loads(AUTH.read_text(encoding="utf-8"))
        self.assertEqual(record["status"], "authorized_not_consumed")
        self.assertEqual(record["scope"]["actions"], [ACTION])
        authority = record["authority"]
        self.assertTrue(authority["role_definition_create"])
        self.assertTrue(authority["role_assignment_create"])
        for key in (
            "application_deployment",
            "vm_mutation",
            "guest_command",
            "network_mutation",
            "transaction_replay",
            "github_pages_publication",
            "pull_request_merge",
            "cleanup",
        ):
            self.assertFalse(authority[key])

    def test_reconciliation_does_not_claim_execution(self) -> None:
        record = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        state = record["current_state"]
        self.assertTrue(state["repository_package_implemented"])
        self.assertTrue(state["azure_rbac_bootstrap_authorized"])
        self.assertFalse(state["azure_rbac_bootstrap_executed"])
        self.assertFalse(state["role_definition_observed"])
        self.assertFalse(state["role_assignment_observed"])
        self.assertFalse(state["effective_target_identity_permission_verified"])
        self.assertFalse(state["deployment_authorized"])


if __name__ == "__main__":
    unittest.main()
