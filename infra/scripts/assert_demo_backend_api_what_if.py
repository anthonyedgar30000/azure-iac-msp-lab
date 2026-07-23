from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_CREATE_TYPES = {
    "Microsoft.Compute/availabilitySets",
    "Microsoft.Compute/virtualMachines",
    "Microsoft.Insights/components",
    "Microsoft.Network/networkInterfaces",
    "Microsoft.Storage/storageAccounts",
    "Microsoft.Web/serverfarms",
    "Microsoft.Web/sites",
    "Microsoft.Web/sites/config",
}
PROTECTED_RESOURCE_FRAGMENTS = (
    "/virtualNetworks/",
    "/loadBalancers/",
    "/publicIPAddresses/",
    "/workspaces/",
    "/virtualMachines/vm-stcollector-",
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid What-If JSON {path}: {exc}") from exc


def classify(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("status") != "Succeeded" or payload.get("error") is not None:
        raise SystemExit("ARM What-If did not complete successfully")
    changes = payload.get("changes")
    if not isinstance(changes, list):
        raise SystemExit("ARM What-If changes must be an array")

    forbidden = [
        item
        for item in changes
        if item.get("changeType") not in {"Create", "Ignore", "NoChange"}
    ]
    if forbidden:
        raise SystemExit(
            "What-If contains Modify/Delete/Replace changes: "
            + ", ".join(str(item.get("resourceId")) for item in forbidden)
        )

    creates = [item for item in changes if item.get("changeType") == "Create"]
    unexpected = [
        item
        for item in creates
        if str(item.get("after", {}).get("type") or "") not in ALLOWED_CREATE_TYPES
    ]
    if unexpected:
        raise SystemExit(
            "What-If contains unexpected resource types: "
            + ", ".join(
                str(item.get("after", {}).get("type") or item.get("resourceId"))
                for item in unexpected
            )
        )

    protected = []
    for item in changes:
        resource_id = str(item.get("resourceId") or "")
        if any(fragment.lower() in resource_id.lower() for fragment in PROTECTED_RESOURCE_FRAGMENTS):
            if item.get("changeType") not in {"Ignore", "NoChange"}:
                protected.append(resource_id)
    if protected:
        raise SystemExit("Protected existing infrastructure would change: " + ", ".join(protected))

    create_types: dict[str, int] = {}
    for item in creates:
        resource_type = str(item.get("after", {}).get("type") or "unknown")
        create_types[resource_type] = create_types.get(resource_type, 0) + 1

    return {
        "status": "accepted_create_or_no_change_only",
        "total_changes": len(changes),
        "creates": len(creates),
        "create_types": create_types,
        "forbidden_change_types": [],
        "protected_existing_changes": [],
        "deployment_authorized": False,
        "azure_mutations_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail closed on unsafe demo backend/API What-If")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    summary = classify(load_json(Path(args.input)))
    Path(args.output).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
