#!/usr/bin/env python3
"""Deterministically analyze post-UFW-change guest, probe, and transaction evidence."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any


VM_NAMES = ("vm-vpn01-mst-dev", "vm-vpn02-mst-dev")
BACKEND_IPS = ("10.20.10.11", "10.20.10.12")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run_command_text(path: Path) -> str:
    payload = load_json(path)
    messages: list[str] = []
    if isinstance(payload, dict):
        values = payload.get("value", [])
        if isinstance(values, list):
            for item in values:
                if isinstance(item, dict) and isinstance(item.get("message"), str):
                    messages.append(item["message"])
        if isinstance(payload.get("message"), str):
            messages.append(payload["message"])
    return "\n".join(messages)


def section(text: str, name: str) -> str:
    marker = f"=== {name} ==="
    start = text.find(marker)
    if start < 0:
        return ""
    start += len(marker)
    end = text.find("=== ", start)
    return text[start:] if end < 0 else text[start:end]


def parse_guest(path: Path) -> dict[str, Any]:
    text = run_command_text(path)
    ufw = section(text, "UFW")
    listener = section(text, "TCP_443_LISTENER")
    active = section(text, "SYSTEMD_ACTIVE")
    enabled = section(text, "SYSTEMD_ENABLED")

    ufw_state = "not_observed"
    if re.search(r"(?im)^Status:\s*active\s*$", ufw):
        ufw_state = "active"
    elif re.search(r"(?im)^Status:\s*inactive\s*$", ufw):
        ufw_state = "inactive"

    allow_rules = [
        line.strip()
        for line in ufw.splitlines()
        if "443" in line and re.search(r"\bALLOW\b", line, re.IGNORECASE)
    ]
    listener_observed = bool(
        re.search(r"(?:0\.0\.0\.0|\*|\[::\]|:::):443\b", listener)
        or re.search(r"\b:443\b", listener)
    )

    def first_state(value: str, accepted: set[str]) -> str:
        for line in value.splitlines():
            normalized = line.strip().lower()
            if normalized in accepted:
                return normalized
        return "not_observed"

    return {
        "command_evidence": "observed" if text else "not_observed",
        "ufw_state": ufw_state,
        "tcp_443_allow_rule_observed": bool(allow_rules),
        "tcp_443_allow_rules": allow_rules,
        "systemd_active_state": first_state(active, {"active", "inactive", "failed", "activating"}),
        "systemd_enabled_state": first_state(enabled, {"enabled", "disabled", "static", "masked"}),
        "tcp_443_listener_observed": listener_observed,
    }


def latest_probe_values(payload: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(payload, dict):
        return result
    for metric in payload.get("value", []):
        if not isinstance(metric, dict):
            continue
        for series in metric.get("timeseries", []):
            if not isinstance(series, dict):
                continue
            metadata: dict[str, str] = {}
            for item in series.get("metadatavalues", []):
                if not isinstance(item, dict):
                    continue
                name = item.get("name", {})
                key = name.get("value") if isinstance(name, dict) else None
                if isinstance(key, str):
                    metadata[key] = str(item.get("value", ""))
            ip = metadata.get("BackendIPAddress")
            if ip not in BACKEND_IPS:
                continue
            points = [
                point
                for point in series.get("data", [])
                if isinstance(point, dict) and point.get("average") is not None
            ]
            if not points:
                result[ip] = {"average": None, "timestamp": None}
                continue
            latest = max(points, key=lambda point: str(point.get("timeStamp", "")))
            result[ip] = {
                "average": latest.get("average"),
                "timestamp": latest.get("timeStamp"),
            }
    return result


def analyze_transactions(payload: Any) -> dict[str, Any]:
    rows = payload if isinstance(payload, list) else []
    http_codes = Counter(str(row.get("http_code", "unknown")) for row in rows if isinstance(row, dict))
    backends = Counter()
    statuses = Counter()
    boundaries = Counter()
    vpn01_success = False
    vpn02_radius_failure = False

    for row in rows:
        if not isinstance(row, dict):
            continue
        response = row.get("response")
        if not isinstance(response, dict):
            continue
        backend = str(response.get("backend", "unknown"))
        status = str(response.get("transaction_status", "unknown"))
        boundary = str(response.get("failure_boundary", "none"))
        backends[backend] += 1
        statuses[status] += 1
        boundaries[boundary] += 1
        vpn01_success = vpn01_success or (backend == "VPN-01" and status == "successful")
        vpn02_radius_failure = vpn02_radius_failure or (
            backend == "VPN-02" and status == "failed" and boundary == "radius_response"
        )

    return {
        "attempts_observed": len(rows),
        "http_code_counts": dict(sorted(http_codes.items())),
        "backend_counts": dict(sorted(backends.items())),
        "transaction_status_counts": dict(sorted(statuses.items())),
        "failure_boundary_counts": dict(sorted(boundaries.items())),
        "vpn01_success_observed": vpn01_success,
        "vpn02_radius_failure_observed": vpn02_radius_failure,
        "intended_scenario_observed": vpn01_success and vpn02_radius_failure,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    guests = {
        vm: parse_guest(args.evidence_dir / f"{vm}-run-command.json")
        for vm in VM_NAMES
    }
    probe_values = latest_probe_values(load_json(args.evidence_dir / "probe-metrics-final.json"))
    transactions = analyze_transactions(load_json(args.evidence_dir / "transactions.json"))

    both_ufw_active = all(item["ufw_state"] == "active" for item in guests.values())
    both_allow_443 = all(item["tcp_443_allow_rule_observed"] for item in guests.values())
    both_listeners = all(item["tcp_443_listener_observed"] for item in guests.values())
    both_services_active = all(item["systemd_active_state"] == "active" for item in guests.values())
    both_probe_healthy = all(
        ip in probe_values
        and isinstance(probe_values[ip].get("average"), (int, float))
        and float(probe_values[ip]["average"]) > 0.0
        for ip in BACKEND_IPS
    )

    if (
        both_ufw_active
        and both_allow_443
        and both_listeners
        and both_services_active
        and both_probe_healthy
        and transactions["intended_scenario_observed"]
    ):
        conclusion = "probe_recovered_after_ufw_change_and_scenario_verified"
    elif both_probe_healthy:
        conclusion = "probe_recovered_but_transaction_scenario_incomplete"
    elif both_ufw_active and both_allow_443 and both_listeners and both_services_active:
        conclusion = "probe_still_unhealthy_despite_observed_guest_readiness"
    else:
        conclusion = "postchange_state_incomplete"

    result = {
        "schema_version": "servicetracer.ufw-probe-postchange-verification.v1",
        "conclusion": conclusion,
        "operator_report_verified": both_ufw_active and both_allow_443,
        "both_ufw_active": both_ufw_active,
        "both_tcp_443_allow_rules_observed": both_allow_443,
        "both_services_active": both_services_active,
        "both_tcp_443_listeners_observed": both_listeners,
        "both_azure_probes_healthy": both_probe_healthy,
        "virtual_machines": guests,
        "probe_values": probe_values,
        "transactions": transactions,
        "causal_attribution_supported": False,
        "exact_root_cause_claimed": False,
        "azure_mutation_performed": False,
        "guest_mutation_performed": False,
        "service_restart_performed": False,
        "automatic_retry_performed": False,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(
        "# UFW and Azure probe post-change verification\n\n"
        f"- conclusion: `{conclusion}`\n"
        f"- both UFW active: `{both_ufw_active}`\n"
        f"- both TCP 443 allow rules observed: `{both_allow_443}`\n"
        f"- both TCP 443 listeners observed: `{both_listeners}`\n"
        f"- both Azure probes healthy: `{both_probe_healthy}`\n"
        f"- intended transaction scenario observed: `{transactions['intended_scenario_observed']}`\n"
        "- causal attribution supported: `false`\n"
        "- exact root cause claimed: `false`\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
