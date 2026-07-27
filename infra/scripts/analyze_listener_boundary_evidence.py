#!/usr/bin/env python3
"""Analyze read-only Azure listener-boundary evidence without inventing guest state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

EXPECTED_BACKENDS = {
    "VPN-01": "10.20.10.11",
    "VPN-02": "10.20.10.12",
}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def id_name(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.rstrip("/").split("/")[-1]


def pool_addresses(pools: list[dict[str, Any]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for pool in pools:
        name = str(pool.get("name") or "unknown")
        addresses: set[str] = set()
        for address in as_list(pool.get("loadBalancerBackendAddresses")):
            if not isinstance(address, dict):
                continue
            ip = address.get("ipAddress") or address.get("privateIPAddress")
            if isinstance(ip, str) and ip:
                addresses.add(ip)
        result[name] = addresses
    return result


def nic_records(nics: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for nic in nics:
        if not isinstance(nic, dict):
            continue
        for config in as_list(nic.get("ipConfigurations")):
            if not isinstance(config, dict):
                continue
            ip = config.get("privateIPAddress")
            if not isinstance(ip, str) or not ip:
                continue
            records[ip] = {
                "nic_name": nic.get("name"),
                "nic_id": nic.get("id"),
                "vm_name": id_name((nic.get("virtualMachine") or {}).get("id")),
                "subnet_id": (config.get("subnet") or {}).get("id"),
                "nic_nsg_id": (nic.get("networkSecurityGroup") or {}).get("id"),
                "backend_pool_ids": [
                    item.get("id")
                    for item in as_list(config.get("loadBalancerBackendAddressPools"))
                    if isinstance(item, dict) and item.get("id")
                ],
            }
    return records


def subnet_nsg_map(vnets: list[dict[str, Any]]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for vnet in vnets:
        if not isinstance(vnet, dict):
            continue
        for subnet in as_list(vnet.get("subnets")):
            if not isinstance(subnet, dict):
                continue
            subnet_id = subnet.get("id")
            if isinstance(subnet_id, str):
                result[subnet_id] = (subnet.get("networkSecurityGroup") or {}).get("id")
    return result


def metadata_dimensions(series: dict[str, Any]) -> dict[str, str]:
    dimensions: dict[str, str] = {}
    for item in as_list(series.get("metadatavalues")):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, dict):
            name = name.get("value")
        value = item.get("value")
        if isinstance(name, str) and isinstance(value, str):
            dimensions[name] = value
    return dimensions


def latest_probe_metrics(payload: dict[str, Any]) -> dict[str, float | None]:
    by_ip: dict[str, float | None] = {ip: None for ip in EXPECTED_BACKENDS.values()}
    values = as_list(payload.get("value"))
    if not values or not isinstance(values[0], dict):
        return by_ip
    for series in as_list(values[0].get("timeseries")):
        if not isinstance(series, dict):
            continue
        ip = metadata_dimensions(series).get("BackendIPAddress")
        if ip not in by_ip:
            continue
        points = [
            point.get("average")
            for point in as_list(series.get("data"))
            if isinstance(point, dict) and point.get("average") is not None
        ]
        if points:
            by_ip[ip] = float(points[-1])
    return by_ip


def iter_effective_rules(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if "effectiveSecurityRules" in value:
            for rule in as_list(value.get("effectiveSecurityRules")):
                if isinstance(rule, dict):
                    yield rule
        for nested in value.values():
            yield from iter_effective_rules(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_effective_rules(nested)


def port_matches_443(value: str) -> bool:
    value = value.strip()
    if value in {"*", "443"}:
        return True
    if "-" in value:
        start, end = value.split("-", 1)
        try:
            return int(start) <= 443 <= int(end)
        except ValueError:
            return False
    return False


def effective_probe_access(payload: Any) -> dict[str, Any]:
    matching: list[dict[str, Any]] = []
    for rule in iter_effective_rules(payload):
        direction = str(rule.get("direction") or "").lower()
        protocol = str(rule.get("protocol") or "").lower()
        if direction != "inbound" or protocol not in {"tcp", "*", "all"}:
            continue

        sources = []
        if rule.get("sourceAddressPrefix") is not None:
            sources.append(str(rule.get("sourceAddressPrefix")))
        sources.extend(str(item) for item in as_list(rule.get("sourceAddressPrefixes")))
        if not any(source.lower() in {"azureloadbalancer", "*", "any"} for source in sources):
            continue

        ports = []
        if rule.get("destinationPortRange") is not None:
            ports.append(str(rule.get("destinationPortRange")))
        ports.extend(str(item) for item in as_list(rule.get("destinationPortRanges")))
        if not any(port_matches_443(port) for port in ports):
            continue

        try:
            priority = int(rule.get("priority"))
        except (TypeError, ValueError):
            priority = 999999
        matching.append(
            {
                "name": rule.get("name"),
                "access": str(rule.get("access") or "").lower(),
                "priority": priority,
                "source": sources,
                "destination_ports": ports,
            }
        )

    if not matching:
        return {"result": "not_observed", "selected_rule": None}
    matching.sort(key=lambda rule: rule["priority"])
    selected = matching[0]
    return {
        "result": selected["access"] == "allow",
        "selected_rule": selected,
    }


def vm_map(vms: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for vm in vms:
        if isinstance(vm, dict) and isinstance(vm.get("name"), str):
            result[vm["name"]] = vm
    return result


def probe_summary(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": probe.get("name"),
            "protocol": probe.get("protocol"),
            "port": probe.get("port"),
            "interval_seconds": probe.get("intervalInSeconds"),
            "unhealthy_threshold": probe.get("numberOfProbes"),
            "provisioning_state": probe.get("provisioningState"),
        }
        for probe in probes
        if isinstance(probe, dict)
    ]


def rule_summary(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": rule.get("name"),
            "protocol": rule.get("protocol"),
            "frontend_port": rule.get("frontendPort"),
            "backend_port": rule.get("backendPort"),
            "probe_name": id_name((rule.get("probe") or {}).get("id")),
            "backend_pool_name": id_name((rule.get("backendAddressPool") or {}).get("id")),
            "provisioning_state": rule.get("provisioningState"),
        }
        for rule in rules
        if isinstance(rule, dict)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    evidence = args.evidence_dir
    account = load_json(evidence / "account.json", {})
    resource_group = load_json(evidence / "resource-group.json", {})
    load_balancer = load_json(evidence / "load-balancer.json", {})
    probes = as_list(load_json(evidence / "load-balancer-probes.json", []))
    rules = as_list(load_json(evidence / "load-balancer-rules.json", []))
    pools = as_list(load_json(evidence / "load-balancer-pools.json", []))
    nics = as_list(load_json(evidence / "network-interfaces.json", []))
    vnets = as_list(load_json(evidence / "virtual-networks.json", []))
    vms = as_list(load_json(evidence / "virtual-machines.json", []))
    metrics = load_json(evidence / "probe-metrics.json", {})
    effective_nsg = load_json(evidence / "effective-nsg.json", {})
    locks = as_list(load_json(evidence / "resource-locks.json", []))

    pools_by_name = pool_addresses(pools)
    all_pool_ips = {ip for addresses in pools_by_name.values() for ip in addresses}
    nics_by_ip = nic_records(nics)
    subnet_nsgs = subnet_nsg_map(vnets)
    vms_by_name = vm_map(vms)
    metric_by_ip = latest_probe_metrics(metrics)

    backends: dict[str, dict[str, Any]] = {}
    for backend, ip in EXPECTED_BACKENDS.items():
        nic = nics_by_ip.get(ip, {})
        vm_name = nic.get("vm_name")
        vm = vms_by_name.get(vm_name, {}) if isinstance(vm_name, str) else {}
        nic_name = nic.get("nic_name")
        effective_payload = effective_nsg.get(nic_name, {}) if isinstance(effective_nsg, dict) else {}
        access = effective_probe_access(effective_payload)
        latest = metric_by_ip.get(ip)
        backends[backend] = {
            "expected_private_ip": ip,
            "backend_pool_membership_observed": ip in all_pool_ips or bool(nic.get("backend_pool_ids")),
            "nic_name": nic_name,
            "vm_name": vm_name,
            "vm_power_state": vm.get("powerState"),
            "vm_provisioning_state": vm.get("provisioningState"),
            "nic_backend_pool_ids": nic.get("backend_pool_ids", []),
            "nic_nsg_id": nic.get("nic_nsg_id"),
            "subnet_id": nic.get("subnet_id"),
            "subnet_nsg_id": subnet_nsgs.get(nic.get("subnet_id")),
            "effective_azure_load_balancer_tcp_443_access": access,
            "dip_availability_latest": latest,
            "probe_health": (
                "not_observed" if latest is None else "healthy" if latest >= 1 else "unhealthy"
            ),
            "guest_listener_tcp_443": "not_observed",
            "guest_firewall_tcp_443": "not_observed",
        }

    summaries = probe_summary(probes)
    tcp_443_probe_observed = any(
        str(item.get("protocol") or "").lower() == "tcp" and item.get("port") == 443
        for item in summaries
    )
    both_members = all(item["backend_pool_membership_observed"] for item in backends.values())
    both_running = all(item["vm_power_state"] == "VM running" for item in backends.values())
    both_probe_unhealthy = all(item["probe_health"] == "unhealthy" for item in backends.values())
    access_results = [
        item["effective_azure_load_balancer_tcp_443_access"]["result"]
        for item in backends.values()
    ]
    both_nsg_allow = all(result is True for result in access_results)
    any_nsg_deny = any(result is False for result in access_results)

    candidates: list[str] = []
    if not tcp_443_probe_observed:
        candidates.append("load_balancer_probe_not_observed_as_tcp_443")
    if not both_members:
        candidates.append("backend_pool_or_nic_membership_incomplete")
    if not both_running:
        candidates.append("one_or_more_backend_vms_not_observed_running")
    if any_nsg_deny:
        candidates.append("effective_nsg_denies_azure_load_balancer_tcp_443")
    if "not_observed" in access_results:
        candidates.append("effective_nsg_result_not_observed_for_one_or_more_backends")
    if both_probe_unhealthy:
        candidates.append("azure_metrics_confirm_both_backends_probe_unhealthy")
    if tcp_443_probe_observed and both_members and both_running and both_nsg_allow and both_probe_unhealthy:
        candidates.append("guest_listener_or_guest_firewall_requires_separate_guest_evidence")

    conclusion = "configuration_or_guest_boundary_requires_followup"
    if any_nsg_deny:
        conclusion = "network_security_boundary_observed"
    elif not both_members:
        conclusion = "backend_membership_boundary_observed"
    elif not both_running:
        conclusion = "vm_runtime_boundary_observed"
    elif tcp_443_probe_observed and both_members and both_running and both_nsg_allow and both_probe_unhealthy:
        conclusion = "guest_listener_or_guest_firewall_boundary_not_yet_observed"

    result = {
        "schema_version": "servicetracer.listener-boundary-diagnostic.v1",
        "operation": "read_only_diagnostic",
        "azure_mutation_performed": False,
        "guest_command_performed": False,
        "exact_root_cause_claimed": False,
        "subscription_name": account.get("name"),
        "resource_group": resource_group.get("name"),
        "resource_group_location": resource_group.get("location"),
        "resource_locks": len(locks),
        "load_balancer": {
            "name": load_balancer.get("name"),
            "provisioning_state": load_balancer.get("provisioningState"),
            "probes": summaries,
            "rules": rule_summary(rules),
            "backend_pool_addresses": {
                name: sorted(addresses) for name, addresses in pools_by_name.items()
            },
        },
        "backends": backends,
        "diagnosis": {
            "tcp_443_probe_observed": tcp_443_probe_observed,
            "both_backend_memberships_observed": both_members,
            "both_vms_observed_running": both_running,
            "both_effective_nsgs_allow_azure_load_balancer_tcp_443": both_nsg_allow,
            "both_probe_metrics_unhealthy": both_probe_unhealthy,
            "candidate_boundaries": candidates,
            "conclusion": conclusion,
            "next_evidence_gate": (
                "separate explicitly authorized guest-level listener and guest-firewall inspection"
                if conclusion == "guest_listener_or_guest_firewall_boundary_not_yet_observed"
                else "repair or further inspect the observed Azure configuration boundary before guest access"
            ),
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Listener-boundary diagnostic",
        "",
        f"- Conclusion: `{conclusion}`",
        f"- Exact root cause claimed: `{str(result['exact_root_cause_claimed']).lower()}`",
        f"- Azure mutation performed: `{str(result['azure_mutation_performed']).lower()}`",
        f"- Guest command performed: `{str(result['guest_command_performed']).lower()}`",
        "",
        "## Backends",
        "",
    ]
    for name, backend in backends.items():
        lines.extend(
            [
                f"### {name}",
                f"- Private IP: `{backend['expected_private_ip']}`",
                f"- Pool membership observed: `{str(backend['backend_pool_membership_observed']).lower()}`",
                f"- VM: `{backend['vm_name']}`",
                f"- Power state: `{backend['vm_power_state']}`",
                f"- Probe health: `{backend['probe_health']}`",
                f"- Effective AzureLoadBalancer → TCP 443: `{backend['effective_azure_load_balancer_tcp_443_access']['result']}`",
                f"- Guest listener TCP 443: `{backend['guest_listener_tcp_443']}`",
                "",
            ]
        )
    lines.extend(["## Candidate boundaries", ""])
    lines.extend(f"- `{item}`" for item in candidates)
    lines.extend(["", f"Next evidence gate: {result['diagnosis']['next_evidence_gate']}", ""])
    args.output_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(result["diagnosis"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
