from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "infra" / "scripts" / "run_collector_demo_api_what_if_cycle.sh"
VERIFIER_PATH = (
    ROOT / "infra" / "scripts" / "verify_collector_demo_api_scheduler_artifact.py"
)
CRON_EXAMPLE = ROOT / "ops" / "cron" / "collector-demo-api-what-if.cron.example"
ENV_EXAMPLE = ROOT / "ops" / "cron" / "collector-demo-api-scheduler.env.example"

spec = importlib.util.spec_from_file_location("scheduler_artifact_verifier", VERIFIER_PATH)
assert spec and spec.loader
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class CollectorDemoApiSchedulerTests(unittest.TestCase):
    def test_runner_is_syntactically_valid_and_never_dispatches_deploy(self) -> None:
        subprocess.run(
            ["bash", "-n", str(RUNNER)],
            check=True,
            capture_output=True,
            text=True,
        )
        text = RUNNER.read_text(encoding="utf-8")
        for expected in (
            "flock -n",
            "gh workflow run",
            "-f operation=what-if",
            "gh run download",
            "verify_collector_demo_api_scheduler_artifact.py",
            "evaluate-collector-demo-api",
            "explicit_deploy_authorization",
            "sync_with_reality",
            "GH_TOKEN_FILE",
            "RAW_EVIDENCE_ROOT",
            "SANITIZED_EVIDENCE_ROOT",
        ):
            self.assertIn(expected, text)
        for prohibited in (
            "-f operation=deploy",
            "az deployment group create",
            "az vm run-command",
            "az resource delete",
            "az group delete",
            "gh run rerun",
        ):
            self.assertNotIn(prohibited, text)

    def test_cron_and_environment_examples_preserve_the_boundary(self) -> None:
        cron = CRON_EXAMPLE.read_text(encoding="utf-8")
        env = ENV_EXAMPLE.read_text(encoding="utf-8")
        self.assertIn("*/15 * * * *", cron)
        self.assertIn("run_collector_demo_api_what_if_cycle.sh", cron)
        self.assertIn("GH_TOKEN_FILE=", env)
        self.assertIn("REVIEWED_COMMIT=0000000000000000000000000000000000000000", env)
        self.assertNotIn("GH_TOKEN=", env)
        self.assertNotIn("operation=deploy", cron + env)

    def _write_valid_artifact(self, directory: Path) -> dict[str, str]:
        expected = {
            "run_id": "123456",
            "commit": "a" * 40,
            "resource_group": "rg-servicetracer-dev-westus2",
            "location": "westus2",
            "environment": "dev",
            "prefix": "mst",
            "dns_label": "st-demo-api-aeg30000",
            "allowed_origin": "https://anthonyedgar30000.github.io",
        }
        payloads = {
            "request.json": {
                "schema_version": "servicetracer.collector-demo-api-request.v2",
                "operation": "what-if",
                "reviewed_commit": expected["commit"],
                "resource_group": expected["resource_group"],
                "location": expected["location"],
                "environment": expected["environment"],
                "prefix": expected["prefix"],
                "dns_label": expected["dns_label"],
                "allowed_origin": expected["allowed_origin"],
                "azure_authentication_authorized": True,
                "azure_mutations_authorized": False,
                "collector_configuration_mutation_authorized": False,
                "base_infrastructure_mutation_authorized": False,
                "microsoft_web_authorized": False,
            },
            "readiness-assessment.json": {
                "schema_version": "servicetracer.collector-demo-api-readiness.v2",
                "blockers": [],
                "deployment_decision_ready": True,
                "public_ip_quota": {
                    "status": "sufficient",
                    "current": 1,
                    "limit": 3,
                    "remaining": 2,
                    "sufficient": True,
                },
                "deployment_authorized": False,
                "azure_mutations_performed": False,
            },
            "arm-validation.json": {
                "properties": {"provisioningState": "Succeeded"}
            },
            "arm-what-if.json": {
                "status": "Succeeded",
                "changes": [],
            },
            "what-if-assessment.json": {
                "schema_version": "servicetracer.collector-demo-api-what-if.v2",
                "status": "accepted_isolated_collector_api_changes",
                "total_changes": 9,
                "creates": 9,
                "ignored_managed_leftovers": [],
                "collector_nic_modifications": [],
                "collector_vm_modifications": [],
                "base_infrastructure_modifications": [],
                "forbidden_changes": [],
                "managed_web_resources_proposed": False,
                "deployment_authorized": False,
                "azure_mutations_performed": False,
            },
            "azure-context.json": {"subscriptionName": "Azure for Students"},
        }
        for name, payload in payloads.items():
            (directory / name).write_text(
                json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
            )

        manifest_lines = []
        for name in sorted(payloads):
            digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
            manifest_lines.append(f"{digest}  collector-demo-api-evidence/{name}")
        (directory / "sha256sums.txt").write_text(
            "\n".join(manifest_lines) + "\n", encoding="utf-8"
        )
        (directory / "evidence-manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": "servicetracer.collector-demo-api-evidence.v1",
                    "operation": "what-if",
                    "reviewed_commit": expected["commit"],
                    "run_id": expected["run_id"],
                    "run_attempt": "1",
                    "generated_at": "2026-07-23T21:00:00Z",
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return expected

    def test_verifier_accepts_exact_read_only_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            expected = self._write_valid_artifact(directory)
            result = verifier.verify_artifact(
                directory,
                expected_run_id=expected["run_id"],
                expected_commit=expected["commit"],
                expected_resource_group=expected["resource_group"],
                expected_location=expected["location"],
                expected_environment=expected["environment"],
                expected_prefix=expected["prefix"],
                expected_dns_label=expected["dns_label"],
                expected_allowed_origin=expected["allowed_origin"],
            )
        self.assertEqual(result["status"], "verified_read_only_what_if_artifact")
        self.assertTrue(result["readiness_passed"])
        self.assertFalse(result["azure_mutations_authorized"])
        self.assertFalse(result["deployment_authorized"])

    def test_verifier_rejects_tampering_and_mutation_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            expected = self._write_valid_artifact(directory)
            request_path = directory / "request.json"
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["azure_mutations_authorized"] = True
            request_path.write_text(json.dumps(request) + "\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                verifier.verify_artifact(
                    directory,
                    expected_run_id=expected["run_id"],
                    expected_commit=expected["commit"],
                    expected_resource_group=expected["resource_group"],
                    expected_location=expected["location"],
                    expected_environment=expected["environment"],
                    expected_prefix=expected["prefix"],
                    expected_dns_label=expected["dns_label"],
                    expected_allowed_origin=expected["allowed_origin"],
                )


if __name__ == "__main__":
    unittest.main()
