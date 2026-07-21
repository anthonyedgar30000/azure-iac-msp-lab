"""Collect bounded live evidence from the Azure probe-scope demonstration.

The public Azure Load Balancer and backend VMs are real Azure resources. The
backend application models a remote-access transaction so the demo can prove a
listener-only TCP probe is narrower than the complete user transaction.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

PUBLIC_SCHEMA = "servicetracer.azure-demo-response.v1"
BACKENDS = ("VPN-01", "VPN-02")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _read_json_response(
    url: str,
    *,
    timeout_seconds: float,
) -> tuple[int, dict[str, str], dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Connection": "close",
            "User-Agent": "ServiceTracer-Azure-Demo/1.0",
        },
    )
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        response = urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
            context=context,
        )
        status = response.status
    except urllib.error.HTTPError as error:
        response = error
        status = error.code

    with response:
        body = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}

    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Azure demo backend returned a non-object JSON payload")
    return status, headers, payload


def collect_transactions(
    frontend_url: str,
    *,
    attempts: int = 30,
    timeout_seconds: float = 20.0,
    pause_seconds: float = 0.15,
) -> list[dict[str, Any]]:
    """Run distinct HTTPS flows until both Azure backend VMs are observed."""

    if attempts < 2:
        raise ValueError("attempts must be at least 2")

    base_url = frontend_url.rstrip("/")
    observed: list[dict[str, Any]] = []
    observed_backends: set[str] = set()

    for attempt_number in range(1, attempts + 1):
        correlation_id = f"AZURE-{_utc_now().strftime('%Y%m%dT%H%M%S')}-{attempt_number:03d}"
        query = urllib.parse.urlencode({"correlation_id": correlation_id})
        started_at = _utc_now()
        status, headers, payload = _read_json_response(
            f"{base_url}/transaction?{query}",
            timeout_seconds=timeout_seconds,
        )
        finished_at = _utc_now()

        if payload.get("schema_version") != PUBLIC_SCHEMA:
            raise ValueError("Azure demo backend returned an unsupported schema")
        backend = payload.get("backend")
        if backend not in BACKENDS:
            raise ValueError(f"Azure demo backend identity is invalid: {backend!r}")
        if payload.get("correlation_id") != correlation_id:
            raise ValueError("Azure demo backend changed the correlation identity")
        if headers.get("x-servicetracer-backend") != backend:
            raise ValueError("Azure demo backend header and body identity disagree")
        if not isinstance(payload.get("stages"), list) or not payload["stages"]:
            raise ValueError("Azure demo backend returned no transaction stages")

        result = {
            "attempt_number": attempt_number,
            "correlation_id": correlation_id,
            "started_at": _format_timestamp(started_at),
            "finished_at": _format_timestamp(finished_at),
            "http_status": status,
            "elapsed_ms": max(1, int((finished_at - started_at).total_seconds() * 1000)),
            "backend": backend,
            "payload": payload,
        }
        observed.append(result)
        observed_backends.add(backend)

        if observed_backends == set(BACKENDS):
            break
        if pause_seconds:
            time.sleep(pause_seconds)

    if observed_backends != set(BACKENDS):
        raise RuntimeError(
            "The live test did not observe both VPN-01 and VPN-02 through the load balancer"
        )
    return observed


def _load_probe_status(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("probe status file must contain a JSON object")
    normalized: dict[str, str] = {}
    for backend in BACKENDS:
        value = payload.get(backend)
        if value not in {"healthy", "unhealthy", "unknown"}:
            raise ValueError(f"probe status for {backend} is invalid: {value!r}")
        normalized[backend] = value
    return normalized


def _stage_record(
    *,
    transaction: dict[str, Any],
    stage: dict[str, Any],
    event_index: int,
    timestamp: datetime,
) -> dict[str, Any]:
    backend = transaction["backend"]
    correlation_id = transaction["correlation_id"]
    source_type = stage.get("source_type")
    event = stage.get("event")
    if source_type not in {"vpn_syslog", "nps_windows", "synthetic_probe"}:
        raise ValueError(f"unsupported stage source type: {source_type!r}")
    if not isinstance(event, str) or not event:
        raise ValueError("stage event must be a non-empty string")

    record: dict[str, Any] = {
        "source_type": source_type,
        "event_id": f"{correlation_id}-{event_index:02d}",
        "timestamp": _format_timestamp(timestamp),
        "event": event,
        "elapsed_ms": int(stage.get("elapsed_ms", 0)),
    }
    if source_type == "vpn_syslog":
        record.update({"device": backend, "session_id": correlation_id})
    elif source_type == "nps_windows":
        record.update(
            {
                "computer": "NPS-01" if event == "radius_access_accept" else "DC-01",
                "gateway": backend,
                "transaction_id": correlation_id,
            }
        )
    else:
        record.update(
            {
                "probe_id": "AZURE-LIVE-PROBE",
                "target": "remote-access-demo",
                "gateway": backend,
                "transaction_id": correlation_id,
            }
        )

    for optional_field in ("retries", "timeout_ms"):
        if optional_field in stage:
            record[optional_field] = stage[optional_field]
    return record


def build_source_records(
    transactions: Iterable[dict[str, Any]],
    probe_status: dict[str, str],
    *,
    load_balancer_id: str = "LB-REMOTE-AZURE",
) -> list[dict[str, Any]]:
    """Convert observed Azure flows into the existing source-adapter contract."""

    transaction_list = list(transactions)
    if not transaction_list:
        raise ValueError("at least one live transaction is required")

    records: list[dict[str, Any]] = []
    context_time = _utc_now()
    for index, backend in enumerate(BACKENDS, start=1):
        status = probe_status.get(backend)
        if status not in {"healthy", "unhealthy", "unknown"}:
            raise ValueError(f"probe status for {backend} is invalid: {status!r}")
        records.append(
            {
                "source_type": "azure_load_balancer",
                "event_id": f"LB-LIVE-STATE-{index:02d}",
                "timestamp": _format_timestamp(context_time + timedelta(milliseconds=index)),
                "load_balancer_id": load_balancer_id,
                "backend_id": backend,
                "event": "backend_probe_state",
                "selection_mode": "five_tuple",
                "probe": {
                    "name": "tcp-443-shallow",
                    "protocol": "tcp",
                    "port": 443,
                    "scope": "listener_only",
                },
                "probe_status": status,
                "administrative_state": "active",
            }
        )

    for transaction in transaction_list:
        correlation_id = transaction["correlation_id"]
        backend = transaction["backend"]
        timestamp = datetime.fromisoformat(
            transaction["started_at"].replace("Z", "+00:00")
        )
        records.extend(
            [
                {
                    "source_type": "synthetic_probe",
                    "event_id": f"{correlation_id}-01",
                    "timestamp": _format_timestamp(timestamp),
                    "probe_id": "AZURE-LIVE-PROBE",
                    "target": "remote-access-demo",
                    "gateway": backend,
                    "transaction_id": correlation_id,
                    "event": "public_dns_resolved",
                    "elapsed_ms": 1,
                },
                {
                    "source_type": "azure_load_balancer",
                    "event_id": f"{correlation_id}-02",
                    "timestamp": _format_timestamp(timestamp + timedelta(milliseconds=1)),
                    "load_balancer_id": load_balancer_id,
                    "backend_id": backend,
                    "transaction_id": correlation_id,
                    "event": "backend_selected",
                    "elapsed_ms": 1,
                },
            ]
        )

        stage_time = timestamp + timedelta(milliseconds=2)
        for event_index, stage in enumerate(transaction["payload"]["stages"], start=3):
            records.append(
                _stage_record(
                    transaction=transaction,
                    stage=stage,
                    event_index=event_index,
                    timestamp=stage_time,
                )
            )
            stage_time += timedelta(milliseconds=max(1, int(stage.get("elapsed_ms", 1))))

    return records


def write_jsonl(records: Iterable[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, separators=(",", ":"), sort_keys=True))
            stream.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect live Azure load-balancer and backend evidence"
    )
    parser.add_argument("--frontend-url", required=True)
    parser.add_argument("--probe-status", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-output", type=Path, required=True)
    parser.add_argument("--attempts", type=int, default=30)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--load-balancer-id", default="LB-REMOTE-AZURE")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        probe_status = _load_probe_status(args.probe_status)
        transactions = collect_transactions(
            args.frontend_url,
            attempts=args.attempts,
            timeout_seconds=args.timeout_seconds,
        )
        records = build_source_records(
            transactions,
            probe_status,
            load_balancer_id=args.load_balancer_id,
        )
        write_jsonl(records, args.output)
        args.raw_output.parent.mkdir(parents=True, exist_ok=True)
        args.raw_output.write_text(
            json.dumps(transactions, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"azure demo collection failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
