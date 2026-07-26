#!/usr/bin/env python3
"""Normalize Azure Cost Management query evidence without inventing cost facts."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any


def load_json(path: Path | None) -> Any:
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid Cost Management evidence {path}: {exc}") from exc


def summarize(
    payload: Any,
    *,
    scope: str,
    unavailable_reason: str | None = None,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": "servicetracer.azure-cost-observation.v1",
        "scope": scope,
        "timeframe": "MonthToDate",
        "metric": "PreTaxCost",
        "source": "azure_cost_management_query_2023_11_01",
        "observation_status": "not_observed",
        "amount": None,
        "currency": None,
        "boundary": "not_observed != zero_cost",
    }

    if unavailable_reason:
        base["reason"] = unavailable_reason
        return base

    root = payload if isinstance(payload, dict) else {}
    properties = root.get("properties")
    if not isinstance(properties, dict):
        base["reason"] = "response_properties_missing"
        return base

    columns = properties.get("columns")
    rows = properties.get("rows")
    if not isinstance(columns, list) or not isinstance(rows, list):
        base["reason"] = "response_columns_or_rows_missing"
        return base
    if not rows:
        base["reason"] = "cost_management_returned_no_rows"
        return base

    column_names = [
        str(column.get("name") or "") if isinstance(column, dict) else ""
        for column in columns
    ]
    try:
        cost_index = column_names.index("PreTaxCost")
        currency_index = column_names.index("Currency")
    except ValueError:
        base["reason"] = "required_cost_columns_missing"
        return base

    total = Decimal("0")
    currencies: set[str] = set()
    row_count = 0
    for row in rows:
        if not isinstance(row, list):
            base["reason"] = "invalid_cost_row"
            return base
        if max(cost_index, currency_index) >= len(row):
            base["reason"] = "cost_row_too_short"
            return base
        try:
            total += Decimal(str(row[cost_index]))
        except (InvalidOperation, ValueError):
            base["reason"] = "invalid_cost_value"
            return base
        currency = str(row[currency_index] or "").strip()
        if not currency:
            base["reason"] = "currency_missing"
            return base
        currencies.add(currency)
        row_count += 1

    if len(currencies) != 1:
        base["reason"] = "multiple_currencies_observed"
        base["currencies"] = sorted(currencies)
        return base

    base.update(
        {
            "observation_status": "observed",
            "amount": float(total),
            "currency": next(iter(currencies)),
            "row_count": row_count,
            "boundary": "observed_month_to_date_cost != remaining_credit",
        }
    )
    return base


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize a Cost Management query into bounded cost evidence"
    )
    parser.add_argument("--input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--scope", required=True, choices=("subscription", "resource_group"))
    parser.add_argument("--unavailable-reason")
    args = parser.parse_args()

    if not args.input and not args.unavailable_reason:
        parser.error("--input or --unavailable-reason is required")

    result = summarize(
        load_json(Path(args.input)) if args.input else None,
        scope=args.scope,
        unavailable_reason=args.unavailable_reason,
    )
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
