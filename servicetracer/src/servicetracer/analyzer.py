"""Deterministic incident localization for ordered service transactions."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

TERMINAL_FAILURE_STATUSES = {"failed", "timeout", "rejected"}
SUCCESS_STATUS = "success"
NOT_REACHED_STATUS = "not_reached"


@dataclass(frozen=True)
class StageObservation:
    stage_id: str
    status: str
    elapsed_ms: int | None = None
    retries: int = 0
    timeout_ms: int | None = None


@dataclass(frozen=True)
class Attempt:
    attempt_id: str
    started_at: str
    gateway: str
    stages: tuple[StageObservation, ...]


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_attempts(path: str | Path) -> list[dict[str, Any]]:
    """Load JSON Lines transaction attempts."""
    attempts: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                attempts.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
    return attempts


def load_tickets(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON array of operational-history records."""
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Ticket file must contain a JSON array")
    return payload


def _normalize_attempt(raw: dict[str, Any], stage_order: list[str]) -> Attempt:
    required = {"attempt_id", "started_at", "gateway", "stages"}
    missing = sorted(required - raw.keys())
    if missing:
        raise ValueError(f"Attempt is missing required fields: {', '.join(missing)}")

    observations: list[StageObservation] = []
    observed_order: list[str] = []
    for stage in raw["stages"]:
        stage_id = str(stage["stage_id"])
        status = str(stage["status"])
        if status not in TERMINAL_FAILURE_STATUSES | {SUCCESS_STATUS, NOT_REACHED_STATUS}:
            raise ValueError(f"Unsupported stage status: {status}")
        observed_order.append(stage_id)
        observations.append(
            StageObservation(
                stage_id=stage_id,
                status=status,
                elapsed_ms=stage.get("elapsed_ms"),
                retries=int(stage.get("retries", 0)),
                timeout_ms=stage.get("timeout_ms"),
            )
        )

    if observed_order != stage_order:
        raise ValueError(
            f"Attempt {raw['attempt_id']} stage order does not match the service path"
        )

    _parse_datetime(str(raw["started_at"]))
    return Attempt(
        attempt_id=str(raw["attempt_id"]),
        started_at=str(raw["started_at"]),
        gateway=str(raw["gateway"]),
        stages=tuple(observations),
    )


def _first_failure(attempt: Attempt) -> StageObservation | None:
    for stage in attempt.stages:
        if stage.status in TERMINAL_FAILURE_STATUSES:
            return stage
    return None


def _last_success_before_failure(attempt: Attempt) -> StageObservation | None:
    previous: StageObservation | None = None
    for stage in attempt.stages:
        if stage.status in TERMINAL_FAILURE_STATUSES:
            return previous
        if stage.status == SUCCESS_STATUS:
            previous = stage
    return previous


def _not_reached_after_failure(attempt: Attempt) -> list[str]:
    failure_seen = False
    result: list[str] = []
    for stage in attempt.stages:
        if stage.status in TERMINAL_FAILURE_STATUSES:
            failure_seen = True
            continue
        if failure_seen and stage.status == NOT_REACHED_STATUS:
            result.append(stage.stage_id)
    return result


