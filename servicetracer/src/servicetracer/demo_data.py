"""Generate the deterministic twenty-attempt ServiceTracer demo dataset."""

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


def build_demo_attempts() -> list[dict[str, Any]]:
    """Return 20 attempts: 10 via VPN-01 and 10 via VPN-02, with 9 VPN-02 timeouts."""
    base = datetime(2026, 7, 19, 14, 0, tzinfo=timezone.utc)
    attempts: list[dict[str, Any]] = []

    for index in range(20):
        gateway = "VPN-01" if index < 10 else "VPN-02"
        failure = gateway == "VPN-02" and index < 19
        stages: list[dict[str, Any]] = []

        for stage_index, stage_id in enumerate(STAGE_ORDER):
            if failure and stage_id == "radius_response":
                stages.append(
                    {
                        "stage_id": stage_id,
                        "status": "timeout",
                        "elapsed_ms": 15000,
                        "retries": 3,
                        "timeout_ms": 15000,
                    }
                )
            elif failure and stage_index > STAGE_ORDER.index("radius_response"):
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

        attempts.append(
            {
                "attempt_id": f"ATT-{index + 1:03d}",
                "started_at": (base + timedelta(minutes=index))
                .isoformat()
                .replace("+00:00", "Z"),
                "gateway": gateway,
                "stages": stages,
            }
        )

    return attempts


def write_jsonl(path: str | Path) -> None:
    rows = build_demo_attempts()
    Path(path).write_text(
        "\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ServiceTracer demo attempts")
    parser.add_argument("--output", required=True, help="Destination JSONL path")
    args = parser.parse_args()
    write_jsonl(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
