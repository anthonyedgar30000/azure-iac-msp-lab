from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
RESOLVER = ROOT / "infra" / "scripts" / "resolve_vm_plan.sh"


class ResolveVmPlanRuntimeTests(unittest.TestCase):
    def test_candidate_arrays_reach_arm_validation_without_nameref_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp = Path(temporary_directory)
            fake_bin = temp / "bin"
            artifacts = temp / "artifacts"
            github_output = temp / "github-output.txt"
            fake_bin.mkdir()

            fake_az = fake_bin / "az"
            fake_az.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env bash
                    set -euo pipefail

                    if [[ "$1 $2" == "vm show" ]]; then
                      printf 'Standard_B1s\\n'
                      exit 0
                    fi

                    if [[ "$1 $2" == "vm list-skus" ]]; then
                      cat <<'JSON'
                    [
                      {"name":"Standard_B1s","restrictions":[{"type":"Location","reasonCode":"NotAvailableForSubscription"}]},
                      {"name":"Standard_B1ms","restrictions":[]},
                      {"name":"Standard_B2s","restrictions":[]},
                      {"name":"Standard_B2ms","restrictions":[]},
                      {"name":"Standard_D2as_v5","restrictions":[]},
                      {"name":"Standard_D2s_v5","restrictions":[]}
                    ]
                    JSON
                      exit 0
                    fi

                    if [[ "$1 $2 $3" == "deployment group validate" ]]; then
                      printf '{"properties":{"provisioningState":"Succeeded"}}\\n'
                      exit 0
                    fi

                    if [[ "$1 $2 $3" == "deployment group what-if" ]]; then
                      printf '{"status":"Succeeded"}\\n'
                      exit 0
                    fi

                    printf 'unexpected az invocation: %s\\n' "$*" >&2
                    exit 99
                    """
                ),
                encoding="utf-8",
            )
            fake_az.chmod(0o755)

            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"

            result = subprocess.run(
                [
                    "bash",
                    str(RESOLVER),
                    "--resource-group",
                    "rg-servicetracer-dev-westus2",
                    "--location",
                    "westus2",
                    "--prefix",
                    "mst",
                    "--environment",
                    "dev",
                    "--deploy-demo-backends",
                    "true",
                    "--requested-backend-size",
                    "auto",
                    "--deploy-public-report-endpoint",
                    "true",
                    "--requested-collector-size",
                    "auto",
                    "--collector-source-ref",
                    "a" * 40,
                    "--expected-private-ip",
                    "10.20.40.10",
                    "--collector-port",
                    "8080",
                    "--collector-admin-ssh-public-key",
                    "ssh-ed25519 AAAATEST",
                    "--artifact-dir",
                    str(artifacts),
                    "--github-output",
                    str(github_output),
                ],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("circular name reference", result.stderr)

            backend_candidates = (
                artifacts.read_text(encoding="utf-8")
                if artifacts.is_file()
                else (artifacts / "backend-candidates.txt").read_text(encoding="utf-8")
            ).splitlines()
            collector_candidates = (
                artifacts / "collector-candidates.txt"
            ).read_text(encoding="utf-8").splitlines()

            self.assertEqual(backend_candidates[0], "Standard_B1s")
            self.assertEqual(collector_candidates[0], "Standard_B1s")
            self.assertEqual(len(backend_candidates), len(set(backend_candidates)))
            self.assertEqual(len(collector_candidates), len(set(collector_candidates)))

            attempts = [
                json.loads(line)
                for line in (artifacts / "sku-validation-attempts.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(attempts[0]["status"], "succeeded")
            self.assertEqual(attempts[0]["collector_vm_size"], "Standard_B1s")
            self.assertEqual(attempts[0]["demo_backend_vm_size"], "Standard_B1s")

            outputs = github_output.read_text(encoding="utf-8")
            self.assertIn("demo_backend_vm_size=Standard_B1s", outputs)
            self.assertIn("collector_vm_size=Standard_B1s", outputs)


if __name__ == "__main__":
    unittest.main()
