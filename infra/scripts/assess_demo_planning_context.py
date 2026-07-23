from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _capability(sku: dict[str, Any], name: str) -> str | None:
    wanted = name.lower()
    for capability in sku.get("capabilities", []):
        if str(capability.get("name", "")).lower() == wanted:
            value = capability.get("value")
            return None if value is None else str(value)
    return None


def _observation_list(payload: Any) -> tuple[list[dict[str, Any]] | None, str]:
    if isinstance(payload, list):
        return payload, "observed"
    if isinstance(payload, dict) and payload.get("status") == "not_observable":
        return None, "not_observable"
    return None, "invalid_evidence"


def _select_sku(
    payload: Any,
    *,
    backend_vm_size: str,
    location: str,
) -> dict[str, Any] | None:
    if not isinstance(payload, list):
        return None
    candidates = [
        item
        for item in payload
        if isinstance(item, dict)
        and item.get("name") == backend_vm_size
        and str(item.get("resourceType", "")).lower() == "virtualmachines"
        and (
            not item.get("locations")
            or location.lower() in {str(value).lower() for value in item.get("locations", [])}
        )
    ]
    unrestricted = [item for item in candidates if not item.get("restrictions")]
    if unrestricted:
        return unrestricted[0]
    return candidates[0] if candidates else None


def _usage_headroom(
    usage: Any,
    *,
    usage_name: str | None,
) -> dict[str, Any]:
    if not isinstance(usage, list) or not usage_name:
        return {"status": "not_observable"}
    target = _normalize(usage_name)
    for item in usage:
        if not isinstance(item, dict):
            continue
        name = item.get("name", {})
        value = name.get("value") if isinstance(name, dict) else None
        localized = name.get("localizedValue") if isinstance(name, dict) else None
        if target not in {_normalize(value), _normalize(localized)}:
            continue
        current = item.get("currentValue")
        limit = item.get("limit")
        if not isinstance(current, (int, float)) or not isinstance(limit, (int, float)):
            return {"status": "invalid_evidence", "name": value or localized}
        return {
            "status": "observed",
            "name": value or localized,
            "current": current,
            "limit": limit,
            "headroom": limit - current,
        }
    return {"status": "not_observable", "requested_name": usage_name}


def _total_core_headroom(usage: Any) -> dict[str, Any]:
    if not isinstance(usage, list):
        return {"status": "not_observable"}
    preferred = []
    fallback = []
    for item in usage:
        if not isinstance(item, dict):
            continue
        name = item.get("name", {})
        value = name.get("value") if isinstance(name, dict) else None
        localized = name.get("localizedValue") if isinstance(name, dict) else None
        normalized = {_normalize(value), _normalize(localized)}
        if "totalregionalvcpus" in normalized or "cores" in normalized:
            preferred.append(item)
        elif any("core" in candidate for candidate in normalized):
            if not any(token in candidate for candidate in normalized for token in ("spot", "lowpriority")):
                fallback.append(item)
    candidates = preferred or fallback
    if not candidates:
        return {"status": "not_observable"}
    item = candidates[0]
    name = item.get("name", {})
    current = item.get("currentValue")
    limit = item.get("limit")
    if not isinstance(current, (int, float)) or not isinstance(limit, (int, float)):
        return {"status": "invalid_evidence"}
    return {
        "status": "observed",
        "name": name.get("value") or name.get("localizedValue"),
        "current": current,
        "limit": limit,
        "headroom": limit - current,
    }


def _select_linux_consumption_price(
    payload: Any,
    *,
    backend_vm_size: str,
    location: str,
) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    items = payload.get("Items", payload.get("items", []))
    if not isinstance(items, list):
        return None
    matches: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        product_name = str(item.get("productName", ""))
        meter_name = str(item.get("meterName", ""))
        meter_type = str(item.get("type", item.get("priceType", "")))
        if item.get("armSkuName") != backend_vm_size:
            continue
        if str(item.get("armRegionName", "")).lower() != location.lower():
            continue
        if meter_type.lower() != "consumption":
            continue
        if item.get("isPrimaryMeterRegion") is False:
            continue
        if "windows" in product_name.lower():
            continue
        if any(token in meter_name.lower() for token in ("spot", "low priority", "lowpriority")):
            continue
        if "hour" not in str(item.get("unitOfMeasure", "")).lower():
            continue
        if not isinstance(item.get("retailPrice"), (int, float)):
            continue
        matches.append(item)
    return min(matches, key=lambda item: float(item["retailPrice"])) if matches else None


