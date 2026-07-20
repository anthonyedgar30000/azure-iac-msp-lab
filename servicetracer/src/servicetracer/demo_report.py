"""Bounded, user-facing report for the VPN-02 technician handoff demo."""

from __future__ import annotations

from typing import Any


def _workflow_step(
    step_id: str,
    action: str,
    purpose: str,
    success_criteria: str,
) -> dict[str, str]:
    return {
        "step_id": step_id,
        "owner": "technician",
        "status": "pending",
        "action": action,
        "purpose": purpose,
        "success_criteria": success_criteria,
    }


def build_technician_handoff(
    incident_report: dict[str, Any],
    load_balancer_assessment: dict[str, Any],
    containment_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the deliberately narrow report used by the portfolio demo.

    ServiceTracer establishes that the configured load-balancer probe is healthy,
    identifies the backend associated with failed sessions, and hands the case to
    a technician. It does not expose deeper analyzer stages or claim the exact
    configuration defect.
    """

    localization = incident_report.get("localization", {})
    summary = incident_report.get("summary", {})
    suspect_backend = localization.get("candidate_gateway")
    healthy_backend = localization.get("healthy_peer")

    if not suspect_backend or not healthy_backend:
        return {
            "scenario": "intermittent_remote_access",
            "status": "insufficient_evidence",
            "service_tracer_finding": (
                "ServiceTracer could not establish both an affected backend and a "
                "healthier comparison backend from the supplied evidence."
            ),
            "root_cause": {
                "status": "not_determined",
                "owner": "technician",
            },
        }

    probe = load_balancer_assessment.get("probe", {})
    backend_states = load_balancer_assessment.get("backend_states", {})
    probe_gap = bool(load_balancer_assessment.get("shallow_probe_gap_detected"))
    suspect_probe_status = load_balancer_assessment.get("candidate_probe_status")
    failure_rates = localization.get("gateway_failure_rates", {})

    workflow = [
        _workflow_step(
            "temporary-user-reroute",
            f"Temporarily route the affected user through {healthy_backend}.",
            (
                "Restore access and determine whether the failure follows the user "
                f"or remains associated with {suspect_backend}."
            ),
            (
                f"The affected user completes the remote-access transaction through "
                f"{healthy_backend}."
            ),
        ),
        _workflow_step(
            "manual-backend-troubleshooting",
            f"Review {suspect_backend} manually and correct the suspect VPN profile or configuration.",
            (
                "Perform device-specific troubleshooting outside ServiceTracer's "
                "bounded localization role."
            ),
            "A specific configuration difference is identified, corrected, and recorded.",
        ),
        _workflow_step(
            "controlled-test-user-validation",
            f"Test {suspect_backend} directly with a dedicated test user before normal routing resumes.",
            "Validate the repair without exposing the original user to an unverified backend.",
            f"The test user completes the full remote-access transaction through {suspect_backend}.",
        ),
        _workflow_step(
            "original-user-return",
            f"Return the original user to {suspect_backend} and repeat the connection test.",
            "Confirm production service for the originally affected user after controlled validation.",
            f"The original user connects successfully through {suspect_backend}.",
        ),
    ]

    containment_status = None
    if containment_plan:
        containment_status = containment_plan.get("status")

    return {
        "scenario": "intermittent_remote_access",
        "status": "technician_investigation_required",
        "incident": {
            "classification": summary.get("classification"),
            "attempts": summary.get("attempts"),
            "successful_attempts": summary.get("successful_attempts"),
            "failed_attempts": summary.get("failed_attempts"),
        },
        "load_balancer": {
            "status": "healthy_under_configured_probe",
            "probe_name": probe.get("name"),
            "probe_scope": probe.get("scope"),
            "backend_states": backend_states,
            "probe_gap_detected": probe_gap,
        },
        "localization": {
            "suspect_backend": suspect_backend,
            "healthy_comparison_backend": healthy_backend,
            "suspect_probe_status": suspect_probe_status,
            "backend_failure_rates": failure_rates,
        },
        "service_tracer_finding": (
            f"The configured load-balancer probe is healthy, but failed remote-access "
            f"sessions are concentrated on {suspect_backend}. Continue the investigation "
            f"on {suspect_backend}; {healthy_backend} is the comparison and temporary "
            "service path."
        ),
        "investigation_boundary": {
            "service_tracer_stops_at": suspect_backend,
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
        "temporary_service_status": containment_status,
        "technician_workflow": workflow,
    }
