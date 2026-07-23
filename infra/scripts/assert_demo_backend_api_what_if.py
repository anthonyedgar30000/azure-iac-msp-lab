from __future__ import annotations

import argparse
import json
import re
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

_RESOURCE_LINE = re.compile(
    r"^\s{2}(?P<symbol>[+\-~=*x])\s+"
    r"(?P<resource>[A-Za-z0-9.]+/[^\s\[]+)"
    r"(?:\s+\[[^\]]+\])?\s*$"
)
_SYMBOL_TO_CHANGE_TYPE = {
    "+": "Create",
    "-": "Delete",
    "~": "Modify",
    "=": "NoChange",
    "*": "Ignore",
    "x": "NoEffect",
}
_SUMMARY_TOKEN_TO_CHANGE_TYPE = {
    "create": "Create",
    "delete": "Delete",
    "modify": "Modify",
    "replace": "Replace",
    "no change": "NoChange",
    "ignore": "Ignore",
    "no effect": "NoEffect",
}


def _resource_type(resource_path: str) -> str:
    parts = resource_path.split("/")
    if len(parts) < 3 or len(parts) % 2 == 0:
        raise SystemExit(f"Invalid resource path in ARM What-If output: {resource_path}")
    return "/".join([parts[0], *parts[1::2]])


def parse_pretty_what_if(text: str) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    summary_line: str | None = None

    for line in text.splitlines():
        if line.startswith("Resource changes:"):
            summary_line = line
            continue
        match = _RESOURCE_LINE.match(line)
        if not match:
            continue
        resource_path = match.group("resource")
        change_type = _SYMBOL_TO_CHANGE_TYPE[match.group("symbol")]
        item: dict[str, Any] = {
            "changeType": change_type,
            "resourceId": f"/providers/{resource_path}",
        }
        if change_type == "Create":
            item["after"] = {"type": _resource_type(resource_path)}
        changes.append(item)

    if summary_line is None:
        raise SystemExit("ARM What-If text is missing the resource-change summary")
    if not changes and not re.search(r"\b0\s+to\s+create\b", summary_line, re.IGNORECASE):
        raise SystemExit("ARM What-If text did not contain parseable resource changes")

    parsed_counts: dict[str, int] = {}
    for item in changes:
        change_type = str(item["changeType"])
        parsed_counts[change_type] = parsed_counts.get(change_type, 0) + 1

    for token, change_type in _SUMMARY_TOKEN_TO_CHANGE_TYPE.items():
        pattern = (
            rf"(?P<count>\d+)\s+(?:to\s+)?{re.escape(token)}"
            if token not in {"no change", "no effect"}
            else rf"(?P<count>\d+)\s+{re.escape(token)}"
        )
        match = re.search(pattern, summary_line, re.IGNORECASE)
        if match and parsed_counts.get(change_type, 0) != int(match.group("count")):
            raise SystemExit(
                "ARM What-If text parsing did not match its summary for "
                f"{change_type}: parsed {parsed_counts.get(change_type, 0)}, "
                f"summary {match.group('count')}"
            )

    return {"status": "Succeeded", "error": None, "changes": changes}


def load_what_if(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Unable to read What-If evidence {path}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return parse_pretty_what_if(text)


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
    summary = classify(load_what_if(Path(args.input)))
    Path(args.output).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
