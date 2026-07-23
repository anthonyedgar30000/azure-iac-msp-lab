from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_CREATE_TYPES = {
    "Microsoft.Compute/virtualMachines/extensions",
    "Microsoft.Network/loadBalancers",
    "Microsoft.Network/networkSecurityGroups/securityRules",
    "Microsoft.Network/publicIPAddresses",
}
FORBIDDEN_PROVIDER_FRAGMENTS = (
    "/providers/Microsoft.Web/",
    "/providers/Microsoft.Insights/components/",
)
PASSIVE_CHANGE_TYPES = {"Ignore", "NoChange"}
DEFAULT_TARGET_CHANGE_TYPES = {"Create", "NoChange"}
PUBLIC_IP_RECONCILIATION = {
    "path": "tags.exposure",
    "propertyChangeType": "Modify",
    "before": "load-balanced-public-https",
    "after": "dedicated-load-balanced-public-https",
}


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


def _named_items(properties: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    raw = properties.get(key)
    if not isinstance(raw, list):
        raise SystemExit(f"Dedicated load balancer {key} must be an array")
    result: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise SystemExit(f"Dedicated load balancer {key} entries must have names")
        name = item["name"]
        if name in result:
            raise SystemExit(f"Dedicated load balancer {key} contains duplicate {name}")
        result[name] = item
    return result


def _item_properties(item: dict[str, Any], label: str) -> dict[str, Any]:
    properties = item.get("properties")
    if not isinstance(properties, dict):
        raise SystemExit(f"{label} must contain properties")
    return properties


def _validate_public_ip(item: dict[str, Any], *, dns_label: str) -> None:
    properties = _properties(item)
    if properties.get("publicIPAllocationMethod") != "Static":
        raise SystemExit("Collector API public IP must remain static")
    dns_settings = properties.get("dnsSettings")
    if not isinstance(dns_settings, dict) or dns_settings.get("domainNameLabel") != dns_label:
        raise SystemExit("Collector API public IP DNS label differs from the bounded request")


def _validate_public_ip_reconciliation(item: dict[str, Any]) -> None:
    delta = item.get("delta")
    if not isinstance(delta, list) or len(delta) != 1:
        raise SystemExit("Collector API public IP Modify must contain exactly one approved delta")
    change = delta[0]
    if not isinstance(change, dict):
        raise SystemExit("Collector API public IP delta must be an object")
    observed = {key: change.get(key) for key in PUBLIC_IP_RECONCILIATION}
    if observed != PUBLIC_IP_RECONCILIATION:
        raise SystemExit("Collector API public IP Modify leaves the bounded exposure-tag reconciliation")
    if change.get("children") not in (None, []):
        raise SystemExit("Collector API public IP reconciliation must not contain nested changes")


def _validate_dedicated_load_balancer(
    item: dict[str, Any],
    *,
    suffix: str,
    private_ip: str,
    virtual_network_id: str,
) -> None:
    after = item.get("after") if isinstance(item.get("after"), dict) else {}
    sku = after.get("sku") if isinstance(after.get("sku"), dict) else {}
    if sku.get("name") != "Standard":
        raise SystemExit("Collector API load balancer must use Standard SKU")

    properties = _properties(item)
    frontends = _named_items(properties, "frontendIPConfigurations")
    pools = _named_items(properties, "backendAddressPools")
    probes = _named_items(properties, "probes")
    rules = _named_items(properties, "loadBalancingRules")

    if set(frontends) != {"fe-public-st-demo-api"}:
        raise SystemExit("Dedicated load balancer must contain exactly the collector API frontend")
    if set(pools) != {"be-st-demo-api"}:
        raise SystemExit("Dedicated load balancer must contain exactly the collector API backend pool")
    if set(probes) != {"probe-tcp-80-st-demo-api"}:
        raise SystemExit("Dedicated load balancer must contain exactly the bounded TCP/80 probe")
    if set(rules) != {"rule-st-demo-api-http", "rule-st-demo-api-https"}:
        raise SystemExit("Dedicated load balancer must contain exactly the HTTP and HTTPS rules")

    frontend = _item_properties(frontends["fe-public-st-demo-api"], "collector API frontend")
    public_ip = frontend.get("publicIPAddress")
    public_ip_id = public_ip.get("id") if isinstance(public_ip, dict) else None
    if not isinstance(public_ip_id, str) or not _ends_with(
        public_ip_id, f"/publicIPAddresses/pip-st-demo-api-{suffix}"
    ):
        raise SystemExit("Dedicated load balancer frontend does not use the bounded public IP")

    pool = _item_properties(pools["be-st-demo-api"], "collector API backend pool")
    if "virtualNetwork" in pool or "subnet" in pool:
        raise SystemExit("IP-based backend pool must not set virtual network at pool level")
    addresses = pool.get("loadBalancerBackendAddresses")
    if not isinstance(addresses, list) or len(addresses) != 1:
        raise SystemExit("Collector API backend pool must contain exactly one address")
    address = addresses[0] if isinstance(addresses[0], dict) else {}
    if address.get("name") != "collector":
        raise SystemExit("Collector API backend address must be named collector")
    address_properties = _item_properties(address, "collector API backend address")
    if address_properties.get("ipAddress") != private_ip:
        raise SystemExit("Collector API backend pool does not target the proven collector private IP")
    virtual_network = address_properties.get("virtualNetwork")
    if not isinstance(virtual_network, dict) or virtual_network.get("id") != virtual_network_id:
        raise SystemExit("Collector API backend address does not use the proven virtual network")

    probe = _item_properties(probes["probe-tcp-80-st-demo-api"], "collector API probe")
    if probe.get("protocol") != "Tcp" or probe.get("port") != 80:
        raise SystemExit("Collector API probe must remain TCP/80")

    expected_ports = {
        "rule-st-demo-api-http": 80,
        "rule-st-demo-api-https": 443,
    }
    load_balancer_name = f"lb-st-demo-api-{suffix}"
    for name, port in expected_ports.items():
        rule = _item_properties(rules[name], name)
        if rule.get("protocol") != "Tcp" or rule.get("frontendPort") != port or rule.get("backendPort") != port:
            raise SystemExit(f"{name} ports differ from the bounded contract")
        if rule.get("disableOutboundSnat") is not True:
            raise SystemExit(f"{name} must disable outbound SNAT")
        references = {
            "frontendIPConfiguration": "/frontendIPConfigurations/fe-public-st-demo-api",
            "backendAddressPool": "/backendAddressPools/be-st-demo-api",
            "probe": "/probes/probe-tcp-80-st-demo-api",
        }
        for field, ending in references.items():
            reference = rule.get(field)
            reference_id = reference.get("id") if isinstance(reference, dict) else None
            expected_ending = f"/loadBalancers/{load_balancer_name}{ending}"
            if not isinstance(reference_id, str) or not _ends_with(reference_id, expected_ending):
                raise SystemExit(f"{name} {field} reference leaves the dedicated load balancer")


def _validate_expected_payload(
    item: dict[str, Any],
    *,
    suffix: str,
    private_ip: str,
    virtual_network_id: str,
    dns_label: str,
) -> None:
    resource_id = str(item.get("resourceId") or "")
    properties = _properties(item)
    lowered = resource_id.lower()

    if lowered.endswith(f"/publicipaddresses/pip-st-demo-api-{suffix}".lower()):
        _validate_public_ip(item, dns_label=dns_label)
    elif lowered.endswith(f"/loadbalancers/lb-st-demo-api-{suffix}".lower()):
        _validate_dedicated_load_balancer(
            item,
            suffix=suffix,
            private_ip=private_ip,
            virtual_network_id=virtual_network_id,
        )
    elif lowered.endswith("/securityrules/allow-demo-api-http-from-internet"):
        if properties.get("destinationAddressPrefix") != private_ip or properties.get("destinationPortRange") != "80":
            raise SystemExit("Collector API HTTP NSG rule does not match the bounded collector endpoint")
    elif lowered.endswith("/securityrules/allow-demo-api-https-from-internet"):
        if properties.get("destinationAddressPrefix") != private_ip or properties.get("destinationPortRange") != "443":
            raise SystemExit("Collector API HTTPS NSG rule does not match the bounded collector endpoint")


def classify(
    payload: dict[str, Any],
    *,
    suffix: str,
    private_ip: str,
    virtual_network_id: str,
    dns_label: str,
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

    public_ip_suffix = f"/publicIPAddresses/pip-st-demo-api-{suffix}"
    target_suffixes = {
        public_ip_suffix: "Microsoft.Network/publicIPAddresses",
        f"/loadBalancers/lb-st-demo-api-{suffix}": "Microsoft.Network/loadBalancers",
        "/securityRules/Allow-Demo-API-HTTP-From-Internet": "Microsoft.Network/networkSecurityGroups/securityRules",
        "/securityRules/Allow-Demo-API-HTTPS-From-Internet": "Microsoft.Network/networkSecurityGroups/securityRules",
        f"/virtualMachines/vm-stcollector-{suffix}/extensions/servicetracer-demo-api": "Microsoft.Compute/virtualMachines/extensions",
    }
    matched_targets: dict[str, str] = {}
    approved_reconciliations: list[str] = []
    unexpected_creates: list[str] = []
    seen_resource_ids: set[str] = set()

    for item in changes:
        resource_id = str(item.get("resourceId") or "")
        change_type = str(item.get("changeType") or "")
        normalized_id = resource_id.lower()
        if normalized_id in seen_resource_ids:
            raise SystemExit(f"Duplicate ARM What-If entry: {resource_id}")
        seen_resource_ids.add(normalized_id)

        matched_suffix = next(
            (expected for expected in target_suffixes if _ends_with(resource_id, expected)),
            None,
        )
        if matched_suffix is not None:
            allowed_change_types = set(DEFAULT_TARGET_CHANGE_TYPES)
            if matched_suffix == public_ip_suffix:
                allowed_change_types.add("Modify")
            if change_type not in allowed_change_types:
                raise SystemExit(f"Target resource has an unapproved change type {change_type}: {resource_id}")
            expected_type = target_suffixes[matched_suffix]
            if _resource_type(item) != expected_type:
                raise SystemExit(f"Target resource type differs from contract: {resource_id}")
            _validate_expected_payload(
                item,
                suffix=suffix,
                private_ip=private_ip,
                virtual_network_id=virtual_network_id,
                dns_label=dns_label,
            )
            if change_type == "Modify":
                _validate_public_ip_reconciliation(item)
                approved_reconciliations.append(resource_id)
            matched_targets[matched_suffix] = change_type
        elif change_type == "Create":
            resource_type = _resource_type(item)
            if resource_type not in ALLOWED_CREATE_TYPES:
                unexpected_creates.append(resource_id or resource_type)
            else:
                unexpected_creates.append(resource_id or resource_type)

    if unexpected_creates:
        raise SystemExit("Unexpected resources would be created: " + ", ".join(unexpected_creates))

    missing_targets = sorted(set(target_suffixes) - set(matched_targets))
    if missing_targets:
        raise SystemExit("What-If omitted required collector API targets: " + ", ".join(missing_targets))

    approved_reconciliation_ids = {resource_id.lower() for resource_id in approved_reconciliations}
    forbidden = [
        str(item.get("resourceId") or item.get("changeType"))
        for item in changes
        if item.get("changeType") not in {"Create", "Ignore", "NoChange"}
        and str(item.get("resourceId") or "").lower() not in approved_reconciliation_ids
    ]
    if forbidden:
        raise SystemExit(
            "What-If contains unapproved Modify/Delete/Replace changes: " + ", ".join(forbidden)
        )

    creates = [item for item in changes if item.get("changeType") == "Create"]
    return {
        "schema_version": "servicetracer.collector-demo-api-what-if.v2",
        "status": "accepted_isolated_collector_api_changes",
        "ingress_strategy": "dedicated_standard_load_balancer",
        "total_changes": len(changes),
        "creates": len(creates),
        "target_resource_states": matched_targets,
        "approved_reconciliations": approved_reconciliations,
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
    parser.add_argument("--virtual-network-id", required=True)
    parser.add_argument("--dns-label", required=True)
    args = parser.parse_args()

    summary = classify(
        _load_json(Path(args.input)),
        suffix=args.suffix,
        private_ip=args.private_ip,
        virtual_network_id=args.virtual_network_id,
        dns_label=args.dns_label,
    )
    Path(args.output).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
