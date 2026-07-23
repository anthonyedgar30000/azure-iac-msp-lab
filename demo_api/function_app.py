from __future__ import annotations

import json
import os
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

import azure.functions as func

from core import build_api_response, normalize_attempts

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

BACKEND_TRANSACTION_URL = os.environ.get("SERVICETRACER_BACKEND_TRANSACTION_URL", "")
ALLOWED_ORIGIN = os.environ.get(
    "SERVICETRACER_ALLOWED_ORIGIN", "https://anthonyedgar30000.github.io"
)
SOURCE_ID = os.environ.get("WEBSITE_HOSTNAME", "servicetracer-demo-api")


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Vary": "Origin",
    }


def _json_response(payload: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, separators=(",", ":")),
        status_code=status_code,
        headers=_headers(),
        mimetype="application/json",
    )


def _tls_context() -> ssl.SSLContext:
    # The synthetic backend VMs use short-lived self-signed certificates. The API target is
    # fixed by deployment configuration, never supplied by the caller, and exists only to
    # exercise the bounded lab listener through the Azure Load Balancer.
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _run_transaction(correlation_id: str) -> dict:
    url = f"{BACKEND_TRANSACTION_URL}?{urlencode({'correlation_id': correlation_id})}"
    request = Request(url, headers={"User-Agent": "servicetracer-demo-api/1.0"})
    status_code = 0
    raw_body = b""
    try:
        with urlopen(request, context=_tls_context(), timeout=10) as response:
            status_code = response.status
            raw_body = response.read()
    except HTTPError as exc:
        status_code = exc.code
        raw_body = exc.read()
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "correlation_id": correlation_id,
            "backend": "UNRESOLVED",
            "transaction_status": "failed",
            "failure_boundary": "listener_unreachable",
            "stages": [],
            "http_status": 0,
            "transport_error": type(exc).__name__,
        }

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "correlation_id": correlation_id,
            "backend": "UNRESOLVED",
            "transaction_status": "failed",
            "failure_boundary": "invalid_backend_response",
            "stages": [],
            "http_status": status_code,
        }

    if payload.get("schema_version") != "servicetracer.azure-demo-response.v1":
        return {
            "correlation_id": correlation_id,
            "backend": str(payload.get("backend") or "UNRESOLVED"),
            "transaction_status": "failed",
            "failure_boundary": "unsupported_backend_schema",
            "stages": [],
            "http_status": status_code,
        }

    return {
        "correlation_id": correlation_id,
        "backend": str(payload.get("backend") or "UNRESOLVED"),
        "transaction_status": str(payload.get("transaction_status") or "failed"),
        "failure_boundary": payload.get("failure_boundary"),
        "stages": payload.get("stages") if isinstance(payload.get("stages"), list) else [],
        "http_status": status_code,
        "backend_observed_at": payload.get("observed_at"),
    }


@app.route(route="health", methods=["GET"])
def health(_: func.HttpRequest) -> func.HttpResponse:
    configured = bool(BACKEND_TRANSACTION_URL.startswith("https://"))
    return _json_response(
        {
            "status": "healthy" if configured else "misconfigured",
            "schema_version": "servicetracer.demo-api-health.v1",
            "backend_target_configured": configured,
        },
        200 if configured else 503,
    )


@app.route(route="demo/run", methods=["POST", "OPTIONS"])
def demo_run(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_headers())
    if not BACKEND_TRANSACTION_URL.startswith("https://"):
        return _json_response({"error": "backend_target_not_configured"}, 503)

    try:
        body = req.get_json()
    except ValueError:
        body = {}
    try:
        attempts = normalize_attempts(body.get("attempts") if isinstance(body, dict) else None)
    except ValueError as exc:
        return _json_response({"error": "invalid_request", "detail": str(exc)}, 400)

    transactions = [_run_transaction(str(uuid4())) for _ in range(attempts)]
    return _json_response(build_api_response(transactions, source=SOURCE_ID))
