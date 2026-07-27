from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "infra" / "scripts" / "verify_collector_demo_api_evidence.py"
SOURCE = "be7a0215a2ac47dd038b042e6b21e3c2e155d86a"
ORIGIN = "https://anthonyedgar30000.github.io"
VM = "vm-stcollector-mst-dev"
REGION = "westus2"


class CollectorDemoApiCrlfVerifierTests(unittest.TestCase):
    def test_valid_crlf_headers_and_exact_runtime_evidence_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            health = {
                "status": "healthy",
                "schema_version": "servicetracer.demo-api-health.v1",
                "backend_target_configured": True,
                "hosting_model": "collector_vm_systemd",
                "azure_host": {
                    "verified": True,
                    "vm_name": VM,
                    "location": REGION,
                    "source_ref": SOURCE,
                },
            }
            run = {
                "schema_version": "servicetracer.demo-api-response.v1",
                "report": {"investigation_boundary": {"exact_root_cause_claimed": False}},
                "transactions": [
                    {
                        "transaction_status": "failed",
                        "failure_boundary": "listener_unreachable",
                    }
                    for _ in range(20)
                ],
                "azure_host": {
                    "verified": True,
                    "vm_name": VM,
                    "location": REGION,
                    "source_ref": SOURCE,
                },
            }
            extension = {"provisioningState": "Succeeded", "forceUpdateTag": SOURCE}
            (root / "health.json").write_text(json.dumps(health), encoding="utf-8")
            (root / "run.json").write_text(json.dumps(run), encoding="utf-8")
            (root / "extension.json").write_text(json.dumps(extension), encoding="utf-8")
            (root / "headers.txt").write_bytes(
                (
                    "HTTP/1.1 204 No Content\r\n"
                    f"Access-Control-Allow-Origin: {ORIGIN}\r\n"
                    "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                    "\r\n"
                ).encode("iso-8859-1")
            )
            output = root / "verification.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(VERIFIER),
                    "--health",
                    str(root / "health.json"),
                    "--run",
                    str(root / "run.json"),
                    "--headers",
                    str(root / "headers.txt"),
                    "--extension",
                    str(root / "extension.json"),
                    "--allowed-origin",
                    ORIGIN,
                    "--expected-source",
                    SOURCE,
                    "--expected-vm",
                    VM,
                    "--expected-region",
                    REGION,
                    "--attempts",
                    "20",
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(result["service_validated"])
            self.assertTrue(result["cors_verified"])
            self.assertEqual(result["transactions_verified"], 20)
            self.assertEqual(result["failure_boundary_counts"], {"listener_unreachable": 20})

    def test_wrong_origin_fails_closed(self) -> None:
        source = VERIFIER.read_text(encoding="utf-8")
        self.assertIn('origins == [args.allowed_origin]', source)
        self.assertIn('decode("iso-8859-1")', source)
        self.assertIn("splitlines()", source)
        self.assertNotIn('grep -Eiq', source)


if __name__ == "__main__":
    unittest.main()
