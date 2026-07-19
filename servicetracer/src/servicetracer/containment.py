"""Load-balancer context and containment verification for ServiceTracer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .analyzer import analyze_incident


def load_json_object(path: str | Path) -> dict[str, Any]:
    """Load a JSON object and reject arrays or scalar values."""
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    return payload


def assess_load_balancer(
    incident_report: dict[str, Any],
    load_balancer_state: dict[str, Any],
) -> dict[str, Any]:
    """Compare shallow backend health with observed end-to-end behaviour."""
    probe = load_balancer_state.get("probe")
    backends = load_balancer_state.get("backends")
    if not isinstance(probe, dict):
        raise ValueError("Load-balancer state must define a probe object")
    if not isinstance(backends, list) or not backends:
        raise ValueError("Load-balancer state must define at least one backend")

    backend_by_id: dict[str, dict[str, Any]] = {}
    for backend in backends:
        if not isinstance(backend, dict) or "backend_id" not in backend:
            raise ValueError("Each load-balancer backend must define backend_id")
        backend_id = str(backend["backend_id"])
        if backend_id in backend_by_id:
            raise ValueError(f"Duplicate load-balancer backend: {backend_id}")
        backend_by_id[backend_id] = backend

    localization = incident_report.get("localization", {})
    candidate = localization.get("candidate_gateway")
    failure_rates = localization.get("gateway_failure_rates", {})
    candidate_backend = backend_by_id.get(str(candidate)) if candidate else None
    candidate_probe_status = (
        str(candidate_backend.get("probe_status")) if candidate_backend else None
    )
    candidate_failure_rate = (
        float(failure_rates.get(candidate, 0.0)) if candidate else 0.0
    )
    probe_gap = bool(
        candidate
        and candidate_backend
        and candidate_probe_status == "healthy"
        and candidate_failure_rate > 0
    )

    probe_scope = str(probe.get("scope", "unspecified"))
    explanation: str
    if probe_gap:
        explanation = (
            f"{candidate} remained healthy under the {probe_scope} probe while "
            f"end-to-end attempts through that backend failed at a rate of "
            f"{candidate_failure_rate:.1%}. The probe confirms only its configured "
            "scope and does not establish that the full remote-access transaction is healthy."
        )
    elif candidate and candidate_backend:
        explanation = (
            f"{candidate} probe state and observed end-to-end behaviour did not show "
            "a shallow-probe mismatch in the supplied evidence."
        )
    else:
        explanation = (
            "No candidate backend could be compared with the supplied load-balancer state."
        )

    return {
        "load_balancer_id": load_balancer_state.get("load_balancer_id"),
        "selection_mode": load_balancer_state.get("selection_mode"),
        "probe": {
            "name": probe.get("name"),
            "protocol": probe.get("protocol"),
            "port": probe.get("port"),
            "scope": probe_scope,
        },
        "backend_states": {
            backend_id: {
                "probe_status": backend.get("probe_status"),
                "administrative_state": backend.get("administrative_state"),
            }
            for backend_id, backend in sorted(backend_by_id.items())
        },
        "candidate_backend": candidate,
        "candidate_probe_status": candidate_probe_status,
        "candidate_end_to_end_failure_rate": round(candidate_failure_rate, 4),
        "shallow_probe_gap_detected": probe_gap,
        "explanation": explanation,
        "recommended_check": (
            "Review backend membership, persistence, probe scope, and whether the probe "
            "represents end-to-end service readiness."
        ),
    }


def build_containment_plan(
    incident_report: dict[str, Any],
    service_path: dict[str, Any],
    containment_attempts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create and optionally verify a node-drain containment plan."""
    localization = incident_report.get("localization", {})
    candidate = localization.get("candidate_gateway")
    healthy_peer = localization.get("healthy_peer")
    if not candidate or not healthy_peer:
        return {
            "status": "not_applicable",
            "reason": "A suspect backend and healthier peer were not both established.",
        }

    verification: dict[str, Any] = {
        "performed": False,
        "classification": None,
        "attempts": 0,
        "successful_attempts": 0,
        "failed_attempts": 0,
        "success_rate": None,
        "observed_gateways": [],
        "suspect_received_new_attempts": None,
        "service_stabilized_under_containment": None,
    }
    status = "recommended"

    if containment_attempts is not None:
        post_report = analyze_incident(containment_attempts, service_path, [])
        observed_gateways = sorted(
            {str(attempt.get("gateway")) for attempt in containment_attempts}
        )
        suspect_seen = str(candidate) in observed_gateways
        post_summary = post_report["summary"]
        stabilized = bool(
            post_summary["classification"] == "healthy_under_test" and not suspect_seen
        )
        verification = {
            "performed": True,
            "classification": post_summary["classification"],
            "attempts": post_summary["attempts"],
            "successful_attempts": post_summary["successful_attempts"],
            "failed_attempts": post_summary["failed_attempts"],
            "success_rate": post_summary["success_rate"],
            "observed_gateways": observed_gateways,
            "suspect_received_new_attempts": suspect_seen,
            "service_stabilized_under_containment": stabilized,
        }
        if stabilized:
            status = "stabilized_under_containment"
        elif suspect_seen:
            status = "drain_not_effective"
        else:
            status = "failures_remain_after_drain"

    return {
        "status": status,
        "suspect_backend": candidate,
        "temporary_healthy_backend": healthy_peer,
        "immediate_action": (
            f"Stop assigning new sessions to {candidate} and route new attempts through "
            f"{healthy_peer} while preserving {candidate} evidence."
        ),
        "active_session_handling": (
            "Existing healthy stateful sessions may remain until they end unless the node "
            "presents a security or stability risk. New sessions should avoid the suspect node."
        ),
        "evidence_to_preserve": [
            "running configuration and approved baseline",
            "load-balancer backend and probe state",
            "VPN syslog and authentication events",
            "SNMP counters and traps",
            "RADIUS/NPS events and timeout evidence",
            "ticket and change history",
        ],
        "verification": verification,
        "return_to_service_gates": [
            f"Compare {candidate} with {healthy_peer} and the approved configuration.",
            f"Correct the identified drift or defect on {candidate}.",
            f"Run direct synthetic transactions against {candidate} outside normal rotation.",
            "Confirm the listener probe and the full remote-access transaction both pass.",
            f"Return {candidate} gradually and repeat end-to-end verification through both nodes.",
        ],
        "remaining_uncertainty": [
            (
                f"Stabilization after draining {candidate} narrows the investigation to that "
                "backend, its unique downstream path, or load-balancer handling specific to it; "
                "it does not by itself identify the exact configuration defect."
            ),
            (
                f"While {candidate} is drained, the containment test does not establish that "
                "the node is ready to return to service."
            ),
        ],
    }
