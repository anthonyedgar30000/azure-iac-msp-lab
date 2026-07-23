from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

KNOWN_BACKENDS = ("VPN-01", "VPN-02")
MIN_ATTEMPTS = 2
MAX_ATTEMPTS = 50

TECHNICIAN_WORKFLOW = [
    {
        "step_id": "temporary-user-reroute",
        "owner": "technician",
        "status": "pending",
        "action": "Temporarily route the affected user through VPN-01.",
        "purpose": (
            "Restore access and determine whether the failure follows the user or "
            "remains associated with VPN-02."
        ),
        "success_criteria": (
            "The affected user completes the remote-access transaction through VPN-01."
        ),
    },
    {
        "step_id": "manual-backend-troubleshooting",
        "owner": "technician",
        "status": "pending",
        "action": "Review VPN-02 manually and correct the suspect VPN profile or configuration.",
        "purpose": (
            "Perform device-specific troubleshooting outside ServiceTracer's bounded "
            "localization role."
        ),
        "success_criteria": (
            "A specific configuration difference is identified, corrected, and recorded."
        ),
    },
    {
        "step_id": "controlled-test-user-validation",
        "owner": "technician",
        "status": "pending",
        "action": "Test VPN-02 directly with a dedicated test user before normal routing resumes.",
        "purpose": (
            "Validate the repair without exposing the original user to an unverified backend."
        ),
        "success_criteria": (
            "The test user completes the full remote-access transaction through VPN-02."
        ),
    },
    {
        "step_id": "original-user-return",
        "owner": "technician",
        "status": "pending",
        "action": "Return the original user to VPN-02 and repeat the connection test.",
        "purpose": (
            "Confirm production service for the originally affected user after controlled validation."
        ),
        "success_criteria": "The original user connects successfully through VPN-02.",
    },
]


def normalize_attempts(value: Any, *, default: int = 20) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("attempts must be an integer")
    try:
        attempts = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("attempts must be an integer") from exc
    if attempts < MIN_ATTEMPTS or attempts > MAX_ATTEMPTS:
        raise ValueError(f"attempts must be between {MIN_ATTEMPTS} and {MAX_ATTEMPTS}")
    return attempts


def _failure_rate(total: int, failed: int) -> float | None:
    if total == 0:
        return None
    return round(failed / total, 4)


def build_handoff_report(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    attempts = len(transactions)
    successes = sum(item.get("transaction_status") == "successful" for item in transactions)
    failures = attempts - successes

    totals = Counter(str(item.get("backend") or "UNRESOLVED") for item in transactions)
    failed_by_backend = Counter(
        str(item.get("backend") or "UNRESOLVED")
        for item in transactions
        if item.get("transaction_status") != "successful"
    )

    rates = {
        backend: _failure_rate(totals[backend], failed_by_backend[backend])
        for backend in KNOWN_BACKENDS
    }
    observed_known = [backend for backend in KNOWN_BACKENDS if totals[backend] > 0]
    suspect = max(
        observed_known,
        key=lambda backend: rates[backend] if rates[backend] is not None else -1.0,
        default="UNRESOLVED",
    )
    healthy = min(
        observed_known,
        key=lambda backend: rates[backend] if rates[backend] is not None else 2.0,
        default="UNRESOLVED",
    )

    concentrated = (
        suspect == "VPN-02"
        and healthy == "VPN-01"
        and rates["VPN-02"] is not None
        and rates["VPN-01"] is not None
        and rates["VPN-02"] > rates["VPN-01"]
    )
    if concentrated:
        finding = (
            "The configured load-balancer probe is healthy, but failed remote-access "
            "sessions are concentrated on VPN-02. Continue the investigation on VPN-02; "
            "VPN-01 is the comparison and temporary service path."
        )
        boundary = "VPN-02"
    else:
        finding = (
            "The API completed correlated transactions, but the current sample does not "
            "support a stable backend localization. Repeat the bounded test before making "
            "a backend-specific claim."
        )
        boundary = suspect

    backend_states = {
        backend: {
            "administrative_state": "active",
            "probe_status": "healthy",
            "observed_transactions": totals[backend],
        }
        for backend in KNOWN_BACKENDS
    }

    return {
        "scenario": "intermittent_remote_access",
        "status": "technician_investigation_required",
        "incident": {
            "classification": "intermittent_failure" if failures else "no_failure_observed",
            "attempts": attempts,
            "successful_attempts": successes,
            "failed_attempts": failures,
        },
        "load_balancer": {
            "status": "healthy_under_configured_probe",
            "probe_name": "tcp-443-shallow",
            "probe_scope": "listener-only",
            "backend_states": backend_states,
            "probe_gap_detected": failures > 0,
        },
        "localization": {
            "suspect_backend": suspect,
            "healthy_comparison_backend": healthy,
            "suspect_probe_status": "healthy" if suspect in KNOWN_BACKENDS else "unresolved",
            "backend_failure_rates": rates,
            "backend_attempt_counts": {backend: totals[backend] for backend in KNOWN_BACKENDS},
        },
        "service_tracer_finding": finding,
        "investigation_boundary": {
            "service_tracer_stops_at": boundary,
            "exact_root_cause_claimed": False,
            "statement": (
                "ServiceTracer localizes the incident to the backend investigation boundary. "
                "The technician performs device-specific diagnosis, repair, and validation."
            ),
        },
        "root_cause": {
            "status": "not_determined_by_servicetracer",
            "owner": "technician",
        },
        "temporary_service_status": "stabilized_under_containment",
        "technician_workflow": TECHNICIAN_WORKFLOW,
    }


def build_api_response(transactions: list[dict[str, Any]], *, source: str) -> dict[str, Any]:
    return {
        "schema_version": "servicetracer.demo-api-response.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "id": source,
            "transport": "azure-load-balancer-correlated-transactions",
        },
        "report": build_handoff_report(transactions),
        "transactions": transactions,
    }
