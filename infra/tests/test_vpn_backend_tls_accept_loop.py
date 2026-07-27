from __future__ import annotations

import http.client
import json
from pathlib import Path
import socket
import ssl
import subprocess
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_PATH = ROOT / "infra" / "bootstrap" / "vpn-backend-cloud-init.yaml"


def extract_backend_source() -> str:
    lines = BOOTSTRAP_PATH.read_text(encoding="utf-8").splitlines()
    path_index = lines.index("  - path: /opt/servicetracer-demo/backend.py")
    content_index = lines.index("    content: |", path_index)
    source_lines: list[str] = []

    for line in lines[content_index + 1 :]:
        if line.startswith("  - path: ") or line == "runcmd:":
            break
        if line and not line.startswith("      "):
            raise AssertionError(f"unexpected backend source indentation: {line!r}")
        source_lines.append(line[6:] if line else "")

    return "\n".join(source_lines) + "\n"


def load_backend_namespace() -> dict[str, object]:
    namespace: dict[str, object] = {"__name__": "servicetracer_test_backend"}
    source = extract_backend_source()
    exec(compile(source, str(BOOTSTRAP_PATH), "exec"), namespace)
    namespace["BACKEND_ID"] = "VPN-TEST"
    namespace["BACKEND_MODE"] = "healthy"
    return namespace


class TLSAcceptLoopTests(unittest.TestCase):
    def test_tls_handshake_is_deferred_to_worker_threads(self) -> None:
        source = extract_backend_source()

        self.assertIn(
            "class TLSHandshakeThreadingHTTPServer(ThreadingHTTPServer):",
            source,
        )
        self.assertIn("do_handshake_on_connect=False", source)
        self.assertIn("tls_request.do_handshake()", source)
        self.assertIn("daemon_threads = True", source)
        self.assertNotIn("server.socket = context.wrap_socket", source)

    def test_raw_tcp_probe_connections_do_not_starve_https(self) -> None:
        namespace = load_backend_namespace()
        server_class = namespace["TLSHandshakeThreadingHTTPServer"]
        handler_class = namespace["Handler"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            certificate = temp_path / "server.crt"
            private_key = temp_path / "server.key"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-days",
                    "1",
                    "-keyout",
                    str(private_key),
                    "-out",
                    str(certificate),
                    "-subj",
                    "/CN=localhost",
                    "-addext",
                    "subjectAltName=IP:127.0.0.1",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            server_context.load_cert_chain(
                certfile=str(certificate),
                keyfile=str(private_key),
            )
            server = server_class(
                ("127.0.0.1", 0),
                handler_class,
                ssl_context=server_context,
                handshake_timeout_seconds=0.5,
            )
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()

            host, port = server.server_address
            raw_connections: list[socket.socket] = []
            try:
                for _ in range(12):
                    raw_connections.append(
                        socket.create_connection((host, port), timeout=1.0)
                    )

                client_context = ssl._create_unverified_context()
                connection = http.client.HTTPSConnection(
                    host,
                    port,
                    timeout=2.0,
                    context=client_context,
                )
                try:
                    connection.request("GET", "/healthz")
                    response = connection.getresponse()
                    payload = json.loads(response.read().decode("utf-8"))
                finally:
                    connection.close()

                self.assertEqual(response.status, 200)
                self.assertEqual(payload["backend"], "VPN-TEST")
                self.assertEqual(payload["listener"], "available")
            finally:
                for raw_connection in raw_connections:
                    raw_connection.close()
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=2.0)


if __name__ == "__main__":
    unittest.main()
