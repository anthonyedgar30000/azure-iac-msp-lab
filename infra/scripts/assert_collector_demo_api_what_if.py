from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_CREATE_TYPES = {
    "Microsoft.Compute/virtualMachines/extensions",
    "Microsoft.Network/loadBalancers/backendAddressPools",
    "Microsoft.Network/loadBalancers/frontendIPConfigurations",
    "Microsoft.Network/loadBalancers/loadBalancingRules",
    "Microsoft.Network/loadBalancers/probes",
    "Microsoft.Network/networkSecurityGroups/securityRules",
    "Microsoft.Network/publicIPAddresses",
}
FORBIDDEN_PROVIDER_FRAGMENTS = (
    "/providers/Microsoft.Web/",
    "/providers/Microsoft.Insights/components/",
)
PASSIVE_CHANGE_TYPES = {"Ignore", "NoChange"}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid ARM What-If JSON {path}: {exc}") from exc


def _resource_type(item: dict[str, Any]) -> str:
    after = item.get("after") if isinstance(item.get("after"), dict) else {}
    before = item.get("before") if isinstance(item.get("before"), dict) else {}
    return str(after.get("type") or before.get("type") or "")


def _ends_with(resource_id: str, suffix: str) -> bool:
    return resource_id.lower().endswith(suffix.lower())


def _properties(item: dict[str, Any]) -> dict[str, Any]:
    after = item.get("after") if isinstance(item.get("after"), dict) else {}
    properties = after.get("properties")
    return properties if isinstance(properties, dict) else {}


def _validate_expected_payload(item: dict[str, Any], *, private_ip: str) -> None:
    resource_id = str(item.get("resourceId") or "")
    properties = _properties(item)
    lowered = resource_id.lower()

    if lowered.endswith("/backendaddresspools/be-st-demo-api"):
        addresses = properties.get("loadBalancerBackendAddresses")
        if not isinstance(addresses, list) or len(addresses) != 1:
            raise SystemExit("Collector API backend pool must contain exactly one address")
        address_properties = addresses[0].get("properties") if isinstance(addresses[0], dict) else None
        if not isinstance(address_properties, dict) or address_properties.get("ipAddress") != private_ip:
            raise SystemExit("Collector API backend pool does not target the proven collector private IP")

    if lowered.endswith("/securityrules/allow-demo-api-http-from-internet"):
        if properties.get("destinationAddressPrefix") != private_ip or properties.get("destinationPortRange") != "80":
            raise SystemExit("Collector API HTTP NSG rule does not match the bounded collector endpoint")

    if lowered.endswith("/securityrules/allow-demo-api-https-from-internet"):
        if properties.get("destinationAddressPrefix") != private_ip or properties.get("destinationPortRange") != "443":
            raise SystemExit("Collector API HTTPS NSG rule does not match the bounded collector endpoint")


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

    active_managed_provider_changes: list[str] = []
    ignored_managed_leftovers: list[str] = []
    for item in changes:
        if not isinstance(item, dict):
            raise SystemExit("ARM What-If change entries must be objects")
        resource_id = str(item.get("resourceId") or "")
        change_type = str(item.get("changeType") or "")
        if any(fragment.lower() in resource_id.lower() for fragment in FORBIDDEN_PROVIDER_FRAGMENTS):
            if change_type in PASSIVE_CHANGE_TYPES:
                ignored_managed_leftovers.append(resource_id)
            else:
                active_managed_provider_changes.append(resource_id or change_type)
    if active_managed_provider_changes:
        raise SystemExit(
            "Managed web/App Insights resources remain in the active proposed path: "
            + ", ".join(active_managed_provider_changes)
        )

    creates = [item for item in changes if item.get("changeType") == "Create"]
    allowed_create_suffixes = {
        f"/publicIPAddresses/pip-st-demo-api-{suffix}",
        "/frontendIPConfigurations/fe-public-st-demo-api",
        "/backendAddressPools/be-st-demo-api",
        "/probes/probe-tcp-80-st-demo-api",
        "/loadBalancingRules/rule-st-demo-api-http",
        "/loadBalancingRules/rule-st-demo-api-https",
        "/securityRules/Allow-Demo-API-HTTP-From-Internet",
        "/securityRules/Allow-Demo-API-HTTPS-From-Internet",
        f"/virtualMachines/vm-stcollector-{suffix}/extensions/servicetracer-demo-api",
    }
    unexpected_creates: list[str] = []
    seen_create_ids: set[str] = set()
    for item in creates:
        resource_id = str(item.get("resourceId") or "")
        resource_type = _resource_type(item)
        normalized_id = resource_id.lower()
        if normalized_id in seen_create_ids:
            raise SystemExit(f"Duplicate Create entry in ARM What-If: {resource_id}")
        seen_create_ids.add(normalized_id)
        if resource_type not in ALLOWED_CREATE_TYPES:
            unexpected_creates.append(resource_id or resource_type)
            continue
        if not any(_ends_with(resource_id, suffix_value) for suffix_value in allowed_create_suffixes):
            unexpected_creates.append(resource_id or resource_type)
            continue
        _validate_expected_payload(item, private_ip=private_ip)
    if unexpected_creates:
        raise SystemExit("Unexpected resources would be created: " + ", ".join(unexpected_creates))

    forbidden = [
        str(item.get("resourceId") or item.get("changeType"))
        for item in changes
        if item.get("changeType") not in {"Create", "Ignore", "NoChange"}
    ]
    if forbidden:
        raise SystemExit(
            "What-If contains unapproved Modify/Delete/Replace changes: " + ", ".join(forbidden)
        )

    return {
        "schema_version": "servicetracer.collector-demo-api-what-if.v2",
        "status": "accepted_isolated_collector_api_changes",
        "total_changes": len(changes),
        "creates": len(creates),
        "ignored_managed_leftovers": ignored_managed_leftovers,
        "collector_nic_modifications": [],
        "collector_vm_modifications": [],
        "base_infrastructure_modifications": [],
        "forbidden_changes": [],
        "managed_web_resources_proposed": False,
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
