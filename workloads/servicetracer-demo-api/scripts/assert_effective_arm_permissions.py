#!/usr/bin/env python3
"""Fail closed unless Azure's effective-permissions response allows required actions."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any


def normalize_patterns(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.lower() for item in value if isinstance(item, str) and item]


def pattern_matches(pattern: str, action: str) -> bool:
    return fnmatch.fnmatchcase(action.lower(), pattern.lower())


def permission_allows(permission: dict[str, Any], action: str) -> bool:
    actions = normalize_patterns(permission.get("actions"))
    not_actions = normalize_patterns(permission.get("notActions"))
    allowed = any(pattern_matches(pattern, action) for pattern in actions)
    denied = any(pattern_matches(pattern, action) for pattern in not_actions)
    return allowed and not denied


def effective_allows(document: dict[str, Any], action: str) -> bool:
    value = document.get("value")
    if not isinstance(value, list):
        return False
    permissions = [item for item in value if isinstance(item, dict)]
    return any(permission_allows(permission, action) for permission in permissions)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--require", action="append", required=True, dest="required")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid permissions JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(document, dict):
        print("permissions root must be an object", file=sys.stderr)
        return 2

    results = {action: effective_allows(document, action) for action in args.required}
    summary = {
        "status": "accepted" if all(results.values()) else "rejected",
        "required_actions": results,
        "claim_boundary": "effective permission observed != future authorization granted",
    }

    if args.output:
        args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if not all(results.values()):
        missing = [action for action, allowed in results.items() if not allowed]
        print(f"required ARM permissions not observed: {missing}", file=sys.stderr)
        return 1

    print("required ARM permissions verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
