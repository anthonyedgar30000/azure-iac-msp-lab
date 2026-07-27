#!/usr/bin/env python3
"""Deterministically verify collector demo API evidence, including CRLF headers."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def parse_headers(path: Path) -> dict[str, list[str]]:
    # HTTP headers are ISO-8859-1 bytes. splitlines() safely normalizes CRLF/LF
    # without asking a regex engine to interpret a textual \\r escape.
    text = path.read_bytes().decode("iso-8859-1")
    headers: dict[str, list[str]] = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        name, value = raw_line.split(":", 1)
        headers.setdefault(name.strip().lower(), []).append(value.strip())
    return headers


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--run", dest="run_path", type=Path, required=True)
    parser.add_argument("--headers", type=Path, required=True)
    parser.add_argument("--extension", type=Path, required=True)
    parser.add_argument("--allowed-origin", required=True)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--expected-vm", required=True)
    parser.add_argument("--expected-region", required=True)
    parser.add_argument("--attempts", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    health = load_json(args.health)
    run = load_json(args.run_path)
    extension = load_json(args.extension)
    headers = parse_headers(args.headers)

    require(health.get("status") == "healthy", "public health is not healthy")
    require(
        health.get("schema_version") == "servicetracer.demo-api-health.v1",
        "unexpected health schema",
    )
    require(health.get("backend_target_configured") is True, "backend target is not configured")
    require(health.get("hosting_model") == "collector_vm_systemd", "unexpected hosting model")

    health_host = health.get("azure_host")
    require(isinstance(health_host, dict), "health response has no azure_host object")
    require(health_host.get("verified") is True, "health Azure host is not verified")
    require(health_host.get("vm_name") == args.expected_vm, "health VM identity mismatch")
    require(health_host.get("location") == args.expected_region, "health region mismatch")
    require(health_host.get("source_ref") == args.expected_source, "health source mismatch")

    require(
        extension.get("provisioningState") == "Succeeded",
        "VM extension provisioning state is not Succeeded",
    )
    require(extension.get("forceUpdateTag") == args.expected_source, "extension source tag mismatch")

    require(
        run.get("schema_version") == "servicetracer.demo-api-response.v1",
        "unexpected run response schema",
    )
    transactions = run.get("transactions")
    require(isinstance(transactions, list), "transactions is not a list")
    require(len(transactions) == args.attempts, "transaction count mismatch")

    report = run.get("report")
    require(isinstance(report, dict), "run response has no report object")
    boundary = report.get("investigation_boundary")
    require(isinstance(boundary, dict), "run response has no investigation boundary")
    require(boundary.get("exact_root_cause_claimed") is False, "unsupported exact root cause claimed")

    run_host = run.get("azure_host")
    require(isinstance(run_host, dict), "run response has no azure_host object")
    require(run_host.get("verified") is True, "run Azure host is not verified")
    require(run_host.get("vm_name") == args.expected_vm, "run VM identity mismatch")
    require(run_host.get("location") == args.expected_region, "run region mismatch")
    require(run_host.get("source_ref") == args.expected_source, "run source mismatch")

    origins = headers.get("access-control-allow-origin", [])
    require(origins == [args.allowed_origin], "CORS allow-origin mismatch")
    methods = headers.get("access-control-allow-methods", [])
    require(any("POST" in value.split(", ") for value in methods), "CORS POST method not allowed")

    status_counts = Counter(str(item.get("transaction_status", "unknown")) for item in transactions)
    boundary_counts = Counter(str(item.get("failure_boundary", "none")) for item in transactions)

    result = {
        "schema_version": "servicetracer.collector-demo-api-verification.v2",
        "service_validated": True,
        "tls_verified": True,
        "health_verified": True,
        "azure_host_verified": True,
        "exact_source_verified": True,
        "extension_verified": True,
        "cors_verified": True,
        "cors_parser": "iso_8859_1_splitlines_exact_value",
        "transactions_verified": len(transactions),
        "transaction_status_counts": dict(sorted(status_counts.items())),
        "failure_boundary_counts": dict(sorted(boundary_counts.items())),
        "exact_root_cause_claimed": False,
        "expected_source": args.expected_source,
        "expected_vm": args.expected_vm,
        "expected_region": args.expected_region,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
