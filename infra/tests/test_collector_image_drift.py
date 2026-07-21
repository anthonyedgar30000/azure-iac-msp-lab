from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "infra" / "scripts" / "check_collector_image_drift.sh"
IMAGE = ROOT / "infra" / "config" / "collector-image.json"


class CollectorImageDriftTests(unittest.TestCase):
    def _run(self, mode: str) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        temp = Path(temporary_directory.name)
        fake_bin = temp / "bin"
        artifacts = temp / "artifacts"
        github_output = temp / "github-output.txt"
        az_log = temp / "az.log"
        fake_bin.mkdir()

        fake_az = fake_bin / "az"
        fake_az.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                set -euo pipefail
                printf '%s\\n' "$*" >> "$AZ_LOG"

                if [[ "$1 $2" == "vm show" ]]; then
                  cat <<'JSON'
                {
                  "id":"/subscriptions/test/resourceGroups/rg-servicetracer-dev-westus2/providers/Microsoft.Compute/virtualMachines/vm-stcollector-mst-dev",
                  "hardwareProfile":{"vmSize":"Standard_B2ats_v2"},
                  "storageProfile":{
                    "imageReference":{"publisher":"Canonical","offer":"0001-com-ubuntu-server-jammy","sku":"22_04-lts-gen2","version":"22.04.202607010"},
                    "osDisk":{"managedDisk":{"id":"/disks/os-current"}},
                    "dataDisks":[{"name":"disk-stcollector-evidence-mst-dev","managedDisk":{"id":"/disks/evidence-current"}}]
                  },
                  "identity":{"principalId":"principal-current"},
                  "networkProfile":{"networkInterfaces":[{"id":"/nics/collector-current"}]}
                }
                JSON
                  exit 0
                fi

                if [[ "$1 $2 $3" == "network nic show" ]]; then
                  printf '{"id":"/nics/collector-current","name":"nic-stcollector-mst-dev"}\\n'
                  exit 0
                fi

                if [[ "$1 $2" == "disk show" ]]; then
                  if [[ "$*" == *"disk-stcollector-evidence-mst-dev"* ]]; then
                    printf '{"id":"/disks/evidence-current","name":"disk-stcollector-evidence-mst-dev"}\\n'
                  else
                    printf '{"id":"/disks/os-current","name":"disk-stcollector-os-mst-dev"}\\n'
                  fi
                  exit 0
                fi

                if [[ "$1 $2 $3" == "role assignment list" ]]; then
                  printf '[{"roleDefinitionName":"Storage Blob Data Contributor","scope":"/storage/report"}]\\n'
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
        environment["AZ_LOG"] = str(az_log)

        result = subprocess.run(
            [
                "bash",
                str(SCRIPT),
                "--mode",
                mode,
                "--resource-group",
                "rg-servicetracer-dev-westus2",
                "--prefix",
                "mst",
                "--environment",
                "dev",
                "--desired-image-file",
                str(IMAGE),
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
        return result, artifacts, az_log

    def test_guard_blocks_immutable_image_drift_before_arm_planning(self) -> None:
        result, artifacts, az_log = self._run("guard")
        self.assertEqual(result.returncode, 42, result.stderr)
        self.assertIn("immutable image", result.stderr.lower())
        assessment = json.loads(
            (artifacts / "collector-image-drift.json").read_text(encoding="utf-8")
        )
        self.assertEqual(assessment["status"], "replacement_required")
        self.assertTrue(assessment["immutable_image_drift"])
        self.assertIn("ubuntu-24_04-lts", json.dumps(assessment))
        self.assertNotIn("deployment group validate", az_log.read_text(encoding="utf-8"))

    def test_plan_captures_preservation_boundary_without_mutation(self) -> None:
        result, artifacts, az_log = self._run("plan")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(
            (artifacts / "collector-replacement-plan.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(plan["operation"], "plan_only")
        self.assertFalse(plan["execution_authorized"])
        self.assertFalse(plan["execution_performed"])
        self.assertFalse(plan["azure_mutations_performed"])
        self.assertTrue(
            plan["preservation_boundary"]["evidence_disk_must_be_preserved"]
        )
        self.assertEqual(
            plan["preservation_boundary"]["evidence_disk_id"],
            "/disks/evidence-current",
        )
        self.assertEqual(
            plan["future_exact_confirmation"],
            "REPLACE:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev",
        )

        invocation_log = az_log.read_text(encoding="utf-8")
        for forbidden in (
            " vm delete",
            " disk delete",
            " snapshot create",
            " nic delete",
            " vm deallocate",
            " disk detach",
            " disk attach",
            " deployment group create",
        ):
            self.assertNotIn(forbidden, invocation_log)


if __name__ == "__main__":
    unittest.main()
