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


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid ARM What-If JSON {path}: {exc}") from exc


def _resource_type(item: dict[str, Any]) -> str:
    return str(item.get("after", {}).get("type") or "")


def _ends_with(resource_id: str, suffix: str) -> bool:
    return resource_id.lower().endswith(suffix.lower())


def classify(
    payload: dict[str, Any],
    *,
    suffix: str,
    private_ip: str,
) -> dict[str, Any]:
    del private_ip  # The collector NIC remains private and is not an authorized change.

    if payload.get("status") != "Succeeded" or payload.get("error") is not None:
        raise SystemExit("ARM What-If did not complete successfully")
    changes = payload.get("changes")
    if not isinstance(changes, list):
        raise SystemExit("ARM What-If changes must be an array")

    for item in changes:
        resource_id = str(item.get("resourceId") or "")
        if any(fragment.lower() in resource_id.lower() for fragment in FORBIDDEN_PROVIDER_FRAGMENTS):
            raise SystemExit(f"Managed web/App Insights resources remain in the proposed path: {resource_id}")

    creates = [item for item in changes if item.get("changeType") == "Create"]
    allowed_create_suffixes = {
        f"/publicIPAddresses/pip-st-demo-api-{suffix}",
        "/frontendIPConfigurations/fe-public-st-demo-api",
        "/backendAddressPools/be-st-demo-api",
        "/probes/probe-tcp-443-st-demo-api",
        "/loadBalancingRules/rule-st-demo-api-http",
        "/loadBalancingRules/rule-st-demo-api-https",
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
        "schema_version": "servicetracer.collector-demo-api-what-if.v1",
        "status": "accepted_load_balanced_collector_api_creates_only",
        "total_changes": len(changes),
        "creates": len(creates),
        "collector_nic_modifications": [],
        "collector_vm_modifications": [],
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
