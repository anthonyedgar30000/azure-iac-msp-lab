#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
from pathlib import Path
from typing import Any

OUTPUT_SCHEMA = "servicetracer.infrastructure-graph.v1"
CONTRACT_SCHEMA = "servicetracer.azure-resource-graph-semantic-inventory.v1"
RESOURCE_ID_RE = re.compile(
    r"^/subscriptions/(?P<subscription>[^/]+)/resourcegroups/(?P<resource_group>[^/]+)/providers/(?P<provider>[^/]+)/(?P<rest>.+)$",
    re.IGNORECASE,
)
SENSITIVE_KEY_RE = re.compile(
    r"(^|_)(password|passwd|secret|token|connectionstring|connection_string|privatekey|private_key|clientsecret|client_secret)($|_)",
    re.IGNORECASE,
)


class InventoryError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError(message)


def canonical_id(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip().startswith("/"), f"{field} must be an Azure resource ID")
    return value.strip().lower().rstrip("/")


def canonical_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def ensure_no_sensitive_keys(value: Any, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            require(not SENSITIVE_KEY_RE.search(str(key)), f"sensitive key marker detected at {path}.{key}")
            ensure_no_sensitive_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            ensure_no_sensitive_keys(item, f"{path}[{index}]")


def parse_resource_scope(resource_id: str) -> tuple[str, str]:
    match = RESOURCE_ID_RE.match(resource_id)
    require(match is not None, f"malformed resource ID: {resource_id}")
    return match.group("subscription").lower(), match.group("resource_group").lower()


def subscription_node_id(subscription_id: str) -> str:
    return f"/subscriptions/{subscription_id.lower()}"


def resource_group_node_id(subscription_id: str, resource_group: str) -> str:
    return f"/subscriptions/{subscription_id.lower()}/resourcegroups/{resource_group.lower()}"


def edge_id(source: str, relationship: str, target: str) -> str:
    material = f"{source}|{relationship}|{target}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def display_name_from_id(resource_id: str) -> str:
    return resource_id.rsplit("/", 1)[-1]


def resource_type_from_id(resource_id: str) -> str:
    marker = "/providers/"
    if marker not in resource_id:
        return "azure.scope/unresolved"
    provider_path = resource_id.split(marker, 1)[1].split("/")
    if len(provider_path) < 2:
        return "azure.resource/unresolved"
    namespace = provider_path[0]
    type_parts = provider_path[1::2]
    return "/".join([namespace, *type_parts]).lower()


class GraphBuilder:
    def __init__(self, observed_at_utc: str, subscriptions: set[str]) -> None:
        self.observed_at_utc = observed_at_utc
        self.subscriptions = subscriptions
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}
        self.limitations: set[str] = set()

    def add_node(
        self,
        node_id: str,
        *,
        kind: str,
        name: str,
        resource_type: str,
        subscription_id: str | None,
        resource_group: str | None,
        location: str | None = None,
        attributes: dict[str, Any] | None = None,
        observation_status: str = "observed",
    ) -> None:
        candidate = {
            "id": node_id,
            "kind": kind,
            "name": name,
            "type": resource_type,
            "subscription_id": subscription_id,
            "resource_group": resource_group,
            "location": location,
            "observation_status": observation_status,
            "attributes": attributes or {},
        }
        existing = self.nodes.get(node_id)
        if existing is None:
            self.nodes[node_id] = candidate
            return
        require(existing["kind"] == candidate["kind"], f"conflicting node kind for {node_id}")
        require(existing["type"] == candidate["type"], f"conflicting node type for {node_id}")
        promoted_to_observed = existing.get("observation_status") == "not_observed" and candidate.get("observation_status") == "observed"
        if promoted_to_observed:
            existing["observation_status"] = "observed"
            existing["name"] = candidate["name"]
            existing["location"] = candidate["location"] or existing.get("location")
        merged_attributes = dict(existing.get("attributes", {}))
        if promoted_to_observed:
            merged_attributes.pop("reference_only", None)
        for key, value in candidate["attributes"].items():
            if key in merged_attributes and merged_attributes[key] != value:
                merged_attributes[key] = {
                    "verification_status": "conflicting",
                    "values": sorted([merged_attributes[key], value], key=lambda item: json.dumps(item, sort_keys=True)),
                }
            else:
                merged_attributes[key] = value
        existing["attributes"] = merged_attributes

    def ensure_reference_node(self, resource_id: str) -> None:
        if resource_id in self.nodes:
            return
        subscription_id, resource_group = parse_resource_scope(resource_id)
        require(subscription_id in self.subscriptions, f"reference scope is outside explicit subscriptions: {resource_id}")
        self.add_scope_nodes(subscription_id, resource_group)
        self.add_node(
            resource_id,
            kind="resource",
            name=display_name_from_id(resource_id),
            resource_type=resource_type_from_id(resource_id),
            subscription_id=subscription_id,
            resource_group=resource_group,
            observation_status="not_observed",
            attributes={"reference_only": True},
        )
        self.limitations.add("Some relationship targets were referenced but not returned by the bounded resource query.")
        self.add_edge(resource_group_node_id(subscription_id, resource_group), "contains", resource_id)

    def add_scope_nodes(self, subscription_id: str, resource_group: str) -> None:
        require(subscription_id in self.subscriptions, f"record scope is outside explicit subscriptions: {subscription_id}")
        sub_id = subscription_node_id(subscription_id)
        rg_id = resource_group_node_id(subscription_id, resource_group)
        self.add_node(
            sub_id,
            kind="subscription",
            name=subscription_id,
            resource_type="microsoft.resources/subscriptions",
            subscription_id=subscription_id,
            resource_group=None,
        )
        self.add_node(
            rg_id,
            kind="resource_group",
            name=resource_group,
            resource_type="microsoft.resources/subscriptions/resourcegroups",
            subscription_id=subscription_id,
            resource_group=resource_group,
        )
        self.add_edge(sub_id, "contains", rg_id)

    def add_edge(self, source: str, relationship: str, target: str, attributes: dict[str, Any] | None = None) -> None:
        require(source != target, f"self edge is not allowed: {source}")
        identifier = edge_id(source, relationship, target)
        candidate = {
            "id": identifier,
            "source": source,
            "relationship": relationship,
            "target": target,
            "attributes": attributes or {},
        }
        existing = self.edges.get(identifier)
        if existing is None:
            self.edges[identifier] = candidate
            return
        require(existing == candidate, f"duplicate edge contains conflicting attributes: {identifier}")

    def build(self) -> dict[str, Any]:
        nodes = sorted(self.nodes.values(), key=lambda item: item["id"])
        edges = sorted(self.edges.values(), key=lambda item: (item["source"], item["relationship"], item["target"]))
        digest_payload = {"nodes": nodes, "edges": edges}
        digest = hashlib.sha256(json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return {
            "schema_version": OUTPUT_SCHEMA,
            "source_system": "azure_resource_graph",
            "observed_at_utc": self.observed_at_utc,
            "subscription_scope": sorted(self.subscriptions),
            "nodes": nodes,
            "edges": edges,
            "limitations": sorted(self.limitations),
            "graph_digest": digest,
        }


def require_records(payload: dict[str, Any], name: str) -> list[dict[str, Any]]:
    value = payload.get(name)
    require(isinstance(value, list), f"results.{name} must be an array")
    require(all(isinstance(item, dict) for item in value), f"results.{name} must contain objects")
    return value


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    require(isinstance(payload, dict), "input must be a JSON object")
    ensure_no_sensitive_keys(payload)
    metadata = payload.get("metadata")
    results = payload.get("results")
    require(isinstance(metadata, dict), "metadata must be an object")
    require(isinstance(results, dict), "results must be an object")
    observed_at_utc = canonical_text(metadata.get("observed_at_utc"))
    require(observed_at_utc is not None, "metadata.observed_at_utc is required")
    subscriptions_raw = metadata.get("subscriptions")
    require(isinstance(subscriptions_raw, list) and bool(subscriptions_raw), "metadata.subscriptions must be a non-empty array")
    subscriptions = {str(item).lower() for item in subscriptions_raw}
    require(metadata.get("query_complete") is True, "query_result_truncated_without_continuation_evidence")

    builder = GraphBuilder(observed_at_utc, subscriptions)

    for record in require_records(results, "resources"):
        resource_id = canonical_id(record.get("id"), "resources.id")
        subscription_id, resource_group = parse_resource_scope(resource_id)
        require(subscription_id == str(record.get("subscriptionId", "")).lower(), f"subscription mismatch for {resource_id}")
        require(resource_group == str(record.get("resourceGroup", "")).lower(), f"resource-group mismatch for {resource_id}")
        builder.add_scope_nodes(subscription_id, resource_group)
        attributes = {
            "kind": canonical_text(record.get("kind")),
            "sku_name": canonical_text(record.get("skuName")),
            "managed_by": canonical_text(record.get("managedBy")),
            "tags": record.get("tags") if isinstance(record.get("tags"), dict) else {},
        }
        attributes = {key: value for key, value in attributes.items() if value not in (None, {}, [])}
        builder.add_node(
            resource_id,
            kind="resource",
            name=str(record.get("name") or display_name_from_id(resource_id)),
            resource_type=str(record.get("type") or resource_type_from_id(resource_id)).lower(),
            subscription_id=subscription_id,
            resource_group=resource_group,
            location=canonical_text(record.get("location")),
            attributes=attributes,
        )
        builder.add_edge(resource_group_node_id(subscription_id, resource_group), "contains", resource_id)
        managed_by = canonical_text(record.get("managedBy"))
        if managed_by:
            managed_by_id = canonical_id(managed_by, "resources.managedBy")
            builder.ensure_reference_node(managed_by_id)
            builder.add_edge(resource_id, "uses", managed_by_id, {"basis": "managedBy"})

    for record in require_records(results, "vm_attachments"):
        vm_id = canonical_id(record.get("vmId"), "vm_attachments.vmId")
        builder.ensure_reference_node(vm_id)
        record_kind = record.get("recordKind")
        if record_kind == "vm_nic":
            nic_id = canonical_id(record.get("nicId"), "vm_attachments.nicId")
            builder.ensure_reference_node(nic_id)
            builder.add_edge(vm_id, "attached_to", nic_id, {"primary": bool(record.get("primary"))})
        elif record_kind == "vm_disk":
            disk_id = canonical_id(record.get("diskId"), "vm_attachments.diskId")
            builder.ensure_reference_node(disk_id)
            attrs = {"disk_role": str(record.get("diskRole") or "unknown")}
            if record.get("lun") is not None:
                attrs["lun"] = int(record["lun"])
            builder.add_edge(vm_id, "uses", disk_id, attrs)
        else:
            raise InventoryError(f"unsupported vm attachment recordKind: {record_kind}")

    for record in require_records(results, "nic_ip_configurations"):
        nic_id = canonical_id(record.get("nicId"), "nic_ip_configurations.nicId")
        builder.ensure_reference_node(nic_id)
        subscription_id, resource_group = parse_resource_scope(nic_id)
        ip_name = canonical_text(record.get("ipConfigurationName"))
        require(ip_name is not None, "ipConfigurationName is required")
        ip_node_id = f"{nic_id}/ipconfigurations/{ip_name.lower()}"
        private_ip = canonical_text(record.get("privateIpAddress"))
        if private_ip:
            try:
                ipaddress.ip_address(private_ip)
            except ValueError as exc:
                raise InventoryError(f"invalid private IP address: {private_ip}") from exc
        builder.add_node(
            ip_node_id,
            kind="resource",
            name=ip_name,
            resource_type="microsoft.network/networkinterfaces/ipconfigurations",
            subscription_id=subscription_id,
            resource_group=resource_group,
            attributes={
                key: value
                for key, value in {
                    "private_ip_address": private_ip,
                    "private_ip_allocation_method": canonical_text(record.get("privateIpAllocationMethod")),
                    "primary": bool(record.get("primary")),
                }.items()
                if value is not None
            },
        )
        builder.add_edge(nic_id, "contains", ip_node_id)

        for field, relationship in (("subnetId", "connected_to"), ("publicIpId", "exposes")):
            value = canonical_text(record.get(field))
            if value:
                target = canonical_id(value, f"nic_ip_configurations.{field}")
                builder.ensure_reference_node(target)
                builder.add_edge(ip_node_id, relationship, target)

        nic_nsg = canonical_text(record.get("nicNsgId"))
        if nic_nsg:
            target = canonical_id(nic_nsg, "nic_ip_configurations.nicNsgId")
            builder.ensure_reference_node(target)
            builder.add_edge(nic_id, "protected_by", target)

        backend_pool_ids = record.get("backendPoolIds") or []
        require(isinstance(backend_pool_ids, list), "backendPoolIds must be an array")
        for pool in backend_pool_ids:
            if isinstance(pool, dict):
                pool = pool.get("id")
            target = canonical_id(pool, "nic_ip_configurations.backendPoolIds")
            builder.ensure_reference_node(target)
            builder.add_edge(ip_node_id, "uses", target, {"basis": "load_balancer_backend_pool"})

    for record in require_records(results, "subnets"):
        vnet_id = canonical_id(record.get("vnetId"), "subnets.vnetId")
        subnet_id = canonical_id(record.get("subnetId"), "subnets.subnetId")
        builder.ensure_reference_node(vnet_id)
        subscription_id, resource_group = parse_resource_scope(subnet_id)
        prefixes: list[str] = []
        single_prefix = canonical_text(record.get("addressPrefix"))
        if single_prefix:
            prefixes.append(single_prefix)
        multi_prefixes = record.get("addressPrefixes") or []
        require(isinstance(multi_prefixes, list), "addressPrefixes must be an array")
        prefixes.extend(str(item) for item in multi_prefixes if str(item).strip())
        for prefix in prefixes:
            try:
                ipaddress.ip_network(prefix, strict=False)
            except ValueError as exc:
                raise InventoryError(f"invalid subnet prefix: {prefix}") from exc
        builder.add_node(
            subnet_id,
            kind="resource",
            name=str(record.get("subnetName") or display_name_from_id(subnet_id)),
            resource_type="microsoft.network/virtualnetworks/subnets",
            subscription_id=subscription_id,
            resource_group=resource_group,
            attributes={"address_prefixes": sorted(set(prefixes))},
        )
        builder.add_edge(vnet_id, "contains", subnet_id)
        for field, relationship in (("subnetNsgId", "protected_by"), ("routeTableId", "uses")):
            value = canonical_text(record.get(field))
            if value:
                target = canonical_id(value, f"subnets.{field}")
                builder.ensure_reference_node(target)
                builder.add_edge(subnet_id, relationship, target)

    graph = builder.build()
    node_ids = {node["id"] for node in graph["nodes"]}
    for edge in graph["edges"]:
        require(edge["source"] in node_ids, f"edge source is missing: {edge['source']}")
        require(edge["target"] in node_ids, f"edge target is missing: {edge['target']}")
    return graph


def validate_contract(document: dict[str, Any]) -> None:
    require(document.get("schema_version") == CONTRACT_SCHEMA, "unexpected contract schema")
    require(document.get("status") == "repository_adapter_only", "contract must remain repository-only")
    source = document.get("source")
    require(isinstance(source, dict), "source must be an object")
    require(source.get("service") == "azure_resource_graph", "source service mismatch")
    require(source.get("rest_api_version") == "2024-04-01", "REST API version mismatch")
    require(source.get("query_scope_requires_explicit_subscription_ids") is True, "explicit subscriptions must be required")
    require(source.get("default_subscription_inference_allowed") is False, "default subscription inference must be denied")
    package = document.get("query_package")
    require(isinstance(package, dict), "query_package must be an object")
    require(package.get("query_execution_authorized") is False, "query execution must remain unauthorized")
    authority = document.get("authority")
    require(isinstance(authority, dict), "authority must be an object")
    require(authority.get("repository_implementation_authorized") is True, "repository implementation must be authorized")
    require(authority.get("pull_request_creation_authorized") is True, "pull request creation must be authorized")
    for key, value in authority.items():
        if key not in {"repository_implementation_authorized", "pull_request_creation_authorized"}:
            require(value is False, f"authority.{key} must remain false")
    distinctions = document.get("canonical_distinctions")
    require(isinstance(distinctions, list), "canonical_distinctions must be an array")
    for marker in (
        "resource_graph_observed != deployed_from_current_main",
        "relationship_inferred != network_path_verified",
        "not_observed != absent",
        "adapter_implemented != Azure_query_executed",
    ):
        require(marker in distinctions, f"missing distinction: {marker}")
    failure = document.get("failure_and_rollback")
    require(isinstance(failure, dict), "failure_and_rollback must be an object")
    require(failure.get("cleanup_authorized") is False, "cleanup must remain unauthorized")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InventoryError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InventoryError(f"invalid JSON in {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize bounded Azure Resource Graph query results.")
    parser.add_argument("--input", type=Path, help="JSON payload containing metadata and named query results")
    parser.add_argument("--output", type=Path, help="Destination for normalized infrastructure graph JSON")
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(".project/contracts/azure-resource-graph-semantic-inventory.json"),
    )
    parser.add_argument("--validate-contract-only", action="store_true")
    args = parser.parse_args()

    try:
        validate_contract(load_json(args.contract))
        if args.validate_contract_only:
            print("azure resource graph semantic inventory contract validation passed")
            return 0
        require(args.input is not None, "--input is required")
        graph = normalize(load_json(args.input))
        encoded = json.dumps(graph, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
    except (InventoryError, OSError) as exc:
        print(f"azure resource graph semantic inventory failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
