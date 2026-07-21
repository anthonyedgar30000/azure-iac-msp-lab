"""Sanitize and publish bounded ServiceTracer reports.

The public report path deliberately exports only the technician-handoff contract.
Unexpected analyzer fields are dropped rather than forwarded to a browser.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import json
from pathlib import Path
import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


PUBLIC_SCHEMA_VERSION = "servicetracer.public-report.v1"
DEFAULT_TTL_SECONDS = 900
DEFAULT_CONTAINER = "$web"
DEFAULT_BLOB_PATH = "reports/technician-handoff-report.json"
_STORAGE_ACCOUNT_PATTERN = re.compile(r"^[a-z0-9]{3,24}$")
_ALLOWED_ROOT_CAUSE_STATES = {
    "not_determined",
    "not_determined_by_servicetracer",
}


class PublicationError(RuntimeError):
    """Raised when a bounded report cannot be safely prepared or published."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PublicationError(f"{field} must be an object")
    return value


def _copy_fields(source: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: source.get(field) for field in fields if field in source}


def sanitize_technician_handoff(report: dict[str, Any]) -> dict[str, Any]:
    """Return a strict, public-safe projection of a technician handoff report."""

    report = _mapping(report, "report")
    if report.get("status") != "technician_investigation_required":
        raise PublicationError(
            "only technician_investigation_required reports can be published"
        )

    boundary = _mapping(report.get("investigation_boundary"), "investigation_boundary")
    if boundary.get("exact_root_cause_claimed") is not False:
        raise PublicationError("public reports must not claim an exact root cause")

    root_cause = _mapping(report.get("root_cause"), "root_cause")
    if root_cause.get("status") not in _ALLOWED_ROOT_CAUSE_STATES:
        raise PublicationError("public report contains an unsupported root-cause state")

    incident = _mapping(report.get("incident"), "incident")
    load_balancer = _mapping(report.get("load_balancer"), "load_balancer")
    localization = _mapping(report.get("localization"), "localization")
    backend_states = _mapping(load_balancer.get("backend_states"), "backend_states")
    failure_rates = _mapping(
        localization.get("backend_failure_rates"), "backend_failure_rates"
    )

    safe_backend_states: dict[str, dict[str, Any]] = {}
    for backend, backend_state in backend_states.items():
        safe_backend_states[str(backend)] = _copy_fields(
            _mapping(backend_state, f"backend_states.{backend}"),
            ("administrative_state", "probe_status"),
        )

    safe_failure_rates: dict[str, float] = {}
    for backend, failure_rate in failure_rates.items():
        if not isinstance(failure_rate, (int, float)) or isinstance(failure_rate, bool):
            raise PublicationError(
                f"backend_failure_rates.{backend} must be a number"
            )
        if failure_rate < 0 or failure_rate > 1:
            raise PublicationError(
                f"backend_failure_rates.{backend} must be between 0 and 1"
            )
        safe_failure_rates[str(backend)] = float(failure_rate)

    workflow = report.get("technician_workflow")
    if not isinstance(workflow, list) or not workflow:
        raise PublicationError("technician_workflow must be a non-empty array")

    safe_workflow: list[dict[str, Any]] = []
    for index, step in enumerate(workflow):
        safe_step = _copy_fields(
            _mapping(step, f"technician_workflow[{index}]"),
            (
                "step_id",
                "owner",
                "status",
                "action",
                "purpose",
                "success_criteria",
            ),
        )
        if not safe_step.get("step_id") or not safe_step.get("action"):
            raise PublicationError(
                f"technician_workflow[{index}] is missing step_id or action"
            )
        safe_workflow.append(safe_step)

    return {
        "scenario": report.get("scenario"),
        "status": report.get("status"),
        "incident": _copy_fields(
            incident,
            (
                "classification",
                "attempts",
                "successful_attempts",
                "failed_attempts",
            ),
        ),
        "load_balancer": {
            **_copy_fields(
                load_balancer,
                (
                    "status",
                    "probe_name",
                    "probe_scope",
                    "probe_gap_detected",
                ),
            ),
            "backend_states": safe_backend_states,
        },
        "localization": {
            **_copy_fields(
                localization,
                (
                    "suspect_backend",
                    "healthy_comparison_backend",
                    "suspect_probe_status",
                ),
            ),
            "backend_failure_rates": safe_failure_rates,
        },
        "service_tracer_finding": report.get("service_tracer_finding"),
        "investigation_boundary": _copy_fields(
            boundary,
            (
                "service_tracer_stops_at",
                "exact_root_cause_claimed",
                "statement",
            ),
        ),
        "root_cause": _copy_fields(root_cause, ("status", "owner")),
        "temporary_service_status": report.get("temporary_service_status"),
        "technician_workflow": safe_workflow,
    }


