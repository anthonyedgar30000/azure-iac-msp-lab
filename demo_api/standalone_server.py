from __future__ import annotations

import json
import logging
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from uuid import uuid4

from core import build_api_response, normalize_attempts
from runtime import run_transaction

BACKEND_TRANSACTION_URL = os.environ.get("SERVICETRACER_BACKEND_TRANSACTION_URL", "")
ALLOWED_ORIGIN = os.environ.get(
    "SERVICETRACER_ALLOWED_ORIGIN", "https://anthonyedgar30000.github.io"
)
SOURCE_ID = os.environ.get("SERVICETRACER_SOURCE_ID", "collector-hosted-demo-api")
HOSTING_MODEL = os.environ.get("SERVICETRACER_HOSTING_MODEL", "collector_vm_systemd")
LISTEN_ADDRESS = os.environ.get("SERVICETRACER_DEMO_API_LISTEN", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("SERVICETRACER_DEMO_API_PORT", "8090"))
MAX_REQUEST_BYTES = 4096

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("servicetracer.demo_api")


def _response_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Vary": "Origin",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    }


def _origin_permitted(origin: str | None) -> bool:
    return not origin or origin == ALLOWED_ORIGIN


class DemoApiHandler(BaseHTTPRequestHandler):
    server_version = "ServiceTracerDemoAPI/1.0"
    sys_version = ""

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status.value)
        for name, value in _response_headers().items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _path(self) -> str:
        return urlsplit(self.path).path.rstrip("/") or "/"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if self._path() != "/api/health":
            self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return

        configured = BACKEND_TRANSACTION_URL.startswith("https://")
        self._send_json(
            {
                "status": "healthy" if configured else "misconfigured",
                "schema_version": "servicetracer.demo-api-health.v1",
                "backend_target_configured": configured,
                "hosting_model": HOSTING_MODEL,
            },
            HTTPStatus.OK if configured else HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if self._path() != "/api/demo/run":
            self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        if not _origin_permitted(self.headers.get("Origin")):
            self._send_json({"error": "origin_not_allowed"}, HTTPStatus.FORBIDDEN)
            return
        self.send_response(HTTPStatus.NO_CONTENT.value)
        for name, value in _response_headers().items():
            self.send_header(name, value)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if self._path() != "/api/demo/run":
            self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        if not _origin_permitted(self.headers.get("Origin")):
            self._send_json({"error": "origin_not_allowed"}, HTTPStatus.FORBIDDEN)
            return
        if not BACKEND_TRANSACTION_URL.startswith("https://"):
            self._send_json(
                {"error": "backend_target_not_configured"},
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json({"error": "invalid_content_length"}, HTTPStatus.BAD_REQUEST)
            return
        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json({"error": "request_too_large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return

        try:
            body = json.loads(self.rfile.read(content_length) or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            attempts = normalize_attempts(body.get("attempts") if isinstance(body, dict) else None)
        except ValueError as exc:
            self._send_json(
                {"error": "invalid_request", "detail": str(exc)},
                HTTPStatus.BAD_REQUEST,
            )
            return

        transactions = [
            run_transaction(BACKEND_TRANSACTION_URL, str(uuid4()))
            for _ in range(attempts)
        ]
        self._send_json(build_api_response(transactions, source=SOURCE_ID))

    def log_message(self, format_string: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.address_string(), format_string % args)


def main() -> int:
    if not 1 <= LISTEN_PORT <= 65535:
        raise SystemExit("SERVICETRACER_DEMO_API_PORT must be between 1 and 65535")
    server = ThreadingHTTPServer((LISTEN_ADDRESS, LISTEN_PORT), DemoApiHandler)
    LOGGER.info("Listening on http://%s:%s", LISTEN_ADDRESS, LISTEN_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
