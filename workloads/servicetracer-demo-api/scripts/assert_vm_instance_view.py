#!/usr/bin/env python3
"""Fail closed unless Azure VM instance-view reports PowerState/running."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def status_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def extract_statuses(document: dict[str, Any]) -> list[dict[str, Any]]:
    statuses = status_list(document.get("statuses"))
    if statuses:
        return statuses
    instance_view = document.get("instanceView")
    if isinstance(instance_view, dict):
        return status_list(instance_view.get("statuses"))
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()

    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid instance-view JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(document, dict):
        print("instance-view root must be an object", file=sys.stderr)
        return 2

    statuses = extract_statuses(document)
    if not statuses:
        print("no usable VM status collection", file=sys.stderr)
        return 1

    if not any(item.get("code") == "PowerState/running" for item in statuses):
        codes = [item.get("code") for item in statuses]
        print(f"VM not observed running; status codes={codes}", file=sys.stderr)
        return 1

    print("VM running state verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
