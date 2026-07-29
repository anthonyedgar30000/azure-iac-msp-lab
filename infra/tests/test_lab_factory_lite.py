from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from lab_factory.catalog import CatalogError, list_profiles, load_catalog, prepare_lab_plan
from lab_factory.cli import main as cli_main


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class AzureLabFactoryLiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_catalog(repository_root=REPOSITORY_ROOT)

    def _complete_parameters(self) -> dict[str, str]:
        return {
            "dnsLabel": "st-demo-api-test-123",
            "allowedOrigin": "https://example.invalid",
            "backendTransactionUrl": "https://backend.example.invalid/api/demo/run",
            "adminSshPublicKey": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestOnlyKey lab-test",
            "sourceRepository": "https://github.com/anthonyedgar30000/azure-iac-msp-lab.git",
            "sourceRef": "0123456789abcdef0123456789abcdef01234567",
            "installerUri": "https://raw.githubusercontent.com/anthonyedgar30000/azure-iac-msp-lab/0123456789abcdef0123456789abcdef01234567/workloads/servicetracer-demo-api/scripts/install.sh",
        }

    def test_catalog_contains_one_bounded_candidate_profile(self) -> None:
        profiles = list_profiles(self.catalog)
        self.assertEqual(len(profiles), 1)
        profile = profiles[0]
        self.assertEqual(profile["id"], "servicetracer-demo-api")
        self.assertEqual(profile["version"], "1.0.0")
        self.assertEqual(profile["release_state"], "candidate")
        self.assertEqual(profile["allowed_locations"], ["westus2"])
        self.assertEqual(profile["default_ttl_hours"], 8)

    def test_profile_references_existing_subscription_bicep_root(self) -> None:
        profile = self.catalog["profiles"][0]
        template = REPOSITORY_ROOT / profile["template"]["path"]
        self.assertTrue(template.is_file())
        source = template.read_text(encoding="utf-8")
        self.assertIn("targetScope = 'subscription'", source)
        self.assertEqual(profile["template"]["scope"], "subscription")

    def test_incomplete_request_stops_at_parameter_gate(self) -> None:
        plan = prepare_lab_plan(
            self.catalog,
            profile_id="servicetracer-demo-api",
            repository_root=REPOSITORY_ROOT,
        )
        self.assertEqual(plan["deployment"]["operation"], "prepare_only")
        self.assertFalse(plan["gates"]["ready_for_preflight"])
        self.assertEqual(plan["next_gate"], "parameters_required")
        self.assertEqual(
            plan["deployment"]["missing_required_parameters"],
            sorted(self._complete_parameters()),
        )
        self.assertFalse(plan["execution"]["azure_queries_performed"])
        self.assertFalse(plan["execution"]["azure_mutations_performed"])
        self.assertFalse(plan["execution"]["deployment_authorized"])

    def test_complete_request_prepares_preflight_without_echoing_values(self) -> None:
        parameters = self._complete_parameters()
        plan = prepare_lab_plan(
            self.catalog,
            profile_id="servicetracer-demo-api",
            environment="test",
            location="westus2",
            ttl_hours=6,
            request_id="lab-demo-001",
            parameters=parameters,
            repository_root=REPOSITORY_ROOT,
        )
        self.assertTrue(plan["gates"]["ready_for_preflight"])
        self.assertEqual(plan["next_gate"], "preflight_required")
        self.assertEqual(plan["deployment"]["resource_group"], "rg-st-demo-api-test-westus2")
        self.assertEqual(plan["deployment"]["missing_required_parameters"], [])
        self.assertEqual(plan["deployment"]["user_supplied_parameter_names"], sorted(parameters))
        serialized = json.dumps(plan, sort_keys=True)
        for value in parameters.values():
            self.assertNotIn(value, serialized)
        self.assertRegex(plan["deployment"]["template_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(plan["plan_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertFalse(plan["execution"]["deployment_authorized"])
        self.assertFalse(plan["execution"]["cleanup_authorized"])

    def test_plan_is_deterministic_for_same_request(self) -> None:
        parameters = self._complete_parameters()
        first = prepare_lab_plan(
            self.catalog,
            profile_id="servicetracer-demo-api",
            parameters=parameters,
            request_id="lab-demo-002",
            repository_root=REPOSITORY_ROOT,
        )
        second = prepare_lab_plan(
            self.catalog,
            profile_id="servicetracer-demo-api",
            parameters=parameters,
            request_id="lab-demo-002",
            repository_root=REPOSITORY_ROOT,
        )
        self.assertEqual(first, second)

    def test_unapproved_location_is_rejected(self) -> None:
        with self.assertRaisesRegex(CatalogError, "location is not allowed"):
            prepare_lab_plan(
                self.catalog,
                profile_id="servicetracer-demo-api",
                location="eastus",
                repository_root=REPOSITORY_ROOT,
            )

    def test_fixed_parameter_override_is_rejected(self) -> None:
        with self.assertRaisesRegex(CatalogError, "fixed parameters cannot be overridden"):
            prepare_lab_plan(
                self.catalog,
                profile_id="servicetracer-demo-api",
                parameters={"prefix": "other"},
                repository_root=REPOSITORY_ROOT,
            )

    def test_ttl_outside_profile_boundary_is_rejected(self) -> None:
        with self.assertRaisesRegex(CatalogError, "ttl_hours is outside"):
            prepare_lab_plan(
                self.catalog,
                profile_id="servicetracer-demo-api",
                ttl_hours=25,
                repository_root=REPOSITORY_ROOT,
            )

    def test_cli_list_is_static_and_cloud_free(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main(["--repository-root", str(REPOSITORY_ROOT), "list"])
        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["profiles"][0]["id"], "servicetracer-demo-api")
        self.assertFalse(payload["execution"]["azure_queries_performed"])
        self.assertFalse(payload["execution"]["azure_mutations_performed"])

    def test_cli_rejects_duplicate_parameter(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main(
                [
                    "--repository-root",
                    str(REPOSITORY_ROOT),
                    "prepare",
                    "--profile",
                    "servicetracer-demo-api",
                    "--parameter",
                    "dnsLabel=one",
                    "--parameter",
                    "dnsLabel=two",
                ]
            )
        self.assertEqual(exit_code, 2)
        payload = json.loads(stderr.getvalue())
        self.assertIn("supplied more than once", payload["error"])
        self.assertFalse(payload["azure_queries_performed"])
        self.assertFalse(payload["azure_mutations_performed"])


if __name__ == "__main__":
    unittest.main()
