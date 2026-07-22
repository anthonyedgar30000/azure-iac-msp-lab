from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any

CONTRACT_SCHEMA = "servicetracer.collector-recovery-evidence-contract.v1"
PACKAGE_SCHEMA = "servicetracer.collector-recovery-evidence.v1"
TARGET = {
    "resource_group": "rg-servicetracer-dev-westus2",
    "collector_vm": "vm-stcollector-mst-dev",
    "collector_nic": "nic-stcollector-mst-dev",
    "collector_evidence_disk": "disk-stcollector-evidence-mst-dev",
    "collector_os_disk": "disk-stcollector-os-mst-dev",
    "evidence_mount": "/var/lib/servicetracer",
}
PHASES = {
    "guest_and_control_plane_preflight": {"guest_preflight", "azure_control_plane_preflight", "cleanup_commitment"},
    "quiesce_and_deallocate_source": {"operation_attempt", "state_observation", "consistency_checkpoint"},
    "create_recovery_points": {"operation_attempt", "state_observation", "consistency_checkpoint"},
    "verify_recovery_points": {"state_observation", "integrity_verification"},
    "isolated_snapshot_boot_rehearsal": {"operation_attempt", "state_observation", "integrity_verification"},
    "teardown_isolated_rehearsal": {"operation_attempt", "state_observation", "cleanup_verification"},
    "remove_old_compute": {"operation_attempt", "state_observation", "decision"},
    "deploy_replacement_compute": {"operation_attempt", "state_observation"},
    "restore_identity_and_rbac": {"operation_attempt", "state_observation"},
    "post_change_verification": {"guest_preflight", "azure_control_plane_preflight", "integrity_verification"},
    "human_recovery_acceptance": {"decision"},
    "cleanup_temporary_recovery_resources": {"cleanup_commitment", "operation_attempt", "cleanup_verification"},
    "rollback_recovery": {
        "operation_attempt", "state_observation", "guest_preflight",
        "azure_control_plane_preflight", "integrity_verification", "decision",
    },
}
CLAIMS = {"snapshot_recoverability", "trusted_launch_bootability", "rollback", "recovery"}
AZURE_ID = re.compile(
    r"^/subscriptions/[0-9a-fA-F-]{36}/resourceGroups/[^/]+/providers/"
    r"Microsoft\.[A-Za-z]+/[A-Za-z]+/[^/]+$"
)
UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


class EvidenceValidationError(RuntimeError):
    pass


