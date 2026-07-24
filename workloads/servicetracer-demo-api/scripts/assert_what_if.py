from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_TYPES = {
    "Microsoft.Resources/resourceGroups",
    "Microsoft.Network/networkSecurityGroups",
    "Microsoft.Network/virtualNetworks",
    "Microsoft.Network/publicIPAddresses",
    "Microsoft.Network/networkInterfaces",
    "Microsoft.Compute/virtualMachines",
    "Microsoft.Compute/virtualMachines/extensions",
}
PASSIVE_CHANGE_TYPES = {"Ignore", "NoChange"}
ALLOWED_ACTIVE_CHANGE_TYPES = {"Create"}


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid What-If JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("What-If payload must be an object")
    return payload


def _resource_type(item: dict[str, Any]) -> str:
    after = item.get("after") if isinstance(item.get("after"), dict) else {}
    before = item.get("before") if isinstance(item.get("before"), dict) else {}
    return str(after.get("type") or before.get("type") or "")


def classify(
    payload: dict[str, Any],
    *,
    target_resource_group: str,
    dependency_resource_group: str,
    suffix: str,
) -> dict[str, Any]:
    if payload.get("status") != "Succeeded" or payload.get("error") is not None:
        raise SystemExit("ARM What-If did not complete successfully")
    changes = payload.get("changes")
    if not isinstance(changes, list):
        raise SystemExit("ARM What-If changes must be an array")

    target_marker = f"/resourceGroups/{target_resource_group}/".lower()
    dependency_marker = f"/resourceGroups/{dependency_resource_group}/".lower()
    required_endings = {
        f"/resourceGroups/{target_resource_group}".lower(),
        f"/publicIPAddresses/pip-st-demo-api-vm-{suffix}".lower(),
        f"/virtualMachines/vm-st-demo-api-{suffix}".lower(),
    }
    observed_required: set[str] = set()
    active: list[dict[str, str]] = []
    passive: list[str] = []
    seen: set[str] = set()

    for item in changes:
        if not isinstance(item, dict):
            raise SystemExit("ARM What-If change entries must be objects")
        resource_id = str(item.get("resourceId") or "")
        change_type = str(item.get("changeType") or "")
        normalized = resource_id.lower()
        if not resource_id:
            raise SystemExit("ARM What-If entry omitted resourceId")
        if normalized in seen:
            raise SystemExit(f"Duplicate What-If entry: {resource_id}")
        seen.add(normalized)

        if dependency_marker in normalized and change_type not in PASSIVE_CHANGE_TYPES:
            raise SystemExit(f"Dependency resource would be mutated: {resource_id}")

        if change_type in PASSIVE_CHANGE_TYPES:
            passive.append(resource_id)
            continue
        if change_type not in ALLOWED_ACTIVE_CHANGE_TYPES:
            raise SystemExit(f"Unapproved change type {change_type}: {resource_id}")

        is_target_rg = normalized.endswith(f"/resourcegroups/{target_resource_group}".lower())
        if not is_target_rg and target_marker not in normalized:
            raise SystemExit(f"Active change leaves the dedicated resource group: {resource_id}")

        resource_type = _resource_type(item)
        if resource_type not in ALLOWED_TYPES:
            raise SystemExit(f"Unapproved resource type {resource_type}: {resource_id}")

        for ending in required_endings:
            if normalized.endswith(ending):
                observed_required.add(ending)
        active.append({"resource_id": resource_id, "change_type": change_type, "resource_type": resource_type})

    missing = sorted(required_endings - observed_required)
    if missing:
        raise SystemExit("What-If omitted required workload resources: " + ", ".join(missing))

    return {
        "schema_version": "servicetracer.demo-api-subproject-what-if.v1",
        "status": "accepted_independent_workload_create_plan",
        "target_resource_group": target_resource_group,
        "dependency_resource_group": dependency_resource_group,
        "active_changes": active,
        "passive_changes": passive,
        "base_infrastructure_modifications": [],
        "dependency_modifications": [],
        "deployment_authorized": False,
        "azure_mutations_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail closed on the independent demo API What-If")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target-resource-group", required=True)
    parser.add_argument("--dependency-resource-group", required=True)
    parser.add_argument("--suffix", required=True)
    args = parser.parse_args()

    result = classify(
        _load(Path(args.input)),
        target_resource_group=args.target_resource_group,
        dependency_resource_group=args.dependency_resource_group,
        suffix=args.suffix,
    )
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
