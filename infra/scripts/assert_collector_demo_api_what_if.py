from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_CREATE_TYPES = {
    "Microsoft.Compute/virtualMachines/extensions",
    "Microsoft.Network/networkSecurityGroups/securityRules",
    "Microsoft.Network/publicIPAddresses",
}
FORBIDDEN_PROVIDER_FRAGMENTS = (
    "/providers/Microsoft.Web/",
    "/providers/Microsoft.Insights/components/",
)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid ARM What-If JSON {path}: {exc}") from exc


def _resource_type(item: dict[str, Any]) -> str:
    return str(item.get("after", {}).get("type") or "")


def _ends_with(resource_id: str, suffix: str) -> bool:
    return resource_id.lower().endswith(suffix.lower())


def _validate_collector_nic_modify(
    item: dict[str, Any],
    *,
    suffix: str,
    private_ip: str,
) -> bool:
    resource_id = str(item.get("resourceId") or "")
    if not _ends_with(resource_id, f"/networkInterfaces/nic-stcollector-{suffix}"):
        return False

    before = item.get("before")
    after = item.get("after")
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False

    before_props = before.get("properties")
    after_props = after.get("properties")
    if not isinstance(before_props, dict) or not isinstance(after_props, dict):
        return False

    before_configs = before_props.get("ipConfigurations")
    after_configs = after_props.get("ipConfigurations")
    if not isinstance(before_configs, list) or not isinstance(after_configs, list):
        return False
    if len(before_configs) != 1 or len(after_configs) != 1:
        return False

    before_config = before_configs[0].get("properties", {})
    after_config = after_configs[0].get("properties", {})
    if not isinstance(before_config, dict) or not isinstance(after_config, dict):
        return False

    immutable_checks = (
        (before_config.get("privateIPAddress"), private_ip),
        (after_config.get("privateIPAddress"), private_ip),
        (before_config.get("privateIPAllocationMethod"), "Static"),
        (after_config.get("privateIPAllocationMethod"), "Static"),
        (before_config.get("subnet", {}).get("id"), after_config.get("subnet", {}).get("id")),
    )
    if any(actual != expected for actual, expected in immutable_checks):
        return False

    before_public_ip = before_config.get("publicIPAddress")
    after_public_ip = after_config.get("publicIPAddress")
    if before_public_ip not in (None, {}):
        return False
    if not isinstance(after_public_ip, dict):
        return False
    public_ip_id = str(after_public_ip.get("id") or "")
    if not _ends_with(public_ip_id, f"/publicIPAddresses/pip-st-demo-api-{suffix}"):
        return False

    allowed_top_level_properties = {
        "auxiliaryMode",
        "auxiliarySku",
        "disableTcpStateTracking",
        "enableAcceleratedNetworking",
        "enableIPForwarding",
        "ipConfigurations",
    }
    changed_top_level = {
        key
        for key in set(before_props) | set(after_props)
        if before_props.get(key) != after_props.get(key)
    }
    return changed_top_level.issubset(allowed_top_level_properties)


def classify(
    payload: dict[str, Any],
    *,
    suffix: str,
    private_ip: str,
) -> dict[str, Any]:
    if payload.get("status") != "Succeeded" or payload.get("error") is not None:
        raise SystemExit("ARM What-If did not complete successfully")
    changes = payload.get("changes")
    if not isinstance(changes, list):
        raise SystemExit("ARM What-If changes must be an array")

    for item in changes:
        resource_id = str(item.get("resourceId") or "")
        if any(fragment.lower() in resource_id.lower() for fragment in FORBIDDEN_PROVIDER_FRAGMENTS):
            raise SystemExit(f"Microsoft.Web/App Insights remains in the proposed path: {resource_id}")

    creates = [item for item in changes if item.get("changeType") == "Create"]
    allowed_create_suffixes = {
        f"/publicIPAddresses/pip-st-demo-api-{suffix}",
        "/securityRules/Allow-Demo-API-HTTP-From-Internet",
        "/securityRules/Allow-Demo-API-HTTPS-From-Internet",
        f"/virtualMachines/vm-stcollector-{suffix}/extensions/servicetracer-demo-api",
    }
    unexpected_creates = []
    for item in creates:
        resource_id = str(item.get("resourceId") or "")
        resource_type = _resource_type(item)
        if resource_type not in ALLOWED_CREATE_TYPES:
            unexpected_creates.append(resource_id or resource_type)
            continue
        if not any(_ends_with(resource_id, suffix_value) for suffix_value in allowed_create_suffixes):
            unexpected_creates.append(resource_id or resource_type)
    if unexpected_creates:
        raise SystemExit("Unexpected resources would be created: " + ", ".join(unexpected_creates))

    accepted_nic_modifies = []
    forbidden = []
    for item in changes:
        change_type = item.get("changeType")
        if change_type in {"Create", "Ignore", "NoChange"}:
            continue
        if change_type == "Modify" and _validate_collector_nic_modify(
            item,
            suffix=suffix,
            private_ip=private_ip,
        ):
            accepted_nic_modifies.append(str(item.get("resourceId")))
            continue
        forbidden.append(str(item.get("resourceId") or change_type))
    if forbidden:
        raise SystemExit(
            "What-If contains unapproved Modify/Delete/Replace changes: " + ", ".join(forbidden)
        )

    return {
        "schema_version": "servicetracer.collector-demo-api-what-if.v1",
        "status": "accepted_collector_demo_api_changes_only",
        "total_changes": len(changes),
        "creates": len(creates),
        "accepted_collector_nic_modifies": accepted_nic_modifies,
        "forbidden_changes": [],
        "microsoft_web_resources_proposed": False,
        "deployment_authorized": False,
        "azure_mutations_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail closed on collector demo API What-If")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--suffix", required=True)
    parser.add_argument("--private-ip", required=True)
    args = parser.parse_args()

    summary = classify(
        _load_json(Path(args.input)),
        suffix=args.suffix,
        private_ip=args.private_ip,
    )
    Path(args.output).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
