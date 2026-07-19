"""Generate deterministic ServiceTracer demo datasets."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

STAGE_ORDER = [
    "public_dns",
    "load_balancer_selection",
    "tcp_connect",
    "tls_handshake",
    "radius_request",
    "radius_response",
    "vpn_address_assignment",
    "tunnel_established",
    "internal_dns",
    "kerberos_ticket",
    "rdp_session",
]

BASE_ELAPSED_MS = {
    "public_dns": 24,
    "load_balancer_selection": 7,
    "tcp_connect": 82,
    "tls_handshake": 310,
    "radius_request": 12,
    "radius_response": 95,
    "vpn_address_assignment": 140,
    "tunnel_established": 120,
    "internal_dns": 18,
    "kerberos_ticket": 130,
    "rdp_session": 980,
}


def _build_attempt(
    *,
    attempt_id: str,
    started_at: datetime,
    gateway: str,
    fail_at_radius_response: bool,
) -> dict[str, Any]:
    stages: list[dict[str, Any]] = []
    failure_index = STAGE_ORDER.index("radius_response")

    for stage_index, stage_id in enumerate(STAGE_ORDER):
        if fail_at_radius_response and stage_id == "radius_response":
            stages.append(
                {
                    "stage_id": stage_id,
                    "status": "timeout",
                    "elapsed_ms": 15000,
                    "retries": 3,
                    "timeout_ms": 15000,
                }
            )
        elif fail_at_radius_response and stage_index > failure_index:
            stages.append({"stage_id": stage_id, "status": "not_reached"})
        else:
            elapsed = BASE_ELAPSED_MS[stage_id] + (8 if gateway == "VPN-02" else 0)
            stages.append(
                {
                    "stage_id": stage_id,
                    "status": "success",
                    "elapsed_ms": elapsed,
                    "retries": 0,
                }
            )

    return {
        "attempt_id": attempt_id,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "gateway": gateway,
        "stages": stages,
    }


def build_demo_attempts() -> list[dict[str, Any]]:
    """Return 20 attempts: 10 per node, with 9 VPN-02 RADIUS timeouts."""
    base = datetime(2026, 7, 19, 14, 0, tzinfo=timezone.utc)
    attempts: list[dict[str, Any]] = []

    for index in range(20):
        gateway = "VPN-01" if index < 10 else "VPN-02"
        failure = gateway == "VPN-02" and index < 19
        attempts.append(
            _build_attempt(
                attempt_id=f"ATT-{index + 1:03d}",
                started_at=base + timedelta(minutes=index),
                gateway=gateway,
                fail_at_radius_response=failure,
            )
        )

    return attempts


def build_containment_attempts() -> list[dict[str, Any]]:
    """Return 12 successful new-session attempts after VPN-02 is drained."""
    base = datetime(2026, 7, 19, 15, 0, tzinfo=timezone.utc)
    return [
        _build_attempt(
            attempt_id=f"CONTAIN-{index + 1:03d}",
            started_at=base + timedelta(minutes=index),
            gateway="VPN-01",
            fail_at_radius_response=False,
        )
        for index in range(12)
    ]


def write_jsonl(path: str | Path, scenario: str = "incident") -> None:
    if scenario == "incident":
        rows = build_demo_attempts()
    elif scenario == "containment":
        rows = build_containment_attempts()
    else:
        raise ValueError(f"Unsupported scenario: {scenario}")

    Path(path).write_text(
        "\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ServiceTracer demo attempts")
    parser.add_argument("--output", required=True, help="Destination JSONL path")
    parser.add_argument(
        "--scenario",
        choices=("incident", "containment"),
        default="incident",
        help="Dataset to generate",
    )
    args = parser.parse_args()
    write_jsonl(args.output, args.scenario)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
