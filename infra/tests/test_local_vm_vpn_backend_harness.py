from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools" / "local-vm-vpn-backend"


class LocalVmVpnBackendHarnessTests(unittest.TestCase):
    def test_required_harness_files_exist(self) -> None:
        required = {
            "README.md",
            "cloud-init.yaml",
            "install-and-test.sh",
            "render_artifacts.py",
            "run.ps1",
            "run.sh",
        }
        self.assertEqual(required, {path.name for path in HARNESS.iterdir()})

    def test_bash_scripts_parse(self) -> None:
        for name in ("install-and-test.sh", "run.sh"):
            subprocess.run(
                ["bash", "-n", str(HARNESS / name)],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_renderer_emits_exact_backend_and_concrete_unit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            subprocess.run(
                [
                    sys.executable,
                    str(HARNESS / "render_artifacts.py"),
                    "--repo-root",
                    str(ROOT),
                    "--output-dir",
                    str(output_dir),
                    "--backend-id",
                    "VPN-LOCAL-TEST",
                    "--mode",
                    "healthy",
                    "--listener-port",
                    "443",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            backend = (output_dir / "backend.py").read_text(encoding="utf-8")
            unit = (output_dir / "servicetracer-demo-backend.service").read_text(
                encoding="utf-8"
            )
            metadata = json.loads(
                (output_dir / "rendered-artifacts.json").read_text(encoding="utf-8")
            )

            self.assertIn("TLSHandshakeThreadingHTTPServer", backend)
            self.assertIn("do_handshake_on_connect=False", backend)
            self.assertIn("tls_request.do_handshake()", backend)
            self.assertNotIn("server.socket = context.wrap_socket", backend)
            self.assertIn("Environment=SERVICETRACER_BACKEND_ID=VPN-LOCAL-TEST", unit)
            self.assertIn("Environment=SERVICETRACER_BACKEND_MODE=healthy", unit)
            self.assertIn("Environment=SERVICETRACER_LISTENER_PORT=443", unit)
            self.assertEqual(metadata["backend_id"], "VPN-LOCAL-TEST")
            self.assertEqual(metadata["listener_port"], 443)
            self.assertEqual(len(metadata["files"]["backend.py"]["sha256"]), 64)

    def test_local_deployment_has_named_checkpoints_and_rollback_marker(self) -> None:
        script = (HARNESS / "install-and-test.sh").read_text(encoding="utf-8")
        for checkpoint in (
            "service-active",
            "listener-present",
            "loopback-health",
            "private-ip-health",
            "raw-probes-connected",
            "https-survives-raw-probes",
            "listener-queue-below-backlog",
            "rendered-hashes-match-installed",
            "local-vm-validation-complete",
        ):
            self.assertIn(checkpoint, script)

        self.assertIn("SERVICETRACER_LOCAL_VALIDATION_SUCCESS", script)
        self.assertIn("SERVICETRACER_LOCAL_ROLLBACK_PERFORMED", script)
        self.assertIn("FORCE_FAILURE_AFTER_INSTALL", script)
        self.assertIn("systemctl restart", script)
        self.assertIn("ufw allow", script)

    def test_harness_is_local_only(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in HARNESS.iterdir()
            if path.is_file()
        )
        self.assertNotIn("azure/login", combined)
        self.assertNotIn("az vm", combined)
        self.assertNotIn("az network", combined)
        self.assertNotIn("AZURE_CLIENT_ID", combined)

    def test_cloud_init_matches_declared_ubuntu_guest_dependencies(self) -> None:
        cloud_init = (HARNESS / "cloud-init.yaml").read_text(encoding="utf-8")
        for package in ("curl", "git", "iproute2", "jq", "openssl", "python3", "ufw"):
            self.assertIn(f"  - {package}\n", cloud_init)
        self.assertNotIn("cloud-init status --wait", cloud_init)

    def test_launchers_request_ubuntu_24_04(self) -> None:
        bash_launcher = (HARNESS / "run.sh").read_text(encoding="utf-8")
        powershell_launcher = (HARNESS / "run.ps1").read_text(encoding="utf-8")
        self.assertIn("multipass launch 24.04", bash_launcher)
        self.assertIn("launch 24.04", powershell_launcher)
        self.assertIn("--cpus 1", bash_launcher)
        self.assertIn("--memory 2G", bash_launcher)
        self.assertIn("--disk 12G", bash_launcher)


if __name__ == "__main__":
    unittest.main()