def _as_utc(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise PublicationError("generated_at must be timezone-aware")
    return current.astimezone(timezone.utc)


def _iso8601(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def build_public_envelope(
    report: dict[str, Any],
    *,
    source_id: str,
    servicetracer_version: str,
    generated_at: datetime | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> dict[str, Any]:
    """Attach provenance and expiry metadata to the sanitized report."""

    if not source_id.strip():
        raise PublicationError("source_id must not be empty")
    if ttl_seconds < 60 or ttl_seconds > 86400:
        raise PublicationError("ttl_seconds must be between 60 and 86400")

    generated = _as_utc(generated_at)
    expires = generated + timedelta(seconds=ttl_seconds)
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "generated_at": _iso8601(generated),
        "expires_at": _iso8601(expires),
        "source": {
            "kind": "azure_collector",
            "id": source_id,
            "servicetracer_version": servicetracer_version,
        },
        "report": sanitize_technician_handoff(report),
    }


def render_public_envelope(envelope: dict[str, Any]) -> bytes:
    return (json.dumps(envelope, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_public_envelope(path: str | Path, envelope: dict[str, Any]) -> Path:
    """Atomically write an envelope so readers never observe a partial JSON file."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_bytes(render_public_envelope(envelope))
    temporary.replace(destination)
    return destination


def _open_json(
    request: Request,
    *,
    opener: Callable[..., Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    try:
        with opener(request, timeout=timeout_seconds) as response:
            payload = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise PublicationError(f"Azure request failed: {exc}") from exc

    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicationError("Azure returned an invalid JSON response") from exc
    return _mapping(decoded, "Azure response")


def acquire_managed_identity_token(
    *,
    client_id: str | None = None,
    opener: Callable[..., Any] = urlopen,
    timeout_seconds: int = 10,
) -> str:
    """Acquire a Storage data-plane token from the Azure Instance Metadata Service."""

    query = {
        "api-version": "2018-02-01",
        "resource": "https://storage.azure.com/",
    }
    if client_id:
        query["client_id"] = client_id

    request = Request(
        f"http://169.254.169.254/metadata/identity/oauth2/token?{urlencode(query)}",
        headers={"Metadata": "true"},
    )
    payload = _open_json(request, opener=opener, timeout_seconds=timeout_seconds)
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise PublicationError("managed identity response did not contain an access token")
    return token


def _validate_blob_destination(
    storage_account: str,
    container: str,
    blob_path: str,
) -> None:
    if not _STORAGE_ACCOUNT_PATTERN.fullmatch(storage_account):
        raise PublicationError(
            "storage_account must be 3-24 lowercase letters or digits"
        )
    if not container or "/" in container or container in {".", ".."}:
        raise PublicationError("container must be a single Azure container name")
    if not blob_path or blob_path.startswith("/") or ".." in blob_path.split("/"):
        raise PublicationError("blob_path must be a relative path without '..'")


def publish_to_azure_blob(
    envelope: dict[str, Any],
    *,
    storage_account: str,
    container: str = DEFAULT_CONTAINER,
    blob_path: str = DEFAULT_BLOB_PATH,
    managed_identity_client_id: str | None = None,
    opener: Callable[..., Any] = urlopen,
    timeout_seconds: int = 20,
    now: datetime | None = None,
) -> str:
    """Upload a public envelope using the VM's managed identity."""

    _validate_blob_destination(storage_account, container, blob_path)
    token = acquire_managed_identity_token(
        client_id=managed_identity_client_id,
        opener=opener,
        timeout_seconds=timeout_seconds,
    )
    container_path = quote(container, safe="$")
    encoded_blob_path = quote(blob_path, safe="/")
    blob_url = (
        f"https://{storage_account}.blob.core.windows.net/"
        f"{container_path}/{encoded_blob_path}"
    )
    request_time = _as_utc(now)
    request = Request(
        blob_url,
        data=render_public_envelope(envelope),
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Cache-Control": "no-store, max-age=0",
            "Content-Type": "application/json; charset=utf-8",
            "x-ms-blob-type": "BlockBlob",
            "x-ms-date": format_datetime(request_time, usegmt=True),
            "x-ms-version": "2023-11-03",
        },
    )
    try:
        with opener(request, timeout=timeout_seconds) as response:
            status = getattr(response, "status", 201)
            if status not in {200, 201}:
                raise PublicationError(
                    f"Azure Blob upload returned unexpected status {status}"
                )
    except (HTTPError, URLError, TimeoutError) as exc:
        raise PublicationError(f"Azure Blob upload failed: {exc}") from exc
    return blob_url