def _layer_assessment(
    attempts: Iterable[Attempt], stage_metadata: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    layer_states: dict[str, Counter[str]] = defaultdict(Counter)
    layer_stages: dict[str, set[str]] = defaultdict(set)

    for attempt in attempts:
        for stage in attempt.stages:
            metadata = stage_metadata[stage.stage_id]
            for layer in metadata["osi_layers"]:
                layer_key = str(layer)
                layer_states[layer_key][stage.status] += 1
                layer_stages[layer_key].add(stage.stage_id)

    result: dict[str, dict[str, Any]] = {}
    for layer in sorted(layer_states, key=int):
        counts = layer_states[layer]
        if sum(counts[status] for status in TERMINAL_FAILURE_STATUSES) > 0:
            state = "failure_observed"
        elif counts[NOT_REACHED_STATUS] and counts[SUCCESS_STATUS]:
            state = "partially_completed_with_downstream_not_reached"
        elif counts[NOT_REACHED_STATUS]:
            state = "not_reached"
        elif counts[SUCCESS_STATUS]:
            state = "observed_healthy_or_completed"
        else:
            state = "no_evidence"
        result[layer] = {
            "state": state,
            "status_counts": dict(sorted(counts.items())),
            "stages": sorted(layer_stages[layer]),
        }
    return result


def _correlate_tickets(
    tickets: list[dict[str, Any]],
    candidate_gateway: str | None,
    failed_stage: str | None,
    incident_start: datetime,
) -> list[dict[str, Any]]:
    if not candidate_gateway or not failed_stage:
        return []

    matches: list[dict[str, Any]] = []
    for ticket in tickets:
        assets = {str(asset) for asset in ticket.get("assets", [])}
        stages = {str(stage) for stage in ticket.get("service_stages", [])}
        if candidate_gateway not in assets or failed_stage not in stages:
            continue

        changed_at = _parse_datetime(str(ticket["changed_at"]))
        age_seconds = (incident_start - changed_at).total_seconds()
        if age_seconds < 0:
            continue
        matches.append(
            {
                "ticket_id": str(ticket["ticket_id"]),
                "summary": str(ticket["summary"]),
                "changed_at": str(ticket["changed_at"]),
                "age_hours": round(age_seconds / 3600, 2),
                "assets": sorted(assets),
                "service_stages": sorted(stages),
                "reason": "same asset and failed service stage",
            }
        )

    return sorted(matches, key=lambda item: item["age_hours"])


def analyze_incident(
    raw_attempts: list[dict[str, Any]],
    service_path: dict[str, Any],
    tickets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Analyze ordered attempts without inferring an unobserved root cause."""
    tickets = tickets or []
    stages = service_path.get("stages", [])
    if not stages:
        raise ValueError("Service path must define at least one stage")

    stage_order = [str(stage["stage_id"]) for stage in stages]
    if len(stage_order) != len(set(stage_order)):
        raise ValueError("Service path stage IDs must be unique")

    stage_metadata = {str(stage["stage_id"]): stage for stage in stages}
    attempts = [_normalize_attempt(raw, stage_order) for raw in raw_attempts]
    if not attempts:
        raise ValueError("At least one attempt is required")

    failures = [attempt for attempt in attempts if _first_failure(attempt)]
    successes = [attempt for attempt in attempts if not _first_failure(attempt)]

    failed_stage_counter = Counter(
        _first_failure(attempt).stage_id for attempt in failures if _first_failure(attempt)
    )
    primary_failed_stage = (
        failed_stage_counter.most_common(1)[0][0] if failed_stage_counter else None
    )

    gateway_totals = Counter(attempt.gateway for attempt in attempts)
    gateway_failures = Counter(attempt.gateway for attempt in failures)
    gateway_rates = {
        gateway: gateway_failures[gateway] / total
        for gateway, total in sorted(gateway_totals.items())
    }

    candidate_gateway: str | None = None
    healthy_peer: str | None = None
    if gateway_rates:
        candidate_gateway = max(gateway_rates, key=gateway_rates.get)
        peers = [gateway for gateway in gateway_rates if gateway != candidate_gateway]
        if peers:
            healthy_peer = min(peers, key=gateway_rates.get)
        if gateway_failures[candidate_gateway] == 0:
            candidate_gateway = None
            healthy_peer = None

    representative_failure = next(
        (
            attempt
            for attempt in failures
            if _first_failure(attempt)
            and _first_failure(attempt).stage_id == primary_failed_stage
            and attempt.gateway == candidate_gateway
        ),
        failures[0] if failures else None,
    )

    last_success = (
        _last_success_before_failure(representative_failure)
        if representative_failure
        else None
    )
    first_failure = _first_failure(representative_failure) if representative_failure else None
    not_reached = (
        _not_reached_after_failure(representative_failure)
        if representative_failure
        else []
    )

    incident_start = min(_parse_datetime(attempt.started_at) for attempt in attempts)
    related_tickets = _correlate_tickets(
        tickets, candidate_gateway, primary_failed_stage, incident_start
    )

    recommendations: list[str] = []
    if candidate_gateway and healthy_peer and gateway_rates[candidate_gateway] > gateway_rates[healthy_peer]:
        recommendations.extend(
            [
                f"Stop assigning new sessions to {candidate_gateway} and route new attempts through {healthy_peer} while preserving evidence.",
                f"Compare {candidate_gateway} with {healthy_peer} and the approved configuration baseline.",
            ]
        )
    if primary_failed_stage == "radius_response":
        recommendations.append(
            "Check the RADIUS destination, route, firewall policy, NPS client registration, shared secret, and timeout/retry evidence."
        )
    if related_tickets:
        recommendations.append(
            f"Review {related_tickets[0]['ticket_id']} as relevant operational history for the same asset and service stage."
        )

    failure_modes = Counter(
        _first_failure(attempt).status for attempt in failures if _first_failure(attempt)
    )
    retry_counts = [
        _first_failure(attempt).retries
        for attempt in failures
        if _first_failure(attempt)
        and _first_failure(attempt).stage_id == primary_failed_stage
    ]
    timeout_values = [
        _first_failure(attempt).timeout_ms
        for attempt in failures
        if _first_failure(attempt)
        and _first_failure(attempt).stage_id == primary_failed_stage
        and _first_failure(attempt).timeout_ms is not None
    ]

    summary = {
        "attempts": len(attempts),
        "successful_attempts": len(successes),
        "failed_attempts": len(failures),
        "success_rate": round(len(successes) / len(attempts), 4),
        "classification": (
            "intermittent_failure"
            if failures and successes
            else "unavailable"
            if failures
            else "healthy_under_test"
        ),
    }

    localization = {
        "candidate_gateway": candidate_gateway,
        "healthy_peer": healthy_peer,
        "gateway_attempts": dict(sorted(gateway_totals.items())),
        "gateway_failures": dict(sorted(gateway_failures.items())),
        "gateway_failure_rates": {
            gateway: round(rate, 4) for gateway, rate in gateway_rates.items()
        },
        "last_successful_stage": last_success.stage_id if last_success else None,
        "first_failed_stage": first_failure.stage_id if first_failure else None,
        "failure_modes": dict(sorted(failure_modes.items())),
        "representative_retries": max(retry_counts) if retry_counts else 0,
        "representative_timeout_ms": max(timeout_values) if timeout_values else None,
        "not_reached": not_reached,
    }

    statement = _render_statement(summary, localization)

    return {
        "service_path_id": service_path.get("service_path_id"),
        "summary": summary,
        "localization": localization,
        "osi_layer_assessment": _layer_assessment(attempts, stage_metadata),
        "related_operational_history": related_tickets,
        "recommendations": recommendations,
        "statement": statement,
        "remaining_uncertainty": [
            "The observed association does not by itself establish the underlying configuration defect.",
            "The failed node or its unique downstream path may contain the fault.",
            "Azure-hosted evidence does not directly reproduce physical cabling or traditional Ethernet switching behaviour.",
        ],
    }


def _render_statement(summary: dict[str, Any], localization: dict[str, Any]) -> str:
    if summary["classification"] == "healthy_under_test":
        return "All observed remote-access attempts completed successfully under the tested conditions."

    candidate = localization["candidate_gateway"] or "an unresolved backend"
    failed_stage = localization["first_failed_stage"] or "an unresolved stage"
    last_success = localization["last_successful_stage"] or "no confirmed prior stage"
    not_reached = localization["not_reached"]
    not_reached_text = ", ".join(not_reached) if not_reached else "no later stages"
    classification_text = {
        "intermittent_failure": "intermittently failing",
        "unavailable": "unavailable",
    }.get(summary["classification"], summary["classification"].replace("_", " "))

    return (
        f"Remote access is {classification_text}. "
        f"{summary['failed_attempts']} of {summary['attempts']} attempts failed. "
        f"Failures were concentrated on {candidate}. The last successful stage was "
        f"{last_success}; the first failed stage was {failed_stage}. "
        f"The failed attempts did not reach: {not_reached_text}."
    )
