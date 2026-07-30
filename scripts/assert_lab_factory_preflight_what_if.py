from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class WhatIfError(RuntimeError):
    pass


ALLOWED_CHANGE_TYPES = {"Create", "NoChange", "Ignore"}
ALLOWED_RESOURCE_TYPES = {
    "Microsoft.Resources/resourceGroups",
    "Microsoft.Resources/deployments",
    "Microsoft.Network/networkSecurityGroups",
    "Microsoft.Network/virtualNetworks",
    "Microsoft.Network/publicIPAddresses",
    "Microsoft.Network/networkInterfaces",
    "Microsoft.Compute/virtualMachines",
    "Microsoft.Compute/virtualMachines/extensions",
}


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise WhatIfError("What-If payload must be a JSON object")
    return payload


def _changes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("changes")
    if candidates is None:
        candidates = payload.get("properties", {}).get("changes")
    if not isinstance(candidates, list):
        raise WhatIfError("What-If changes were not observed")
    return [item for item in candidates if isinstance(item, dict)]


def assess(payload: dict[str, Any], *, resource_group: str) -> dict[str, Any]:
    changes = _changes(payload)
    if not changes:
        raise WhatIfError("What-If returned no changes for an absent target resource group")

    normalized: list[dict[str, str]] = []
    observed_types: set[str] = set()
    for change in changes:
        change_type = str(change.get("changeType") or "")
        resource_id = str(change.get("resourceId") or "")
        resource_type = str(change.get("resourceType") or "")
        if not resource_type:
            after = change.get("after") or {}
            resource_type = str(after.get("type") or "")
        if change_type not in ALLOWED_CHANGE_TYPES:
            raise WhatIfError(f"unexpected What-If change type: {change_type or '<missing>'}")
        if not resource_id:
            raise WhatIfError("What-If change omitted resourceId")
        if resource_type not in ALLOWED_RESOURCE_TYPES:
            raise WhatIfError(f"unexpected resource type: {resource_type or '<missing>'}")

        if resource_type == "Microsoft.Resources/resourceGroups":
            expected_suffix = f"/resourceGroups/{resource_group}".lower()
            if not resource_id.lower().endswith(expected_suffix):
                raise WhatIfError(f"resource-group scope escaped: {resource_id}")
        elif f"/resourceGroups/{resource_group}/".lower() not in resource_id.lower():
            raise WhatIfError(f"resource scope escaped target group: {resource_id}")

        observed_types.add(resource_type)
        normalized.append(
            {
                "change_type": change_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )

    required = {
        "Microsoft.Resources/resourceGroups",
        "Microsoft.Resources/deployments",
    }
    missing = sorted(required - observed_types)
    if missing:
        raise WhatIfError(f"required What-If resource types missing: {', '.join(missing)}")

    return {
        "schema_version": "lab-factory.preflight-what-if-assessment.v1",
        "resource_group": resource_group,
        "change_count": len(normalized),
        "change_types": sorted({item["change_type"] for item in normalized}),
        "resource_types": sorted(observed_types),
        "unexpected_changes": [],
        "scope_contained": True,
        "deletes_observed": False,
        "modifications_observed": False,
        "what_if_passed": True,
        "boundary": "accepted What-If != deployment authorized",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        result = assess(_load(args.input), resource_group=args.resource_group)
    except (WhatIfError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
