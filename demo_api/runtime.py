from __future__ import annotations

import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _tls_context() -> ssl.SSLContext:
    """Return the bounded lab TLS context used for the synthetic backends.

    The backend endpoint is fixed by deployment configuration and is not supplied by
    the caller. The synthetic backend VMs use short-lived self-signed certificates,
    so the demo runtime deliberately disables certificate validation only for this
    single configured lab hop.
    """

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def run_transaction(backend_transaction_url: str, correlation_id: str) -> dict:
    url = f"{backend_transaction_url}?{urlencode({'correlation_id': correlation_id})}"
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
