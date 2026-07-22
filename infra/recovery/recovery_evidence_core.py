from __future__ import annotations

from datetime import datetime, timezone
import json
import math
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
PACKAGE_STATUSES = {"complete", "incomplete", "failed", "aborted", "superseded"}
RECORD_STATUSES = {"passed", "failed", "aborted", "observed", "not_applicable"}
CLAIM_STATUSES = {"not_claimed", "unverified", "failed", "verified"}
RECORD_TYPES = {
    "guest_preflight", "azure_control_plane_preflight", "operation_attempt",
    "state_observation", "consistency_checkpoint", "integrity_verification",
    "cleanup_commitment", "cleanup_verification", "decision",
}
MAINTENANCE_ID_PATTERN = r"^[A-Z0-9][A-Z0-9._:-]{7,127}$"
RECORD_ID_PATTERN = r"^[a-z0-9][a-z0-9._:-]{7,127}$"
COMMAND_ID_PATTERN = r"^[a-z0-9][a-z0-9._:-]{2,127}$"
SHA256_PATTERN = r"^[0-9a-f]{64}$"
FORBIDDEN_FIELD_FRAGMENTS = {
    "password", "passwd", "secret", "token", "credential", "private_key",
    "client_secret", "connection_string", "sas_key", "access_key",
}
FORBIDDEN_VALUE_PREFIXES = {
    "Bearer ", "SharedAccessSignature ", "AccountKey=", "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----", "-----BEGIN OPENSSH PRIVATE KEY-----",
}
PROHIBITED_FAILURE_BEHAVIOR = {
    "silent retry", "unbounded retry", "automatic authority escalation",
    "claiming recovery without post-change verification",
    "deleting recovery artifacts before an accepted terminal decision",
}
RECORD_DETAIL_REQUIREMENTS = {
    "guest_preflight": {"service_state", "health_status", "evidence_mount", "filesystem_uuid", "recent_evidence_readable"},
    "azure_control_plane_preflight": {"vm_power_state", "nic_delete_option", "evidence_disk_delete_option", "os_disk_public_network_access", "observed_role_assignments"},
    "operation_attempt": {"operation", "requested_by", "authorization_reference"},
    "state_observation": {"observed_state", "source"},
    "consistency_checkpoint": {"checkpoint_name", "consistent", "evidence_references"},
    "integrity_verification": {"verification_name", "passed", "checks"},
    "cleanup_commitment": {"owner", "deadline", "maximum_retention_hours", "approved_cost_ceiling_cad"},
    "cleanup_verification": {"removed_resource_ids", "retained_resource_ids", "verified_at", "verifier_identity", "actual_temporary_cost_cad"},
    "decision": {"decision", "reason", "authority", "safe_next_step", "rollback_required"},
}
CLAIM_REQUIREMENTS = {
    "snapshot_recoverability": {
        "required_phases": {"verify_recovery_points", "human_recovery_acceptance"},
        "required_record_types": {"integrity_verification", "decision"},
    },
    "trusted_launch_bootability": {
        "required_phases": {"isolated_snapshot_boot_rehearsal", "human_recovery_acceptance"},
        "required_record_types": {"state_observation", "integrity_verification", "decision"},
    },
    "rollback": {
        "required_phases": {"rollback_recovery", "human_recovery_acceptance"},
        "required_record_types": {
            "operation_attempt", "state_observation", "guest_preflight",
            "azure_control_plane_preflight", "integrity_verification", "decision",
        },
    },
    "recovery": {
        "required_phases": {
            "guest_and_control_plane_preflight", "verify_recovery_points",
            "isolated_snapshot_boot_rehearsal", "teardown_isolated_rehearsal",
            "post_change_verification", "human_recovery_acceptance",
            "cleanup_temporary_recovery_resources",
        },
        "required_record_types": {
            "guest_preflight", "azure_control_plane_preflight", "integrity_verification",
            "cleanup_verification", "decision",
        },
    },
}
AZURE_ID = re.compile(
    r"^/subscriptions/(?P<subscription>[0-9a-fA-F-]{36})/resourceGroups/(?P<resource_group>[^/]+)/providers/"
    r"(?P<provider>Microsoft\.[A-Za-z]+)/(?P<resource_type>[A-Za-z]+)/(?P<name>[^/]+)$"
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


def number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise EvidenceValidationError(f"{field} must be finite")
    return result


def boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceValidationError(f"{field} must be a boolean")
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
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise EvidenceValidationError(f"{field} is invalid") from exc
    if parsed.tzinfo != timezone.utc:
        raise EvidenceValidationError(f"{field} must be UTC")
    return parsed


def patterned(value: Any, field: str, pattern: str) -> str:
    value = text(value, field)
    if re.fullmatch(pattern, value) is None:
        raise EvidenceValidationError(f"{field} does not match the contract pattern")
    return value


def canonical_size(value: Any) -> int:
    try:
        rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError("evidence package is not canonical JSON") from exc
    return len(rendered.encode())


def marker_paths(value: Any, marker: str, *, field: str) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            child_field = f"{field}.{key}" if field else str(key)
            found.update(marker_paths(child, marker, field=child_field))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.update(marker_paths(child, marker, field=f"{field}[{index}]"))
    elif value == marker:
        found.add(field)
    return found


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
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EvidenceValidationError(f"{field} contains a non-finite number")
        return
    if value is None or isinstance(value, (bool, int)):
        return
    raise EvidenceValidationError(f"{field} contains an unsupported JSON value")


def _normalize_claim_requirements(value: dict[str, Any]) -> dict[str, dict[str, set[str]]]:
    result: dict[str, dict[str, set[str]]] = {}
    for claim, requirements_value in value.items():
        requirements = obj(requirements_value, f"claim_requirements.{claim}")
        exact_keys(requirements, {"required_phases", "required_record_types"}, f"claim_requirements.{claim}")
        result[claim] = {
            "required_phases": set(items(requirements["required_phases"], f"claim_requirements.{claim}.required_phases")),
            "required_record_types": set(items(requirements["required_record_types"], f"claim_requirements.{claim}.required_record_types")),
        }
    return result


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
    require(target.get("single_subscription_boundary_required"), True, "target subscription boundary")

    package = obj(contract.get("package"), "package")
    require(package.get("schema_version"), PACKAGE_SCHEMA, "package.schema_version")
    exact_limits = {
        "maximum_package_bytes": 524288,
        "maximum_records": 256,
        "maximum_nested_depth": 6,
        "maximum_nested_items": 128,
        "maximum_text_length": 4096,
    }
    for field, expected in exact_limits.items():
        require(package.get(field), expected, f"package.{field}")
    require(package.get("timestamp_format"), "RFC3339_UTC_Z", "timestamp_format")
    require(package.get("maintenance_correlation_id_pattern"), MAINTENANCE_ID_PATTERN, "maintenance ID pattern")
    require(package.get("record_id_pattern"), RECORD_ID_PATTERN, "record ID pattern")
    require(package.get("command_identity_pattern"), COMMAND_ID_PATTERN, "command identity pattern")
    require(package.get("sha256_pattern"), SHA256_PATTERN, "SHA-256 pattern")
    require(set(items(package.get("package_statuses"), "package_statuses")), PACKAGE_STATUSES, "package statuses")
    require(set(items(package.get("record_statuses"), "record_statuses")), RECORD_STATUSES, "record statuses")
    require(set(items(package.get("claim_statuses"), "claim_statuses")), CLAIM_STATUSES, "claim statuses")
    require(set(items(package.get("record_types"), "record_types")), RECORD_TYPES, "record types")
    for field in (
        "complete_requires_all_declared_phase_evidence",
        "failed_or_aborted_requires_terminal_decision",
        "operational_claim_requires_complete_package",
    ):
        require(package.get(field), True, f"package.{field}")

    top = {
        "schema_version", "package_id", "generated_at", "maintenance_correlation_id",
        "target", "declared_phase_ids", "package_status", "supersession", "records",
        "claims", "claim_boundary",
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
    require(_normalize_claim_requirements(obj(contract.get("claim_requirements"), "claim_requirements")), CLAIM_REQUIREMENTS, "claim requirements")

    details = {
        record_type: set(items(required, f"record_detail_requirements.{record_type}"))
        for record_type, required in obj(contract.get("record_detail_requirements"), "record_detail_requirements").items()
    }
    require(details, RECORD_DETAIL_REQUIREMENTS, "record detail requirements")

    redaction = obj(contract.get("redaction_policy"), "redaction_policy")
    require(set(items(redaction.get("forbidden_field_name_fragments"), "forbidden fragments")), FORBIDDEN_FIELD_FRAGMENTS, "forbidden fragments")
    require(set(items(redaction.get("forbidden_value_prefixes"), "forbidden prefixes")), FORBIDDEN_VALUE_PREFIXES, "forbidden prefixes")
    require(redaction.get("redaction_marker"), "[REDACTED]", "redaction marker")
    for field in (
        "redacted_value_requires_sha256", "command_identity_must_be_logical_name_not_raw_command_line",
        "resource_ids_must_be_preserved", "redaction_paths_must_exactly_match_markers",
    ):
        require(redaction.get(field), True, f"redaction_policy.{field}")
    require(redaction.get("raw_stdout_stderr_allowed"), False, "raw output boundary")

    failure = obj(contract.get("failure_and_abort_requirements"), "failure requirements")
    require(set(items(failure.get("required_failed_or_aborted_record_types"), "failure record types")), {"operation_attempt", "decision"}, "failure record types")
    require(set(items(failure.get("decision_details_required"), "decision details")), RECORD_DETAIL_REQUIREMENTS["decision"], "decision details")
    require(set(items(failure.get("prohibited_failure_behavior"), "prohibited failure behavior")), PROHIBITED_FAILURE_BEHAVIOR, "prohibited failure behavior")

    cleanup = obj(contract.get("cleanup_requirements"), "cleanup requirements")
    require(set(items(cleanup.get("commitment_details_required"), "commitment details")), RECORD_DETAIL_REQUIREMENTS["cleanup_commitment"], "commitment details")
    require(set(items(cleanup.get("verification_details_required"), "verification details")), RECORD_DETAIL_REQUIREMENTS["cleanup_verification"], "verification details")
    require(cleanup.get("maximum_retention_hours"), 24, "cleanup retention")
    require(cleanup.get("maximum_approved_cost_cad"), 10.0, "cleanup cost")

    supersession = obj(contract.get("supersession_requirements"), "supersession requirements")
    require(set(items(supersession.get("required_fields"), "supersession fields")), {"superseded_by_package_id", "reason", "evidence_sha256"}, "supersession fields")
    require(supersession.get("required_only_when_package_status_is_superseded"), True, "supersession status gate")
    require(supersession.get("verified_claims_allowed"), False, "supersession claim gate")

    return {
        "contract_valid": True,
        "state": "design_only",
        "active_workflow_present": False,
        "dispatch_authorized": False,
        "azure_authentication_authorized": False,
        "azure_mutations_authorized": False,
        "phase_count": len(PHASES),
        "claim_count": len(CLAIMS),
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
    subscriptions: set[str] = set()
    for field, expected_name in names.items():
        resource_id = text(target.get(field), f"target.{field}", 1024)
        match = AZURE_ID.fullmatch(resource_id)
        if match is None:
            raise EvidenceValidationError(f"target.{field} must be a complete Azure resource ID")
        if match.group("name") != expected_name:
            raise EvidenceValidationError(f"target.{field} does not identify {expected_name}")
        if match.group("resource_group") != contract_target["resource_group"]:
            raise EvidenceValidationError(f"target.{field} belongs to the wrong resource group")
        subscriptions.add(match.group("subscription").lower())
        result.add(resource_id)
    if len(result) != len(names):
        raise EvidenceValidationError("target resource IDs must be distinct")
    if len(subscriptions) != 1:
        raise EvidenceValidationError("target resource IDs cross subscription boundaries")
    return result


def _validate_record_details(
    record_type: str,
    details: dict[str, Any],
    *,
    prefix: str,
    contract: dict[str, Any],
    generated_at: datetime,
) -> None:
    required = set(contract["record_detail_requirements"][record_type])
    missing = required - set(details)
    if missing:
        raise EvidenceValidationError(f"{prefix}.details missing required evidence fields: {sorted(missing)}")

    if record_type == "guest_preflight":
        text(details["service_state"], f"{prefix}.details.service_state", 128)
        text(details["health_status"], f"{prefix}.details.health_status", 128)
        require(details["evidence_mount"], TARGET["evidence_mount"], f"{prefix}.details.evidence_mount")
        text(details["filesystem_uuid"], f"{prefix}.details.filesystem_uuid", 128)
        boolean(details["recent_evidence_readable"], f"{prefix}.details.recent_evidence_readable")
    elif record_type == "azure_control_plane_preflight":
        for field in ("vm_power_state", "nic_delete_option", "evidence_disk_delete_option", "os_disk_public_network_access"):
            text(details[field], f"{prefix}.details.{field}", 256)
        items(details["observed_role_assignments"], f"{prefix}.details.observed_role_assignments")
    elif record_type == "operation_attempt":
        for field in ("operation", "requested_by", "authorization_reference"):
            text(details[field], f"{prefix}.details.{field}", 512)
    elif record_type == "state_observation":
        if not isinstance(details["observed_state"], (dict, list, str, int, float, bool)) or details["observed_state"] is None:
            raise EvidenceValidationError(f"{prefix}.details.observed_state must contain an observation")
        text(details["source"], f"{prefix}.details.source", 512)
    elif record_type == "consistency_checkpoint":
        text(details["checkpoint_name"], f"{prefix}.details.checkpoint_name", 256)
        boolean(details["consistent"], f"{prefix}.details.consistent")
        items(details["evidence_references"], f"{prefix}.details.evidence_references")
    elif record_type == "integrity_verification":
        text(details["verification_name"], f"{prefix}.details.verification_name", 256)
        boolean(details["passed"], f"{prefix}.details.passed")
        items(details["checks"], f"{prefix}.details.checks")
    elif record_type == "cleanup_commitment":
        text(details["owner"], f"{prefix}.details.owner", 256)
        timestamp(details["deadline"], f"{prefix}.details.deadline")
        retention = integer(details["maximum_retention_hours"], f"{prefix}.details.maximum_retention_hours")
        if not 1 <= retention <= contract["cleanup_requirements"]["maximum_retention_hours"]:
            raise EvidenceValidationError(f"{prefix}.details.maximum_retention_hours exceeds contract")
        cost = number(details["approved_cost_ceiling_cad"], f"{prefix}.details.approved_cost_ceiling_cad")
        if not 0 <= cost <= contract["cleanup_requirements"]["maximum_approved_cost_cad"]:
            raise EvidenceValidationError(f"{prefix}.details.approved_cost_ceiling_cad exceeds contract")
    elif record_type == "cleanup_verification":
        removed = items(details["removed_resource_ids"], f"{prefix}.details.removed_resource_ids")
        retained = items(details["retained_resource_ids"], f"{prefix}.details.retained_resource_ids")
        for index, resource_id in enumerate(removed):
            text(resource_id, f"{prefix}.details.removed_resource_ids[{index}]", 1024)
        for index, resource_id in enumerate(retained):
            text(resource_id, f"{prefix}.details.retained_resource_ids[{index}]", 1024)
        if set(removed) & set(retained):
            raise EvidenceValidationError(f"{prefix}.details resource cannot be both removed and retained")
        if timestamp(details["verified_at"], f"{prefix}.details.verified_at") > generated_at:
            raise EvidenceValidationError(f"{prefix}.details.verified_at is after package generation")
        text(details["verifier_identity"], f"{prefix}.details.verifier_identity", 256)
        cost = number(details["actual_temporary_cost_cad"], f"{prefix}.details.actual_temporary_cost_cad")
        if not 0 <= cost <= contract["cleanup_requirements"]["maximum_approved_cost_cad"]:
            raise EvidenceValidationError(f"{prefix}.details.actual_temporary_cost_cad exceeds contract")
    elif record_type == "decision":
        for field in ("decision", "reason", "authority", "safe_next_step"):
            text(details[field], f"{prefix}.details.{field}", 1024)
        boolean(details["rollback_required"], f"{prefix}.details.rollback_required")


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
    if record_type not in RECORD_TYPES:
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
    if status not in RECORD_STATUSES:
        raise EvidenceValidationError(f"{prefix}.status is unsupported")
    if status == "passed" and exit_status != 0:
        raise EvidenceValidationError(f"{prefix} cannot pass with a non-zero exit status")

    target_id = text(record.get("target_resource_id"), f"{prefix}.target_resource_id", 1024)
    if target_id not in resource_ids:
        raise EvidenceValidationError(f"{prefix}.target_resource_id is outside the target boundary")
    for field in ("before_state", "after_state", "details"):
        value = obj(record.get(field), f"{prefix}.{field}")
        safe_json(value, field=f"{prefix}.{field}", policy=policy, limits=package)
    details = obj(record["details"], f"{prefix}.details")
    _validate_record_details(record_type, details, prefix=prefix, contract=contract, generated_at=generated_at)
    patterned(record.get("evidence_sha256"), f"{prefix}.evidence_sha256", package["sha256_pattern"])
    text(record.get("summary"), f"{prefix}.summary", 512)

    marker = policy["redaction_marker"]
    expected_paths: set[str] = set()
    for field in ("before_state", "after_state", "details"):
        expected_paths.update(marker_paths(record[field], marker, field=field))
    redactions = items(record.get("redactions"), f"{prefix}.redactions")
    actual_paths: list[str] = []
    for redaction_index, value in enumerate(redactions):
        redaction = obj(value, f"{prefix}.redactions[{redaction_index}]")
        exact_keys(redaction, {"field_path", "marker", "original_sha256"}, f"{prefix}.redactions[{redaction_index}]")
        actual_paths.append(text(redaction.get("field_path"), f"{prefix}.redactions[{redaction_index}].field_path", 512))
        require(redaction.get("marker"), marker, f"{prefix}.redactions[{redaction_index}].marker")
        patterned(redaction.get("original_sha256"), f"{prefix}.redactions[{redaction_index}].original_sha256", package["sha256_pattern"])
    if len(actual_paths) != len(set(actual_paths)):
        raise EvidenceValidationError(f"{prefix}.redactions contains duplicate field paths")
    if set(actual_paths) != expected_paths:
        raise EvidenceValidationError(
            f"{prefix}.redactions do not exactly match marker paths: "
            f"missing={sorted(expected_paths - set(actual_paths))}, extra={sorted(set(actual_paths) - expected_paths)}"
        )
    return record_id, record_type, status
