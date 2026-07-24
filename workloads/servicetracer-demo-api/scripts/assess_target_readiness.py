#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _usage_record(records: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for record in records:
        if record.get("name", {}).get("value") == name:
            return record
    return None


def _quota_check(record: dict[str, Any] | None, required: int) -> dict[str, Any]:
    if record is None:
        return {
            "observed": False,
            "current": None,
            "limit": None,
            "required": required,
            "sufficient": False,
        }
    current = _as_int(record.get("currentValue"))
    limit = _as_int(record.get("limit"))
    sufficient = current is not None and limit is not None and current + required <= limit
    return {
        "observed": current is not None and limit is not None,
        "current": current,
        "limit": limit,
        "required": required,
        "sufficient": sufficient,
    }


def classify(
    *,
    vm_size: str,
    provider_compute: dict[str, Any],
    provider_network: dict[str, Any],
    sku_records: list[dict[str, Any]],
    compute_usage: list[dict[str, Any]],
    network_usage: list[dict[str, Any]],
    target_resource_group_state: dict[str, Any],
    existing_target_resources: Any,
) -> dict[str, Any]:
    matching = [record for record in sku_records if record.get("name") == vm_size]
    unrestricted = [record for record in matching if not (record.get("restrictions") or [])]
    selected = matching[0] if matching else {}

    capabilities = {
        item.get("name"): item.get("value")
        for item in selected.get("capabilities", [])
        if isinstance(item, dict)
    }
    required_cores = _as_int(capabilities.get("vCPUs"))
    family = selected.get("family")

    total_quota = _quota_check(_usage_record(compute_usage, "cores"), required_cores or 0)
    family_quota = _quota_check(
        _usage_record(compute_usage, str(family)) if family else None,
        required_cores or 0,
    )
    standard_public_ip_quota = _quota_check(
        _usage_record(network_usage, "IPv4StandardSkuPublicIpAddresses"), 1
    )

    resource_group_status = target_resource_group_state.get("status", "not_observed")
    state_evidence_authoritative = (
        target_resource_group_state.get("evidence_authoritative") is True
    )
    explicit_absence_observed = (
        resource_group_status == "not_present"
        and target_resource_group_state.get("error_code") == "ResourceGroupNotFound"
        and state_evidence_authoritative
    )
    existing_group_observed = (
        resource_group_status == "observed_existing"
        and _as_int(target_resource_group_state.get("group_show_exit_status")) == 0
        and _as_int(target_resource_group_state.get("resource_list_exit_status")) == 0
        and state_evidence_authoritative
    )
    resource_group_observed = explicit_absence_observed or existing_group_observed
    resources_authoritative = isinstance(existing_target_resources, list) and resource_group_observed
    existing_resource_count = (
        len(existing_target_resources) if resources_authoritative else None
    )

    checks = {
        "compute_provider_registered": provider_compute.get("registrationState") == "Registered",
        "network_provider_registered": provider_network.get("registrationState") == "Registered",
        "requested_vm_size_observed": bool(matching),
        "requested_vm_size_unrestricted": bool(unrestricted),
        "requested_vm_size_vcpus_observed": required_cores is not None,
        "total_regional_vcpu_quota_sufficient": total_quota["sufficient"],
        "vm_family_vcpu_quota_sufficient": family_quota["sufficient"],
        "standard_ipv4_public_ip_quota_sufficient": standard_public_ip_quota["sufficient"],
        "target_resource_group_state_observed": resource_group_observed,
        "target_resource_inventory_authoritative": resources_authoritative,
    }

    reason_map = {
        "compute_provider_registered": "compute_provider_not_registered",
        "network_provider_registered": "network_provider_not_registered",
        "requested_vm_size_observed": "requested_vm_size_not_observed",
        "requested_vm_size_unrestricted": "requested_vm_size_restricted_for_subscription",
        "requested_vm_size_vcpus_observed": "requested_vm_size_vcpu_capability_not_observed",
        "total_regional_vcpu_quota_sufficient": "total_regional_vcpu_quota_insufficient",
        "vm_family_vcpu_quota_sufficient": "vm_family_vcpu_quota_insufficient",
        "standard_ipv4_public_ip_quota_sufficient": "standard_ipv4_public_ip_quota_insufficient",
        "target_resource_group_state_observed": "target_resource_group_observation_failed",
        "target_resource_inventory_authoritative": "target_resource_inventory_not_authoritative",
    }
    blocking_reasons = [reason_map[name] for name, passed in checks.items() if not passed]

    return {
        "schema_version": "servicetracer.demo-api-target-readiness.v1",
        "status": "ready_for_arm_what_if" if not blocking_reasons else "blocked_target_readiness",
        "requested_vm_size": vm_size,
        "requested_vm_size_family": family,
        "requested_vcpus": required_cores,
        "checks": checks,
        "blocking_reasons": blocking_reasons,
        "sku": {
            "matching_records": len(matching),
            "unrestricted_records": len(unrestricted),
            "restrictions": [
                restriction
                for record in matching
                for restriction in (record.get("restrictions") or [])
            ],
        },
        "quota": {
            "total_regional_vcpus": total_quota,
            "vm_family_vcpus": family_quota,
            "standard_ipv4_public_ips": standard_public_ip_quota,
        },
        "target_resource_group": {
            "status": resource_group_status,
            "stage": target_resource_group_state.get("stage"),
            "error_code": target_resource_group_state.get("error_code"),
            "group_show_exit_status": target_resource_group_state.get(
                "group_show_exit_status"
            ),
            "resource_list_exit_status": target_resource_group_state.get(
                "resource_list_exit_status"
            ),
            "evidence_authoritative": target_resource_group_state.get(
                "evidence_authoritative", False
            ),
            "resources_authoritative": resources_authoritative,
            "existing_resource_count": existing_resource_count,
        },
        "azure_mutations_authorized": False,
        "azure_mutations_performed": False,
        "deployment_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assess read-only target readiness for the independent demo API planner."
    )
    parser.add_argument("--vm-size", required=True)
    parser.add_argument("--provider-compute", type=Path, required=True)
    parser.add_argument("--provider-network", type=Path, required=True)
    parser.add_argument("--vm-size-availability", type=Path, required=True)
    parser.add_argument("--compute-usage", type=Path, required=True)
    parser.add_argument("--network-usage", type=Path, required=True)
    parser.add_argument("--target-resource-group-state", type=Path, required=True)
    parser.add_argument("--existing-target-resources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    assessment = classify(
        vm_size=args.vm_size,
        provider_compute=_load(args.provider_compute),
        provider_network=_load(args.provider_network),
        sku_records=_load(args.vm_size_availability),
        compute_usage=_load(args.compute_usage),
        network_usage=_load(args.network_usage),
        target_resource_group_state=_load(args.target_resource_group_state),
        existing_target_resources=_load(args.existing_target_resources),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(assessment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(assessment, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