def obj(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceValidationError(f"{field} must be an object")
    return value


def items(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceValidationError(f"{field} must be a list")
    return value


def text(value: Any, field: str, maximum: int | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceValidationError(f"{field} must be a non-empty string")
    result = value.strip()
    if maximum is not None and len(result) > maximum:
        raise EvidenceValidationError(f"{field} exceeds maximum length {maximum}")
    return result


def integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise EvidenceValidationError(f"{field} must be an integer")
    return value


def exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise EvidenceValidationError(
            f"{field} fields mismatch: missing={sorted(expected - set(value))}, "
            f"unexpected={sorted(set(value) - expected)}"
        )


def require(value: Any, expected: Any, field: str) -> None:
    if value != expected:
        raise EvidenceValidationError(f"{field} changed")


def timestamp(value: Any, field: str) -> datetime:
    value = text(value, field)
    if not UTC_Z.fullmatch(value):
        raise EvidenceValidationError(f"{field} must be RFC3339 UTC with a trailing Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo != timezone.utc:
        raise EvidenceValidationError(f"{field} must be UTC")
    return parsed


def patterned(value: Any, field: str, pattern: str) -> str:
    value = text(value, field)
    if re.fullmatch(pattern, value) is None:
        raise EvidenceValidationError(f"{field} does not match the contract pattern")
    return value


def canonical_size(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def has_marker(value: Any, marker: str) -> bool:
    if isinstance(value, dict):
        return any(has_marker(item, marker) for item in value.values())
    if isinstance(value, list):
        return any(has_marker(item, marker) for item in value)
    return value == marker


def safe_json(
    value: Any,
    *,
    field: str,
    policy: dict[str, Any],
    limits: dict[str, Any],
    depth: int = 0,
) -> None:
    if depth > integer(limits["maximum_nested_depth"], "maximum_nested_depth"):
        raise EvidenceValidationError(f"{field} exceeds maximum nested depth")
    max_items = integer(limits["maximum_nested_items"], "maximum_nested_items")
    max_text = integer(limits["maximum_text_length"], "maximum_text_length")
    forbidden_keys = [text(v, "forbidden key").lower() for v in items(policy["forbidden_field_name_fragments"], "forbidden keys")]
    forbidden_prefixes = [text(v, "forbidden prefix") for v in items(policy["forbidden_value_prefixes"], "forbidden prefixes")]

    if isinstance(value, dict):
        if len(value) > max_items:
            raise EvidenceValidationError(f"{field} contains too many object fields")
        for key, child in value.items():
            key = text(key, f"{field}.key", 256)
            if any(fragment in key.lower() for fragment in forbidden_keys):
                raise EvidenceValidationError(f"{field}.{key} is a forbidden secret-like field")
            safe_json(child, field=f"{field}.{key}", policy=policy, limits=limits, depth=depth + 1)
        return
    if isinstance(value, list):
        if len(value) > max_items:
            raise EvidenceValidationError(f"{field} contains too many list items")
        for index, child in enumerate(value):
            safe_json(child, field=f"{field}[{index}]", policy=policy, limits=limits, depth=depth + 1)
        return
    if isinstance(value, str):
        if len(value) > max_text:
            raise EvidenceValidationError(f"{field} exceeds maximum text length")
        if any(value.startswith(prefix) for prefix in forbidden_prefixes):
            raise EvidenceValidationError(f"{field} contains a forbidden credential prefix")
        return
    if value is None or isinstance(value, (bool, int, float)):
        return
    raise EvidenceValidationError(f"{field} contains an unsupported JSON value")


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    require(contract.get("schema_version"), CONTRACT_SCHEMA, "schema_version")
    require(contract.get("state"), "design_only", "state")
    authority = obj(contract.get("authority"), "authority")
    for field in (
        "active_workflow_present", "dispatch_authorized",
        "azure_authentication_authorized", "azure_mutations_authorized",
        "evidence_collection_commands_implemented",
    ):
        require(authority.get(field), False, f"authority.{field}")
    require(authority.get("promotion_requires_separate_pull_request"), True, "promotion gate")
    text(authority.get("claim_boundary"), "authority.claim_boundary")

    target = obj(contract.get("target"), "target")
    for field, expected in TARGET.items():
        require(target.get(field), expected, f"target.{field}")
    require(target.get("exact_resource_ids_required_at_collection_time"), True, "target exact IDs")

    package = obj(contract.get("package"), "package")
    require(package.get("schema_version"), PACKAGE_SCHEMA, "package.schema_version")
    for field in ("maximum_package_bytes", "maximum_records", "maximum_nested_depth", "maximum_nested_items", "maximum_text_length"):
        if integer(package.get(field), f"package.{field}") <= 0:
            raise EvidenceValidationError(f"package.{field} must be positive")
    if package["maximum_package_bytes"] > 1048576 or package["maximum_records"] > 512:
        raise EvidenceValidationError("package limits exceed the bounded v1 ceiling")
    require(package.get("timestamp_format"), "RFC3339_UTC_Z", "timestamp_format")
    for field in ("maintenance_correlation_id_pattern", "record_id_pattern", "command_identity_pattern", "sha256_pattern"):
        re.compile(text(package.get(field), f"package.{field}"))
    for field in (
        "complete_requires_all_declared_phase_evidence",
        "failed_or_aborted_requires_terminal_decision",
        "operational_claim_requires_complete_package",
    ):
        require(package.get(field), True, f"package.{field}")

    top = {
        "schema_version", "package_id", "generated_at", "maintenance_correlation_id",
        "target", "declared_phase_ids", "package_status", "records", "claims", "claim_boundary",
    }
    require(set(items(package.get("required_top_level_fields"), "required_top_level_fields")), top, "top-level fields")
    record_fields = {
        "record_id", "record_type", "phase_id", "observed_at", "command_identity",
        "exit_status", "status", "target_resource_id", "before_state", "after_state",
        "evidence_sha256", "summary", "details", "redactions",
    }
    require(set(items(package.get("required_record_fields"), "required_record_fields")), record_fields, "record fields")
    require(set(items(package.get("allowed_record_fields"), "allowed_record_fields")), record_fields, "allowed record fields")
    observed_phases = {
        phase: set(items(required, f"phase_requirements.{phase}"))
        for phase, required in obj(contract.get("phase_requirements"), "phase_requirements").items()
    }
    require(observed_phases, PHASES, "phase requirements")
    require(set(obj(contract.get("claim_requirements"), "claim_requirements")), CLAIMS, "claim requirements")

    redaction = obj(contract.get("redaction_policy"), "redaction_policy")
    require(redaction.get("redaction_marker"), "[REDACTED]", "redaction marker")
    require(redaction.get("redacted_value_requires_sha256"), True, "redaction digest")
    require(redaction.get("raw_stdout_stderr_allowed"), False, "raw output boundary")
    require(redaction.get("command_identity_must_be_logical_name_not_raw_command_line"), True, "command identity boundary")
    require(redaction.get("resource_ids_must_be_preserved"), True, "resource ID boundary")

    failure = obj(contract.get("failure_and_abort_requirements"), "failure requirements")
    require(set(items(failure.get("required_failed_or_aborted_record_types"), "failure record types")), {"operation_attempt", "decision"}, "failure record types")
    require(
        set(items(failure.get("decision_details_required"), "decision details")),
        {"decision", "reason", "authority", "safe_next_step", "rollback_required"},
        "decision details",
    )
    cleanup = obj(contract.get("cleanup_requirements"), "cleanup requirements")
    require(cleanup.get("maximum_retention_hours"), 24, "cleanup retention")
    require(cleanup.get("maximum_approved_cost_cad"), 10.0, "cleanup cost")
    return {
        "contract_valid": True, "state": "design_only",
        "active_workflow_present": False, "dispatch_authorized": False,
        "azure_authentication_authorized": False, "azure_mutations_authorized": False,
        "phase_count": len(PHASES), "claim_count": len(CLAIMS),
    }


def validate_target(target: dict[str, Any], contract_target: dict[str, Any]) -> set[str]:
    exact_keys(target, {
        "resource_group", "collector_vm", "collector_vm_resource_id",
        "collector_nic_resource_id", "collector_evidence_disk_resource_id",
        "collector_os_disk_resource_id", "evidence_mount",
    }, "target")
    for field in ("resource_group", "collector_vm", "evidence_mount"):
        require(target.get(field), contract_target.get(field), f"target.{field}")
    names = {
        "collector_vm_resource_id": contract_target["collector_vm"],
        "collector_nic_resource_id": contract_target["collector_nic"],
        "collector_evidence_disk_resource_id": contract_target["collector_evidence_disk"],
        "collector_os_disk_resource_id": contract_target["collector_os_disk"],
    }
    result: set[str] = set()
    for field, expected_name in names.items():
        resource_id = text(target.get(field), f"target.{field}", 1024)
        if AZURE_ID.fullmatch(resource_id) is None:
            raise EvidenceValidationError(f"target.{field} must be a complete Azure resource ID")
        if resource_id.rstrip("/").rsplit("/", 1)[-1] != expected_name:
            raise EvidenceValidationError(f"target.{field} does not identify {expected_name}")
        if f"/resourceGroups/{contract_target['resource_group']}/" not in resource_id:
            raise EvidenceValidationError(f"target.{field} belongs to the wrong resource group")
        result.add(resource_id)
    return result


def validate_record(
    record: dict[str, Any],
    *,
    index: int,
    contract: dict[str, Any],
    declared_phases: set[str],
    generated_at: datetime,
    resource_ids: set[str],
) -> tuple[str, str, str]:
    package = obj(contract["package"], "package")
    policy = obj(contract["redaction_policy"], "redaction_policy")
    prefix = f"records[{index}]"
    exact_keys(record, set(package["required_record_fields"]), prefix)
    record_id = patterned(record.get("record_id"), f"{prefix}.record_id", package["record_id_pattern"])
    record_type = text(record.get("record_type"), f"{prefix}.record_type")
    if record_type not in set(package["record_types"]):
        raise EvidenceValidationError(f"{prefix}.record_type is unsupported")
    phase_id = text(record.get("phase_id"), f"{prefix}.phase_id")
    if phase_id not in declared_phases:
        raise EvidenceValidationError(f"{prefix}.phase_id was not declared")
    if timestamp(record.get("observed_at"), f"{prefix}.observed_at") > generated_at:
        raise EvidenceValidationError(f"{prefix}.observed_at is after package generation")

    command = patterned(record.get("command_identity"), f"{prefix}.command_identity", package["command_identity_pattern"])
    if any(char in command for char in (" ", ";", "|", "&", "$", "`", "\n", "\r")):
        raise EvidenceValidationError(f"{prefix}.command_identity must be a logical name, not a command line")
    exit_status = integer(record.get("exit_status"), f"{prefix}.exit_status")
    if not -255 <= exit_status <= 255:
        raise EvidenceValidationError(f"{prefix}.exit_status is outside the bounded range")
    status = text(record.get("status"), f"{prefix}.status")
    if status not in set(package["record_statuses"]):
        raise EvidenceValidationError(f"{prefix}.status is unsupported")
    if status == "passed" and exit_status != 0:
        raise EvidenceValidationError(f"{prefix} cannot pass with a non-zero exit status")

    target_id = text(record.get("target_resource_id"), f"{prefix}.target_resource_id", 1024)
    if target_id not in resource_ids:
        raise EvidenceValidationError(f"{prefix}.target_resource_id is outside the target boundary")
    for field in ("before_state", "after_state", "details"):
        value = obj(record.get(field), f"{prefix}.{field}")
        safe_json(value, field=f"{prefix}.{field}", policy=policy, limits=package)
    patterned(record.get("evidence_sha256"), f"{prefix}.evidence_sha256", package["sha256_pattern"])
    text(record.get("summary"), f"{prefix}.summary", 512)

    redactions = items(record.get("redactions"), f"{prefix}.redactions")
    for redaction_index, value in enumerate(redactions):
        redaction = obj(value, f"{prefix}.redactions[{redaction_index}]")
        exact_keys(redaction, {"field_path", "marker", "original_sha256"}, f"{prefix}.redactions[{redaction_index}]")
        text(redaction.get("field_path"), "redaction.field_path", 512)
        require(redaction.get("marker"), "[REDACTED]", "redaction.marker")
        patterned(redaction.get("original_sha256"), "redaction.original_sha256", package["sha256_pattern"])
    if any(has_marker(record[field], "[REDACTED]") for field in ("before_state", "after_state", "details")) and not redactions:
        raise EvidenceValidationError(f"{prefix} contains redacted values without digest metadata")
    return record_id, record_type, status
