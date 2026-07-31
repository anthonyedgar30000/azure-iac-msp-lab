from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
VERIFIER = ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "verify_downloaded_plan_manifest.sh"
ORIGINAL_PREFIX = "servicetracer-demo-api-subproject-plan-evidence"


class PlanManifestVerifierTests(unittest.TestCase):
    def test_flattened_download_verifies_original_prefixed_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = Path(temp) / "accepted-plan-evidence"
            plan_dir.mkdir()
            evidence = plan_dir / "request.json"
            evidence.write_text('{"ok":true}\n', encoding="utf-8")
            digest = subprocess.check_output(["sha256sum", str(evidence)], text=True).split()[0]
            (plan_dir / "artifact-manifest.sha256").write_text(
                f"{digest}  {ORIGINAL_PREFIX}/request.json\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["bash", str(VERIFIER), str(plan_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("request.json: OK", result.stdout)

    def test_tampered_flattened_download_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plan_dir = Path(temp) / "accepted-plan-evidence"
            plan_dir.mkdir()
            (plan_dir / "request.json").write_text("tampered\n", encoding="utf-8")
            (plan_dir / "artifact-manifest.sha256").write_text(
                f"{'0' * 64}  {ORIGINAL_PREFIX}/request.json\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["bash", str(VERIFIER), str(plan_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
