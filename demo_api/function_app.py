from __future__ import annotations

import json
import os
from uuid import uuid4

import azure.functions as func

from core import build_api_response, normalize_attempts
from runtime import run_transaction

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

    transactions = [
        run_transaction(BACKEND_TRANSACTION_URL, str(uuid4())) for _ in range(attempts)
    ]
    return _json_response(build_api_response(transactions, source=SOURCE_ID))
