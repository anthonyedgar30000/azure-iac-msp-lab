from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

from lab_factory.azure_preflight import PreflightError, run_lab_preflight


ROOT = Path(__file__).resolve().parents[1]
RETAIL_API = "https://prices.azure.com/api/retail/prices"


def _fetch_pages(filter_expression: str) -> list[dict[str, Any]]:
    url = (
        f"{RETAIL_API}?currencyCode=CAD&$filter="
        f"{quote(filter_expression, safe=\"()'=_\")}"
    )
    items: list[dict[str, Any]] = []
    page_count = 0
    while url:
        page_count += 1
        if page_count > 10:
            raise PreflightError("retail price query exceeded the bounded page limit")
        with urlopen(url, timeout=30) as response:  # nosec B310 - fixed Microsoft endpoint
            payload = json.load(response)
        page_items = payload.get("Items")
        if not isinstance(page_items, list):
            raise PreflightError("retail price API returned an invalid item collection")
        items.extend(item for item in page_items if isinstance(item, dict))
        next_page = payload.get("NextPageLink")
        if next_page and not str(next_page).startswith(RETAIL_API):
            raise PreflightError("retail price API returned an unexpected next-page host")
        url = str(next_page) if next_page else ""
    return items


def _first_consumption_price(
    items: list[dict[str, Any]],
    *,
    unit_contains: str | None = None,
) -> float | None:
    candidates = []
    for item in items:
        if str(item.get("type", item.get("priceType", ""))).lower() not in {
            "consumption",
            "",
        }:
            continue
        unit = str(item.get("unitOfMeasure", ""))
        if unit_contains and unit_contains.lower() not in unit.lower():
            continue
        price = item.get("retailPrice")
        if isinstance(price, (int, float)) and price >= 0:
            candidates.append(float(price))
    return min(candidates) if candidates else None


def retail_price_fetcher(location: str, vm_size: str) -> dict[str, Any]:
    vm_items = _fetch_pages(
        "serviceName eq 'Virtual Machines' "
        f"and armRegionName eq '{location}' "
        f"and armSkuName eq '{vm_size}' "
        "and priceType eq 'Consumption'"
    )
    network_items = _fetch_pages(
        "serviceName eq 'Virtual Network' "
        f"and armRegionName eq '{location}' "
        "and priceType eq 'Consumption'"
    )
    disk_items = _fetch_pages(
        "serviceName eq 'Storage' "
        f"and armRegionName eq '{location}' "
        "and priceType eq 'Consumption'"
    )

    public_ip_candidates = [
        item
        for item in network_items
        if "public ip" in str(item.get("meterName", "")).lower()
        and "standard"
        in (
            str(item.get("skuName", ""))
            + " "
            + str(item.get("productName", ""))
        ).lower()
        and "ipv4"
        in (
            str(item.get("meterName", ""))
            + " "
            + str(item.get("productName", ""))
        ).lower()
    ]
    disk_candidates = [
        item
        for item in disk_items
        if "standard ssd" in str(item.get("productName", "")).lower()
        and "e4"
        in (
            str(item.get("skuName", ""))
            + " "
            + str(item.get("meterName", ""))
        ).lower()
        and "lrs"
        in (
            str(item.get("skuName", ""))
            + " "
            + str(item.get("meterName", ""))
        ).lower()
    ]

    return {
        "vm_hourly_cad": _first_consumption_price(
            vm_items,
            unit_contains="hour",
        ),
        "public_ip_hourly_cad": _first_consumption_price(
            public_ip_candidates,
            unit_contains="hour",
        ),
        "disk_monthly_cad": _first_consumption_price(
            disk_candidates,
            unit_contains="month",
        ),
        "source": "Azure Retail Prices API",
        "currency": "CAD",
    }


def _load_parameters(path: Path) -> dict[str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise PreflightError("parameter file must contain a JSON object")
    parameters: dict[str, str] = {}
    for name, value in document.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise PreflightError("all parameter file entries must be strings")
        parameters[name] = value
    return parameters


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a bounded read-only Azure Lab Factory preflight."
    )
    parser.add_argument("--profile", default="servicetracer-demo-api")
    parser.add_argument(
        "--environment",
        choices=("dev", "test"),
        default="test",
    )
    parser.add_argument("--ttl-hours", type=int, default=8)
    parser.add_argument("--cost-ceiling-cad", type=float, default=5.0)
    parser.add_argument("--request-id")
    parser.add_argument("--parameters-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    subscription_id = os.environ.get(
        "AZURE_LAB_PREFLIGHT_SUBSCRIPTION_ID",
        "",
    )
    if not subscription_id:
        print(
            "AZURE_LAB_PREFLIGHT_SUBSCRIPTION_ID is required",
            file=sys.stderr,
        )
        return 2

    try:
        parameters = _load_parameters(args.parameters_file)
        result = run_lab_preflight(
            expected_subscription_id=subscription_id,
            profile_id=args.profile,
            environment=args.environment,
            ttl_hours=args.ttl_hours,
            cost_ceiling_cad=args.cost_ceiling_cad,
            parameters=parameters,
            repository_root=ROOT,
            price_fetcher=retail_price_fetcher,
            request_id=args.request_id,
        )
    except (OSError, json.JSONDecodeError, PreflightError) as exc:
        print(f"preflight failed closed: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "blockers": result["blockers"],
                "next_gate": result["next_gate"],
                "preflight_digest": result["preflight_digest"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "passed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
