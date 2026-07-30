#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "servicetracer.azure-mcp-lab-factory-tools.v1"
STATUS = "local_read_only_tools_implemented_not_connected"
BASE_COMMIT = "4136a47d9aa80da99e3849fc721bab55a883b20e"
ALLOWED_TOOLS = [
    "get_current_reality",
    "list_lab_profiles",
    "prepare_lab_request",
]
READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
}
FALSE_AUTHORITY_FIELDS = {
    "live_get_current_reality_execution_authorized",
    "azure_authentication_or_query_authorized",
    "azure_mutation_authorized",
    "model_call_authorized",
    "remote_mcp_deployment_authorized",
    "chatgpt_connection_authorized",
    "rbac_mutation_authorized",
    "cleanup_authorized",
}


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def object_field(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def list_field(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    require(isinstance(value, list), f"{field} must be an array")
    require(allow_empty or bool(value), f"{field} must not be empty")
    return value


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def validate_contract(document: dict[str, Any]) -> None:
    require(document.get("schema_version") == SCHEMA, "unexpected schema_version")
    require(document.get("status") == STATUS, "unexpected status")

    distinctions = set(
        list_field(document.get("canonical_distinctions"), "canonical_distinctions")
    )
    for marker in (
        "historical_single_tool_contract != current_server_inventory",
        "profile_listed != released_lab",
        "prepared_request != ARM_what_if",
        "prepared_request != deployment_authorized",
        "catalog_allowed_location != live_capacity_available",
        "parameter_validated != parameter_value_persisted",
        "local_tool_implemented != ChatGPT_connected",
        "cleanup_defined != cleanup_verified",
    ):
        require(marker in distinctions, f"missing distinction: {marker}")

    baseline = object_field(document.get("repository_baseline"), "repository_baseline")
    require(
        baseline.get("repository") == "anthonyedgar30000/azure-iac-msp-lab",
        "repository mismatch",
    )
    require(baseline.get("base_branch") == "main", "base branch mismatch")
    require(baseline.get("base_commit") == BASE_COMMIT, "base commit mismatch")
    require(
        baseline.get("latest_merged_pull_request") == 214,
        "latest merged PR mismatch",
    )
    require(
        list_field(
            baseline.get("open_pull_requests_observed_before_branch"),
            "open PR baseline",
            allow_empty=True,
        )
        == [],
        "open PR baseline changed",
    )

    supersession = object_field(document.get("supersession"), "supersession")
    require(
        supersession.get("historical_contract")
        == ".project/contracts/azure-mcp-reality-bridge.json",
        "historical contract path mismatch",
    )
    require(
        supersession.get("historical_tool_admission_preserved") is True,
        "historical admission must remain preserved",
    )
    require(
        supersession.get("historical_observation_evidence_rewritten") is False,
        "historical evidence must not be rewritten",
    )

    architecture = object_field(document.get("architecture"), "architecture")
    require(
        architecture.get("network_bind") == "127.0.0.1:8000",
        "server must remain loopback-only",
    )
    require(
        architecture.get("remote_endpoint_deployed") is False,
        "remote endpoint must remain undeployed",
    )
    require(
        architecture.get("azure_execution_path_added") is False,
        "Azure execution path must not be added",
    )

    admission = object_field(document.get("tool_admission"), "tool_admission")
    require(admission.get("default_policy") == "deny", "default policy must deny")
    require(
        admission.get("allowed_tool_names") == ALLOWED_TOOLS,
        "exact tool allowlist mismatch",
    )
    require(
        admission.get("server_version") == "azure-mcp-reality/0.2.0",
        "server version mismatch",
    )
    inventory = list_field(admission.get("tool_inventory"), "tool_inventory")
    require(
        [tool.get("name") for tool in inventory] == ALLOWED_TOOLS,
        "tool inventory order or names changed",
    )
    require(
        admission.get("tool_inventory_digest") == canonical_digest(inventory),
        "tool inventory digest mismatch",
    )

    by_name = {tool["name"]: object_field(tool, f"tool {tool['name']}") for tool in inventory}
    reality = by_name["get_current_reality"]
    require(reality.get("model_inputs") == [], "reality tool must not accept model scope")
    require(reality.get("azure_queries_possible") is True, "reality query boundary missing")
    require(reality["annotations"].get("openWorldHint") is True, "reality tool must remain open-world")

    profiles = by_name["list_lab_profiles"]
    require(profiles.get("model_inputs") == [], "profile list must accept no inputs")
    require(profiles.get("azure_queries_possible") is False, "profile list must be cloud-free")
    require(profiles["annotations"].get("openWorldHint") is False, "profile list must be closed-world")

    prepare = by_name["prepare_lab_request"]
    require(
        prepare.get("model_inputs")
        == [
            "profile_id",
            "environment",
            "location",
            "ttl_hours",
            "version",
            "request_id",
            "parameters",
        ],
        "prepare tool input inventory mismatch",
    )
    require(prepare.get("azure_queries_possible") is False, "prepare tool must be cloud-free")
    require(prepare.get("parameter_values_echoed") is False, "parameter values must not be echoed")
    require(prepare["annotations"].get("openWorldHint") is False, "prepare tool must be closed-world")

    for name, tool in by_name.items():
        annotations = object_field(tool.get("annotations"), f"{name}.annotations")
        for key, expected in READ_ONLY_ANNOTATIONS.items():
            require(annotations.get(key) is expected, f"{name}.{key} changed")
        for key in (
            "azure_mutations_performed",
            "writes_files",
            "returns_secret_values",
        ):
            require(tool.get(key) is False, f"{name}.{key} must remain false")

    boundary = object_field(document.get("lab_factory_boundary"), "lab_factory_boundary")
    require(boundary.get("profile") == "servicetracer-demo-api@1.0.0", "profile changed")
    require(boundary.get("release_state") == "candidate", "profile state changed")
    require(boundary.get("allowed_locations") == ["westus2"], "location allowlist changed")
    ttl = object_field(boundary.get("ttl_hours"), "ttl_hours")
    require(ttl == {"minimum": 1, "default": 8, "maximum": 24}, "TTL boundary changed")
    require(
        boundary.get("cleanup_automatic_execution_enabled") is False,
        "automatic cleanup must remain disabled",
    )
    for key in (
        "parameter_values_returned",
        "azure_queries_performed_by_lab_tools",
        "azure_mutations_performed_by_lab_tools",
    ):
        require(boundary.get(key) is False, f"lab_factory_boundary.{key} must remain false")

    identity = object_field(
        document.get("identity_and_permissions"),
        "identity_and_permissions",
    )
    for key in (
        "lab_tools_require_azure_identity",
        "new_azure_rbac_required",
        "managed_identity_created",
        "secret_created_or_persisted",
    ):
        require(identity.get(key) is False, f"identity_and_permissions.{key} must remain false")

    authority = object_field(document.get("authority"), "authority")
    for key in (
        "repository_branch_and_files_authorized",
        "pull_request_creation_authorized",
        "ordinary_exact_head_ci_authorized",
        "pull_request_merge_authorized",
    ):
        require(authority.get(key) is True, f"authority.{key} must be true")
    for key in FALSE_AUTHORITY_FIELDS:
        require(authority.get(key) is False, f"authority.{key} must remain false")

    cost = object_field(document.get("cost_and_quota"), "cost_and_quota")
    require(
        cost.get("expected_recurring_azure_resource_cost_delta_cad") == 0,
        "repository increment recurring Azure cost must be CAD $0",
    )
    require(cost.get("actual_azure_cost_freshly_observed") is False, "actual cost must remain unobserved")
    require(cost.get("azure_quota_freshly_observed") is False, "quota must remain unobserved")

    failure = object_field(document.get("failure_and_rollback"), "failure_and_rollback")
    fail_closed = set(list_field(failure.get("fail_closed_conditions"), "fail_closed_conditions"))
    for marker in (
        "tool_inventory_changed",
        "unknown_profile",
        "unapproved_location",
        "ttl_outside_profile_boundary",
        "fixed_parameter_override",
        "write_or_secret_capability_detected",
    ):
        require(marker in fail_closed, f"missing fail-closed marker: {marker}")
    require(failure.get("cleanup_authorized") is False, "cleanup must remain unauthorized")


def load_and_validate(path: Path) -> None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing contract: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON: {exc}") from exc
    validate_contract(object_field(document, str(path)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contract",
        nargs="?",
        type=Path,
        default=Path(".project/contracts/azure-mcp-lab-factory-tools-v1.json"),
    )
    args = parser.parse_args()
    try:
        load_and_validate(args.contract)
    except (ContractError, OSError) as exc:
        print(f"azure-mcp lab-factory-tools contract validation failed: {exc}")
        return 1
    print("azure-mcp lab-factory-tools contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