def assess_demo_planning_context(
    *,
    azure_context: Any,
    resource_group: Any,
    compute_usage: Any,
    vm_skus: Any,
    policy_assignments: Any,
    role_assignments: Any,
    deny_assignments: Any,
    resource_locks: Any,
    retail_prices: Any,
    resource_group_name: str,
    location: str,
    backend_vm_size: str,
    backend_vm_count: int = 2,
) -> dict[str, Any]:
    blockers: list[str] = []
    limitations: list[str] = []

    subscription_id = azure_context.get("subscriptionId") if isinstance(azure_context, dict) else None
    tenant_id = azure_context.get("tenantId") if isinstance(azure_context, dict) else None
    account_status = "observed" if subscription_id and tenant_id else "invalid_evidence"
    if account_status != "observed":
        blockers.append("subscription_or_tenant_context_missing")

    observed_rg_name = resource_group.get("name") if isinstance(resource_group, dict) else None
    observed_location = resource_group.get("location") if isinstance(resource_group, dict) else None
    resource_group_status = (
        "observed"
        if observed_rg_name == resource_group_name and str(observed_location).lower() == location.lower()
        else "mismatch"
    )
    if resource_group_status != "observed":
        blockers.append("resource_group_or_region_mismatch")

    sku = _select_sku(vm_skus, backend_vm_size=backend_vm_size, location=location)
    restrictions = sku.get("restrictions", []) if sku else []
    sku_available = bool(sku) and not restrictions
    vcpu_value = _capability(sku, "vCPUs") if sku else None
    try:
        vcpus_per_vm = int(float(vcpu_value)) if vcpu_value is not None else None
    except (TypeError, ValueError):
        vcpus_per_vm = None
    family = sku.get("family") if sku else None
    required_vcpus = vcpus_per_vm * backend_vm_count if vcpus_per_vm is not None else None
    if not sku_available:
        blockers.append("backend_vm_sku_unavailable_or_restricted")
    if required_vcpus is None:
        blockers.append("backend_vm_vcpu_capability_not_observable")

    total_quota = _total_core_headroom(compute_usage)
    family_quota = _usage_headroom(compute_usage, usage_name=family)
    total_sufficient = (
        required_vcpus is not None
        and total_quota.get("status") == "observed"
        and total_quota.get("headroom", -1) >= required_vcpus
    )
    family_sufficient = (
        required_vcpus is not None
        and family_quota.get("status") == "observed"
        and family_quota.get("headroom", -1) >= required_vcpus
    )
    if not total_sufficient:
        blockers.append("regional_vcpu_quota_not_proven_sufficient")
    if not family_sufficient:
        blockers.append("vm_family_quota_not_proven_sufficient")

    policies, policy_status = _observation_list(policy_assignments)
    roles, role_status = _observation_list(role_assignments)
    denies, deny_status = _observation_list(deny_assignments)
    locks, lock_status = _observation_list(resource_locks)
    if policy_status != "observed":
        limitations.append("applicable_policy_assignments_not_observable")
    if role_status != "observed":
        limitations.append("workflow_identity_role_assignments_not_observable")
    if deny_status != "observed":
        limitations.append("deny_assignments_not_observable")
    if lock_status != "observed":
        limitations.append("resource_group_locks_not_observable")

    read_only_locks = [
        item for item in (locks or []) if str(item.get("level", "")).lower() == "readonly"
    ]
    cannot_delete_locks = [
        item for item in (locks or []) if str(item.get("level", "")).lower() == "cannotdelete"
    ]
    if read_only_locks:
        blockers.append("read_only_lock_blocks_deployment")
    if cannot_delete_locks:
        limitations.append("cannot_delete_lock_requires_cleanup_review")

    price = _select_linux_consumption_price(
        retail_prices,
        backend_vm_size=backend_vm_size,
        location=location,
    )
    if price:
        hourly_cad_each = round(float(price["retailPrice"]), 8)
        monthly_cad_two_vms = round(hourly_cad_each * 730 * backend_vm_count, 2)
        price_observation = {
            "status": "observed_retail_estimate",
            "currency": price.get("currencyCode"),
            "hourly_rate_each": hourly_cad_each,
            "estimated_730_hour_month_for_all_backends": monthly_cad_two_vms,
            "meter_name": price.get("meterName"),
            "product_name": price.get("productName"),
            "effective_start_date": price.get("effectiveStartDate"),
            "claim_boundary": "Retail pricing is an estimate and excludes usage-based Function, Storage, networking, logging, taxes, credits, discounts, and actual consumption.",
        }
    else:
        price_observation = {"status": "not_observable"}
        limitations.append("current_cad_vm_retail_price_not_observable")

    credit_observation = {
        "status": "not_observable",
        "reason": "The workflow identity does not currently carry a portable, verified remaining-credit evidence path.",
    }
    limitations.append("remaining_subscription_credit_not_observable")

    core_evidence_complete = not blockers
    classification = "verified_with_limitations" if core_evidence_complete else "partially_verified"

    return {
        "schema_version": "servicetracer.demo-planning-context.v1",
        "classification": classification,
        "scope": {
            "resource_group": resource_group_name,
            "location": location,
            "backend_vm_size": backend_vm_size,
            "backend_vm_count": backend_vm_count,
        },
        "account_context": {
            "status": account_status,
            "subscription_id": subscription_id,
            "tenant_id": tenant_id,
        },
        "resource_group": {
            "status": resource_group_status,
            "observed_name": observed_rg_name,
            "observed_location": observed_location,
        },
        "sku": {
            "status": "available" if sku_available else "unavailable_or_restricted",
            "family": family,
            "vcpus_per_vm": vcpus_per_vm,
            "required_vcpus": required_vcpus,
            "restrictions": restrictions,
        },
        "quota": {
            "regional_total": total_quota,
            "vm_family": family_quota,
            "regional_total_sufficient": total_sufficient,
            "vm_family_sufficient": family_sufficient,
        },
        "policy_assignments": {
            "status": policy_status,
            "count": len(policies or []),
            "claim_boundary": "Assignment presence does not prove the effect of policy on the proposed deployment; ARM validation and What-If remain required.",
        },
        "workflow_identity_roles": {
            "status": role_status,
            "count": len(roles or []),
            "roles": sorted(
                {
                    str(item.get("roleDefinitionName"))
                    for item in (roles or [])
                    if item.get("roleDefinitionName")
                }
            ),
            "claim_boundary": "Observed assignments do not prove every effective permission or deny condition.",
        },
        "deny_assignments": {
            "status": deny_status,
            "count": len(denies or []),
        },
        "resource_locks": {
            "status": lock_status,
            "read_only_count": len(read_only_locks),
            "cannot_delete_count": len(cannot_delete_locks),
        },
        "retail_vm_price": price_observation,
        "remaining_subscription_credit": credit_observation,
        "planning_context_complete": core_evidence_complete,
        "deployment_decision_ready": False,
        "azure_mutations_authorized": False,
        "deployment_authorized": False,
        "blockers": sorted(set(blockers)),
        "limitations": sorted(set(limitations)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess read-only Azure planning context for the ServiceTracer demo.")
    parser.add_argument("--azure-context", required=True)
    parser.add_argument("--resource-group-json", required=True)
    parser.add_argument("--compute-usage", required=True)
    parser.add_argument("--vm-skus", required=True)
    parser.add_argument("--policy-assignments", required=True)
    parser.add_argument("--role-assignments", required=True)
    parser.add_argument("--deny-assignments", required=True)
    parser.add_argument("--resource-locks", required=True)
    parser.add_argument("--retail-prices", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--backend-vm-size", required=True)
    parser.add_argument("--backend-vm-count", type=int, default=2)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    assessment = assess_demo_planning_context(
        azure_context=_load_json(args.azure_context),
        resource_group=_load_json(args.resource_group_json),
        compute_usage=_load_json(args.compute_usage),
        vm_skus=_load_json(args.vm_skus),
        policy_assignments=_load_json(args.policy_assignments),
        role_assignments=_load_json(args.role_assignments),
        deny_assignments=_load_json(args.deny_assignments),
        resource_locks=_load_json(args.resource_locks),
        retail_prices=_load_json(args.retail_prices),
        resource_group_name=args.resource_group,
        location=args.location,
        backend_vm_size=args.backend_vm_size,
        backend_vm_count=args.backend_vm_count,
    )
    Path(args.output).write_text(json.dumps(assessment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
