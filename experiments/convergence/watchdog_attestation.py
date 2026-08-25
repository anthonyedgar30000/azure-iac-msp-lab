#!/usr/bin/env python3
"""Adapt bounded Service Watchdog classifications into local attestations.

This experiment does not import or modify the Service Watchdog project. It
consumes a small explicit bridge record containing fields already represented
by that project's classification/evidence model.
"""

from __future__ import annotations

import math
import re
from typing import Any

VALID = "VALID"
FAULTED = "FAULTED"
UNKNOWN = "UNKNOWN"

_SOURCE_OUTCOMES = {"SATISFIED", "UNSATISFIED", "UNKNOWN", "DISABLED"}
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _number(value: object, name: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or float(value) < 0.0
    ):
        raise ValueError(f"{name} must be a finite non-negative number")
    return float(value)


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _hash(value: object, name: str) -> str:
    text = _string(value, name)
    if _HASH_RE.fullmatch(text) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
    return text


def wrap_watchdog_classification(
    record: dict[str, Any],
    *,
    node_id: str,
    evaluation_time: float,
    max_age_seconds: float,
) -> dict[str, Any]:
    """Create one fail-closed local node attestation.

    The adapter preserves the source classification. Fresh SATISFIED maps to
    VALID, UNSATISFIED maps to FAULTED, and source UNKNOWN maps to UNKNOWN.
    DISABLED also maps to UNKNOWN for a required topology subject because a
    disabled local check cannot establish trust.
    """

    if record.get("schema") != "convergence.watchdog-input.v1":
        raise ValueError("unsupported watchdog bridge schema")
    if record.get("source") != "service-watchdog":
        raise ValueError("unexpected attestation source")

    subject = _string(node_id, "node_id")
    host_id = _string(record.get("host_id"), "host_id")
    config_identity = _hash(record.get("config_identity"), "config_identity")
    target_id = _string(record.get("target_id"), "target_id")
    source_reason = _string(record.get("reason"), "reason")
    evidence_hash = _hash(record.get("evidence_record_hash"), "evidence_record_hash")
    observed_at = _number(record.get("observed_at"), "observed_at")
    evaluated_at = _number(evaluation_time, "evaluation_time")
    max_age = _number(max_age_seconds, "max_age_seconds")

    source_outcome = record.get("outcome")
    if source_outcome not in _SOURCE_OUTCOMES:
        raise ValueError(f"unsupported watchdog outcome: {source_outcome!r}")

    fresh_until = observed_at + max_age
    if not math.isfinite(fresh_until):
        raise ValueError("freshness boundary is not finite")

    if observed_at > evaluated_at:
        status = UNKNOWN
        attestation_reason = "observation_from_future"
    elif evaluated_at > fresh_until:
        status = UNKNOWN
        attestation_reason = "stale_watchdog_classification"
    elif source_outcome == "SATISFIED":
        status = VALID
        attestation_reason = source_reason
    elif source_outcome == "UNSATISFIED":
        status = FAULTED
        attestation_reason = source_reason
    elif source_outcome == "UNKNOWN":
        status = UNKNOWN
        attestation_reason = source_reason
    else:
        status = UNKNOWN
        attestation_reason = "source_target_disabled"

    return {
        "schema": "convergence.local-attestation.v1",
        "subject_kind": "node",
        "subject_id": subject,
        "source": "service-watchdog",
        "host_id": host_id,
        "config_identity": config_identity,
        "target_id": target_id,
        "observed_at": observed_at,
        "evaluated_at": evaluated_at,
        "fresh_until": fresh_until,
        "evidence_record_hash": evidence_hash,
        "source_outcome": source_outcome,
        "source_reason": source_reason,
        "status": status,
        "attestation_reason": attestation_reason,
    }


def as_node_observation(attestation: dict[str, Any]) -> dict[str, str]:
    """Reduce one validated local attestation to the convergence input shape."""

    if attestation.get("schema") != "convergence.local-attestation.v1":
        raise ValueError("unsupported local attestation schema")
    if attestation.get("subject_kind") != "node":
        raise ValueError("attestation is not bound to a node")

    subject_id = _string(attestation.get("subject_id"), "subject_id")
    status = attestation.get("status")
    if status not in {VALID, FAULTED, UNKNOWN}:
        raise ValueError(f"invalid local attestation status: {status!r}")
    return {subject_id: status}
