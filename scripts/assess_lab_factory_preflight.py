from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


class AssessmentError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize(value: object) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def _capability(sku: dict[str, Any], name: str) -> str:
    for item in sku.get("capabilities", []):
        if item.get("name") == name:
            return str(item.get("value", ""))
    raise AssessmentError(f"SKU capability {name!r} was not observed")


def _quota_item(items: list[dict[str, Any]], *, family: str) -> dict[str, Any]:
    target = _normalize(family)
    for item in items:
        name = item.get("name", {})
        candidates = (
            name.get("value", ""),
            name.get("localizedValue", ""),
            item.get("displayName", ""),
        )
        if any(_normalize(candidate) == target for candidate in candidates):
            return item
    raise AssessmentError(f"quota entry for VM family {family!r} was not observed")


def _regional_core_item(items: list[dict[str, Any]]) -> dict[str, Any]:
    for item in items:
        name = item.get("name", {})
        values = " ".join(
            str(value)
            for value in (
                name.get("value", ""),
                name.get("localizedValue", ""),
                item.get("displayName", ""),
            )
        ).lower()
        if "total regional vcpu" in values or _normalize(name.get("value", "")) == "cores":
            return item
    raise AssessmentError("total regional vCPU quota was not observed")


def _standard_public_ip_item(items: list[dict[str, Any]]) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for item in items:
        name = item.get("name", {})
        values = " ".join(
            str(value)
            for value in (
                name.get("value", ""),
                name.get("localizedValue", ""),
                item.get("displayName", ""),
            )
        ).lower()
        if "public" in values and "ip" in values:
            matches.append(item)
            if "standard" in values:
                return item
    if len(matches) == 1:
        return matches[0]
    raise AssessmentError("Standard public IPv4 quota was not observed unambiguously")


def assess(
    *,
    sku_inventory: list[dict[str, Any]],
    compute_usage: list[dict[str, Any]],
    network_usage: list[dict[str, Any]],
    retail_prices: dict[str, Any],
    vm_size: str,
    ttl_hours: int,
    cost_ceiling_cad: Decimal,
) -> dict[str, Any]:
    exact = [item for item in sku_inventory if item.get("name") == vm_size]
    unrestricted = [item for item in exact if not item.get("restrictions")]
    if not unrestricted:
        raise AssessmentError(f"{vm_size} is unavailable or restricted in the requested region")

    sku = unrestricted[0]
    family = str(sku.get("family") or "")
    if not family:
        raise AssessmentError("VM family was not reported for the selected SKU")
    vcpus = int(_capability(sku, "vCPUs"))

    family_quota = _quota_item(compute_usage, family=family)
    regional_quota = _regional_core_item(compute_usage)
    public_ip_quota = _standard_public_ip_item(network_usage)

    family_remaining = int(family_quota["limit"]) - int(family_quota["currentValue"])
    regional_remaining = int(regional_quota["limit"]) - int(regional_quota["currentValue"])
    public_ip_remaining = int(public_ip_quota["limit"]) - int(public_ip_quota["currentValue"])

    items = [
        item
        for item in retail_prices.get("Items", [])
        if item.get("armSkuName") == vm_size
        and item.get("currencyCode") == "CAD"
        and item.get("type") == "Consumption"
        and item.get("unitOfMeasure") == "1 Hour"
        and Decimal(str(item.get("retailPrice", "0"))) > 0
        and not item.get("reservationTerm")
    ]
    linux_items = [
        item
        for item in items
        if "windows" not in str(item.get("productName", "")).lower()
        and "windows" not in str(item.get("skuName", "")).lower()
    ]
    candidates = linux_items or items
    if not candidates:
        raise AssessmentError("a CAD hourly retail price was not observed for the selected VM SKU")

    hourly_price = min(Decimal(str(item["retailPrice"])) for item in candidates)
    incidental_allowance = Decimal("1.50")
    estimated = (hourly_price * ttl_hours + incidental_allowance).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    result = {
        "schema_version": "lab-factory.preflight-capacity-and-cost.v1",
        "vm_size": vm_size,
        "vm_family": family,
        "vm_vcpus": vcpus,
        "sku_available": True,
        "family_quota": {
            "current": int(family_quota["currentValue"]),
            "limit": int(family_quota["limit"]),
            "remaining": family_remaining,
            "sufficient": family_remaining >= vcpus,
        },
        "regional_vcpu_quota": {
            "current": int(regional_quota["currentValue"]),
            "limit": int(regional_quota["limit"]),
            "remaining": regional_remaining,
            "sufficient": regional_remaining >= vcpus,
        },
        "standard_public_ip_quota": {
            "current": int(public_ip_quota["currentValue"]),
            "limit": int(public_ip_quota["limit"]),
            "remaining": public_ip_remaining,
            "sufficient": public_ip_remaining >= 1,
        },
        "cost": {
            "currency": "CAD",
            "vm_hourly_retail_price": str(hourly_price),
            "ttl_hours": ttl_hours,
            "incidental_allowance": str(incidental_allowance),
            "estimated_ceiling_basis": str(estimated),
            "accepted_ceiling": str(cost_ceiling_cad),
            "within_ceiling": estimated <= cost_ceiling_cad,
            "boundary": "retail estimate != actual Azure cost",
        },
    }
    result["preflight_capacity_and_cost_passed"] = all(
        (
            result["family_quota"]["sufficient"],
            result["regional_vcpu_quota"]["sufficient"],
            result["standard_public_ip_quota"]["sufficient"],
            result["cost"]["within_ceiling"],
        )
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sku-inventory", type=Path, required=True)
    parser.add_argument("--compute-usage", type=Path, required=True)
    parser.add_argument("--network-usage", type=Path, required=True)
    parser.add_argument("--retail-prices", type=Path, required=True)
    parser.add_argument("--vm-size", required=True)
    parser.add_argument("--ttl-hours", type=int, required=True)
    parser.add_argument("--cost-ceiling-cad", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        result = assess(
            sku_inventory=_load(args.sku_inventory),
            compute_usage=_load(args.compute_usage),
            network_usage=_load(args.network_usage),
            retail_prices=_load(args.retail_prices),
            vm_size=args.vm_size,
            ttl_hours=args.ttl_hours,
            cost_ceiling_cad=Decimal(args.cost_ceiling_cad),
        )
    except (AssessmentError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["preflight_capacity_and_cost_passed"]:
        raise SystemExit("capacity, quota, or cost ceiling preflight failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
