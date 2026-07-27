#!/usr/bin/env python3
"""Deterministically summarize bounded VPN backend guest-inspection evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VMS = ("vm-vpn01-mst-dev", "vm-vpn02-mst-dev")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def command_text(payload: dict[str, Any]) -> str:
    values = payload.get("value")
    if not isinstance(values, list):
        return ""
    messages: list[str] = []
    for item in values:
        if isinstance(item, dict) and isinstance(item.get("message"), str):
            messages.append(item["message"])
    return "\n".join(messages)


def between(text: str, start: str, end: str) -> str:
    if start not in text:
        return ""
    tail = text.split(start, 1)[1]
    return tail.split(end, 1)[0] if end in tail else tail


def contains_line(section: str, value: str) -> bool:
    return any(line.strip() == value for line in section.splitlines())


def analyze_vm(text: str) -> dict[str, Any]:
    cloud = between(text, "=== CLOUD_INIT ===", "=== SYSTEMD_SHOW ===")
    show = between(text, "=== SYSTEMD_SHOW ===", "=== SYSTEMD_STATUS ===")
    status = between(text, "=== SYSTEMD_STATUS ===", "=== SYSTEMD_ACTIVE ===")
    active = between(text, "=== SYSTEMD_ACTIVE ===", "=== SYSTEMD_ENABLED ===")
    enabled = between(text, "=== SYSTEMD_ENABLED ===", "=== TCP_443_LISTENER ===")
    listener = between(text, "=== TCP_443_LISTENER ===", "=== JOURNAL ===")
    journal = between(text, "=== JOURNAL ===", "=== UFW ===")
    ufw = between(text, "=== UFW ===", "=== END ===")

    active_state = "not_observed"
    for candidate in ("active", "inactive", "failed", "activating", "deactivating", "unknown"):
        if contains_line(active, candidate):
            active_state = candidate
            break

    enabled_state = "not_observed"
    for candidate in ("enabled", "disabled", "static", "masked", "indirect", "generated", "transient"):
        if contains_line(enabled, candidate):
            enabled_state = candidate
            break

    cloud_state = "not_observed"
    lowered_cloud = cloud.lower()
    if "status: done" in lowered_cloud:
        cloud_state = "done"
    elif "status: error" in lowered_cloud:
        cloud_state = "error"
    elif "status: running" in lowered_cloud:
        cloud_state = "running"
    elif "status:" in lowered_cloud:
        cloud_state = "other"

    listener_observed = any(":443" in line and "LISTEN" in line.upper() for line in listener.splitlines())

    ufw_state = "not_observed"
    lowered_ufw = ufw.lower()
    if "status: active" in lowered_ufw:
        ufw_state = "active"
    elif "status: inactive" in lowered_ufw:
        ufw_state = "inactive"
    elif "command not found" in lowered_ufw or "not installed" in lowered_ufw:
        ufw_state = "not_installed"

    direct_error_signals: list[str] = []
    signal_map = {
        "certificate_or_key_missing": ("filenotfounderror", "no such file or directory", "backend.crt", "backend.key"),
        "permission_denied": ("permission denied",),
        "address_in_use": ("address already in use",),
        "python_start_failure": ("traceback (most recent call last)",),
        "systemd_unit_not_found": ("could not be found", "unit servicetracer-demo-backend.service not found"),
    }
    lowered_combined = f"{show}\n{status}\n{journal}".lower()
    for label, needles in signal_map.items():
        if all(needle in lowered_combined for needle in needles):
            direct_error_signals.append(label)

    if listener_observed:
        boundary = "tcp_443_listener_observed"
    elif active_state == "failed":
        boundary = "systemd_service_failed"
    elif active_state == "inactive":
        boundary = "systemd_service_inactive"
    elif active_state == "active":
        boundary = "service_active_but_tcp_443_listener_not_observed"
    elif cloud_state == "error":
        boundary = "cloud_init_error"
    else:
        boundary = "guest_listener_state_incomplete"

    return {
        "cloud_init_state": cloud_state,
        "systemd_active_state": active_state,
        "systemd_enabled_state": enabled_state,
        "tcp_443_listener_observed": listener_observed,
        "ufw_state": ufw_state,
        "boundary": boundary,
        "direct_error_signals": direct_error_signals,
        "journal_observed": bool(journal.strip()),
    }


def build_diagnosis(evidence_dir: Path) -> dict[str, Any]:
    vm_results: dict[str, Any] = {}
    for vm in VMS:
        path = evidence_dir / f"{vm}-run-command.json"
        if not path.exists():
            vm_results[vm] = {
                "command_evidence": "not_observed",
                "boundary": "guest_command_result_not_observed",
            }
            continue
        payload = load_json(path)
        text = command_text(payload)
        vm_results[vm] = {
            "command_evidence": "observed" if text else "empty",
            **analyze_vm(text),
        }

    both_listener_healthy = all(
        vm_results.get(vm, {}).get("tcp_443_listener_observed") is True for vm in VMS
    )
    exact_root_cause_claimed = False
    conclusion = "both_tcp_443_listeners_observed" if both_listener_healthy else "guest_listener_fault_observed"

    return {
        "schema_version": "servicetracer.vpn-backend-guest-inspection.v1",
        "operation": "read_only_guest_inspection",
        "conclusion": conclusion,
        "virtual_machines": vm_results,
        "both_tcp_443_listeners_observed": both_listener_healthy,
        "exact_root_cause_claimed": exact_root_cause_claimed,
        "azure_mutation_performed": False,
        "service_restart_performed": False,
        "guest_firewall_change_performed": False,
        "automatic_retry_performed": False,
    }


def write_markdown(diagnosis: dict[str, Any], path: Path) -> None:
    lines = [
        "# VPN backend guest inspection",
        "",
        f"Conclusion: `{diagnosis['conclusion']}`",
        "",
    ]
    for vm, result in diagnosis["virtual_machines"].items():
        lines.extend(
            [
                f"## {vm}",
                "",
                f"- cloud-init: `{result.get('cloud_init_state', 'not_observed')}`",
                f"- systemd active: `{result.get('systemd_active_state', 'not_observed')}`",
                f"- systemd enabled: `{result.get('systemd_enabled_state', 'not_observed')}`",
                f"- TCP 443 listener observed: `{result.get('tcp_443_listener_observed', False)}`",
                f"- UFW: `{result.get('ufw_state', 'not_observed')}`",
                f"- boundary: `{result.get('boundary', 'not_observed')}`",
                f"- direct error signals: `{result.get('direct_error_signals', [])}`",
                "",
            ]
        )
    lines.extend(
        [
            "No configuration changes, service restarts, firewall changes, deployments, or retries were performed.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    diagnosis = build_diagnosis(args.evidence_dir)
    args.output_json.write_text(json.dumps(diagnosis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(diagnosis, args.output_md)


if __name__ == "__main__":
    main()
