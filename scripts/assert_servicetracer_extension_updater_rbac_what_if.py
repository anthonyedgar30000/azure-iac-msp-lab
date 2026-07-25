#!/usr/bin/env python3
"""Fail closed unless Azure What-If contains only the bounded RBAC bootstrap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_TYPES = {
    "Microsoft.Authorization/roleDefinitions",
    "Microsoft.Authorization/roleAssignments",
}
ALLOWED_CHANGES = {"Create", "Modify", "NoChange", "Ignore"}


def normalize_type(value: str) -> str:
    return value.split("@", 1)[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("what_if")
    parser.add_argument("--role-definition-guid", required=True)
    parser.add_argument("--extension-scope", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.what_if).read_text(encoding="utf-8"))
    changes = payload.get("changes")
    if not isinstance(changes, list):
        raise SystemExit("What-If payload has no changes array")

    accepted = []
    for change in changes:
        resource_id = change.get("resourceId") or ""
        resource_type = normalize_type(change.get("resourceType") or "")
        change_type = change.get("changeType") or ""

        if change_type not in ALLOWED_CHANGES:
            raise SystemExit(f"prohibited change type: {change_type!r}")
        if resource_type not in ALLOWED_TYPES:
            raise SystemExit(f"prohibited resource type: {resource_type!r}")
        if change_type in {"Create", "Modify"}:
            if resource_type == "Microsoft.Authorization/roleDefinitions":
                if not resource_id.lower().endswith(
                    f"/providers/microsoft.authorization/roledefinitions/{args.role_definition_guid}".lower()
                ):
                    raise SystemExit(f"unexpected role definition resource: {resource_id}")
            elif resource_type == "Microsoft.Authorization/roleAssignments":
                prefix = args.extension_scope.rstrip("/") + "/providers/Microsoft.Authorization/roleAssignments/"
                if not resource_id.lower().startswith(prefix.lower()):
                    raise SystemExit(f"role assignment escaped extension scope: {resource_id}")
        accepted.append(
            {
                "resource_id": resource_id,
                "resource_type": resource_type,
                "change_type": change_type,
            }
        )

    mutating = [item for item in accepted if item["change_type"] in {"Create", "Modify"}]
    if len(mutating) > 2:
        raise SystemExit(f"expected at most two mutating RBAC resources, found {len(mutating)}")

    result = {
        "status": "accepted_bounded_rbac_bootstrap",
        "allowed_resource_types": sorted(ALLOWED_TYPES),
        "mutating_changes": mutating,
        "deletes_observed": False,
        "non_rbac_resources_observed": False,
    }
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
