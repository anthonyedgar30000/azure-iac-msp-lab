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
    "rollback_recovery": {"operation_attempt", "state_observation", "guest_preflight", "azure_control_plane_preflight", "integrity_verification", "decision"},
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
        "required_record_types": {"operation_attempt", "state_observation", "guest_preflight", "azure_control_plane_preflight", "integrity_verification", "decision"},
    },
    "recovery": {
        "required_phases": {"guest_and_control_plane_preflight", "verify_recovery_points", "isolated_snapshot_boot_rehearsal", "teardown_isolated_rehearsal", "post_change_verification", "human_recovery_acceptance", "cleanup_temporary_recovery_resources"},
        "required_record_types": {"guest_preflight", "azure_control_plane_preflight", "integrity_verification", "cleanup_verification", "decision"},
    },
}
CLAIMS = set(CLAIM_REQUIREMENTS)
PACKAGE_LIMITS = {
    "maximum_package_bytes": 524288,
    "maximum_records": 256,
    "maximum_nested_depth": 6,
    "maximum_nested_items": 128,
    "maximum_text_length": 4096,
}
PACKAGE_STATUSES = {"complete", "incomplete", "failed", "aborted", "superseded"}
RECORD_STATUSES = {"passed", "failed", "aborted", "observed", "not_applicable"}
CLAIM_STATUSES = {"not_claimed", "unverified", "failed", "verified"}
RECORD_TYPES = {"guest_preflight", "azure_control_plane_preflight", "operation_attempt", "state_observation", "consistency_checkpoint", "integrity_verification", "cleanup_commitment", "cleanup_verification", "decision"}
TOP_LEVEL_FIELDS = {"schema_version", "package_id", "generated_at", "maintenance_correlation_id", "producer", "target", "declared_phase_ids", "package_status", "supersedes_package_ids", "records", "claims", "claim_boundary"}
PRODUCER_FIELDS = {"tool", "version", "identity", "source_commit"}
RECORD_FIELDS = {"record_id", "record_type", "phase_id", "observed_at", "command_identity", "exit_status", "status", "target_resource_id", "before_state", "after_state", "evidence_sha256", "summary", "details", "redactions"}
DETAIL_REQUIREMENTS = {
    "guest_preflight": {"service_state", "health_status", "evidence_mount", "filesystem_uuid", "recent_evidence_readable"},
    "azure_control_plane_preflight": {"vm_power_state", "nic_delete_option", "evidence_disk_delete_option", "os_disk_public_network_access", "observed_role_assignment_ids"},
    "operation_attempt": {"operation", "authority_reference", "started_at", "finished_at"},
    "state_observation": {"property", "observed_value", "observation_source"},
    "consistency_checkpoint": {"checkpoint_id", "checkpoint_sha256", "maintenance_correlation_id"},
    "integrity_verification": {"verification", "expected", "observed"},
    "cleanup_commitment": {"owner", "deadline", "maximum_retention_hours", "approved_cost_ceiling_cad"},
    "cleanup_verification": {"removed_resource_ids", "retained_resource_ids", "verified_at", "verifier_identity", "actual_temporary_cost_cad"},
    "decision": {"decision", "reason", "authority", "safe_next_step", "rollback_required"},
}
FORBIDDEN_FIELD_FRAGMENTS = {"password", "passwd", "secret", "token", "credential", "private_key", "client_secret", "connection_string", "sas_key", "access_key"}
FORBIDDEN_VALUE_PREFIXES = {"Bearer ", "SharedAccessSignature ", "AccountKey=", "-----BEGIN PRIVATE KEY-----", "-----BEGIN RSA PRIVATE KEY-----", "-----BEGIN OPENSSH PRIVATE KEY-----"}
FAILURE_RECORD_TYPES = {"operation_attempt", "decision"}
DECISION_DETAILS = {"decision", "reason", "authority", "safe_next_step", "rollback_required"}
PROHIBITED_FAILURE_BEHAVIOUR = {"silent retry", "unbounded retry", "automatic authority escalation", "claiming recovery without post-change verification", "deleting recovery artifacts before an accepted terminal decision"}
CLEANUP_COMMITMENT_DETAILS = {"owner", "deadline", "maximum_retention_hours", "approved_cost_ceiling_cad"}
CLEANUP_VERIFICATION_DETAILS = {"removed_resource_ids", "retained_resource_ids", "verified_at", "verifier_identity", "actual_temporary_cost_cad"}
PATTERNS = {
    "maintenance_correlation_id_pattern": r"^[A-Z0-9][A-Z0-9._:-]{7,127}$",
    "record_id_pattern": r"^[a-z0-9][a-z0-9._:-]{7,127}$",
    "command_identity_pattern": r"^[a-z0-9][a-z0-9._:-]{2,127}$",
    "sha256_pattern": r"^[0-9a-f]{64}$",
}
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
AZURE_ID = re.compile(r"^/subscriptions/(?P<subscription>[0-9a-fA-F-]{36})/resourceGroups/(?P<resource_group>[^/]+)/providers/Microsoft\.[A-Za-z]+/[A-Za-z]+/(?P<name>[^/]+)$")
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


def raw_text(value: Any, field: str, maximum: int | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceValidationError(f"{field} must be a non-empty string")
    if maximum is not None and len(value) > maximum:
        raise EvidenceValidationError(f"{field} exceeds maximum length {maximum}")
    return value


def integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise EvidenceValidationError(f"{field} must be an integer")
    return value


def number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EvidenceValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise EvidenceValidationError(f"{field} must be finite")
    return result


def boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceValidationError(f"{field} must be boolean")
    return value


def exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise EvidenceValidationError(f"{field} fields mismatch: missing={sorted(expected - set(value))}, unexpected={sorted(set(value) - expected)}")


def exact_text_set(value: Any, expected: set[str], field: str) -> None:
    observed_list = [text(item, f"{field}[]") for item in items(value, field)]
    observed = set(observed_list)
    if observed != expected or len(observed_list) != len(observed):
        raise EvidenceValidationError(f"{field} changed or contains duplicates")


def exact_raw_string_set(value: Any, expected: set[str], field: str) -> None:
    observed_list = [raw_text(item, f"{field}[]") for item in items(value, field)]
    observed = set(observed_list)
    if observed != expected or len(observed_list) != len(observed):
        raise EvidenceValidationError(f"{field} changed or contains duplicates")


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
    return len(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def marker_paths(value: Any, *, prefix: str, marker: str) -> set[str]:
    if isinstance(value, dict):
        result: set[str] = set()
        for key, child in value.items():
            result.update(marker_paths(child, prefix=f"{prefix}.{key}", marker=marker))
        return result
    if isinstance(value, list):
        result = set()
        for index, child in enumerate(value):
            result.update(marker_paths(child, prefix=f"{prefix}[{index}]", marker=marker))
        return result
    return {prefix} if value == marker else set()


def safe_json(value: Any, *, field: str, policy: dict[str, Any], limits: dict[str, Any], depth: int = 0) -> None:
    if depth > integer(limits["maximum_nested_depth"], "maximum_nested_depth"):
        raise EvidenceValidationError(f"{field} exceeds maximum nested depth")
    max_items = integer(limits["maximum_nested_items"], "maximum_nested_items")
    max_text = integer(limits["maximum_text_length"], "maximum_text_length")
    forbidden_keys = [text(item, "forbidden key").lower() for item in items(policy["forbidden_field_name_fragments"], "forbidden keys")]
    forbidden_prefixes = [raw_text(item, "forbidden prefix") for item in items(policy["forbidden_value_prefixes"], "forbidden prefixes")]
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


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    require(contract.get("schema_version"), CONTRACT_SCHEMA, "schema_version")
    require(contract.get("state"), "design_only", "state")
    authority = obj(contract.get("authority"), "authority")
    for field in ("active_workflow_present", "dispatch_authorized", "azure_authentication_authorized", "azure_mutations_authorized", "evidence_collection_commands_implemented"):
        require(authority.get(field), False, f"authority.{field}")
    require(authority.get("promotion_requires_separate_pull_request"), True, "promotion gate")
    text(authority.get("claim_boundary"), "authority.claim_boundary")
    target = obj(contract.get("target"), "target")
    for field, expected in TARGET.items():
        require(target.get(field), expected, f"target.{field}")
    require(target.get("exact_resource_ids_required_at_collection_time"), True, "target exact IDs")
    package = obj(contract.get("package"), "package")
    require(package.get("schema_version"), PACKAGE_SCHEMA, "package.schema_version")
    for field, expected in PACKAGE_LIMITS.items():
        require(package.get(field), expected, f"package.{field}")
    require(package.get("timestamp_format"), "RFC3339_UTC_Z", "timestamp_format")
    for field, expected in PATTERNS.items():
        require(package.get(field), expected, f"package.{field}")
        re.compile(expected)
    exact_text_set(package.get("package_statuses"), PACKAGE_STATUSES, "package.package_statuses")
    exact_text_set(package.get("record_statuses"), RECORD_STATUSES, "package.record_statuses")
    exact_text_set(package.get("claim_statuses"), CLAIM_STATUSES, "package.claim_statuses")
    exact_text_set(package.get("record_types"), RECORD_TYPES, "package.record_types")
    exact_text_set(package.get("required_top_level_fields"), TOP_LEVEL_FIELDS, "package.required_top_level_fields")
    exact_text_set(package.get("producer_required_fields"), PRODUCER_FIELDS, "package.producer_required_fields")
    exact_text_set(package.get("required_record_fields"), RECORD_FIELDS, "package.required_record_fields")
    exact_text_set(package.get("allowed_record_fields"), RECORD_FIELDS, "package.allowed_record_fields")
    for field in ("complete_requires_all_declared_phase_evidence", "failed_or_aborted_requires_terminal_decision", "operational_claim_requires_complete_package"):
        require(package.get(field), True, f"package.{field}")
    observed_phases = {phase: set(items(required, f"phase_requirements.{phase}")) for phase, required in obj(contract.get("phase_requirements"), "phase_requirements").items()}
    require(observed_phases, PHASES, "phase requirements")
    observed_claims = {claim: {"required_phases": set(items(value.get("required_phases"), f"claim_requirements.{claim}.required_phases")), "required_record_types": set(items(value.get("required_record_types"), f"claim_requirements.{claim}.required_record_types"))} for claim, value in obj(contract.get("claim_requirements"), "claim_requirements").items() if isinstance(value, dict)}
    require(observed_claims, CLAIM_REQUIREMENTS, "claim requirements")
    observed_details = {record_type: set(items(required, f"record_detail_requirements.{record_type}")) for record_type, required in obj(contract.get("record_detail_requirements"), "record_detail_requirements").items()}
    require(observed_details, DETAIL_REQUIREMENTS, "record detail requirements")
    redaction = obj(contract.get("redaction_policy"), "redaction_policy")
    exact_text_set(redaction.get("forbidden_field_name_fragments"), FORBIDDEN_FIELD_FRAGMENTS, "redaction_policy.forbidden_field_name_fragments")
    exact_raw_string_set(redaction.get("forbidden_value_prefixes"), FORBIDDEN_VALUE_PREFIXES, "redaction_policy.forbidden_value_prefixes")
    require(redaction.get("redaction_marker"), "[REDACTED]", "redaction marker")
    require(redaction.get("redacted_value_requires_sha256"), True, "redaction digest")
    require(redaction.get("raw_stdout_stderr_allowed"), False, "raw output boundary")
    require(redaction.get("command_identity_must_be_logical_name_not_raw_command_line"), True, "command identity boundary")
    require(redaction.get("resource_ids_must_be_preserved"), True, "resource ID boundary")
    failure = obj(contract.get("failure_and_abort_requirements"), "failure requirements")
    exact_text_set(failure.get("required_failed_or_aborted_record_types"), FAILURE_RECORD_TYPES, "failure record types")
    exact_text_set(failure.get("decision_details_required"), DECISION_DETAILS, "decision details")
    exact_text_set(failure.get("prohibited_failure_behavior"), PROHIBITED_FAILURE_BEHAVIOUR, "prohibited failure behaviour")
    cleanup = obj(contract.get("cleanup_requirements"), "cleanup requirements")
    exact_text_set(cleanup.get("commitment_details_required"), CLEANUP_COMMITMENT_DETAILS, "cleanup commitment details")
    exact_text_set(cleanup.get("verification_details_required"), CLEANUP_VERIFICATION_DETAILS, "cleanup verification details")
    require(cleanup.get("maximum_retention_hours"), 24, "cleanup retention")
    require(cleanup.get("maximum_approved_cost_cad"), 10.0, "cleanup cost")
    return {"contract_valid": True, "state": "design_only", "active_workflow_present": False, "dispatch_authorized": False, "azure_authentication_authorized": False, "azure_mutations_authorized": False, "phase_count": len(PHASES), "claim_count": len(CLAIMS), "record_type_count": len(RECORD_TYPES)}


def validate_target(target: dict[str, Any], contract_target: dict[str, Any]) -> set[str]:
    exact_keys(target, {"subscription_id", "resource_group", "collector_vm", "collector_vm_resource_id", "collector_nic_resource_id", "collector_evidence_disk_resource_id", "collector_os_disk_resource_id", "evidence_mount"}, "target")
    subscription_id = text(target.get("subscription_id"), "target.subscription_id")
    if UUID.fullmatch(subscription_id) is None:
        raise EvidenceValidationError("target.subscription_id must be a UUID")
    for field in ("resource_group", "collector_vm", "evidence_mount"):
        require(target.get(field), contract_target.get(field), f"target.{field}")
    names = {"collector_vm_resource_id": contract_target["collector_vm"], "collector_nic_resource_id": contract_target["collector_nic"], "collector_evidence_disk_resource_id": contract_target["collector_evidence_disk"], "collector_os_disk_resource_id": contract_target["collector_os_disk"]}
    result: set[str] = set()
    observed_subscriptions: set[str] = set()
    for field, expected_name in names.items():
        resource_id = text(target.get(field), f"target.{field}", 1024)
        match = AZURE_ID.fullmatch(resource_id)
        if match is None or UUID.fullmatch(match.group("subscription")) is None:
            raise EvidenceValidationError(f"target.{field} must be a complete Azure resource ID")
        if match.group("name") != expected_name:
            raise EvidenceValidationError(f"target.{field} does not identify {expected_name}")
        if match.group("resource_group") != contract_target["resource_group"]:
            raise EvidenceValidationError(f"target.{field} belongs to the wrong resource group")
        observed_subscriptions.add(match.group("subscription").lower())
        result.add(resource_id)
    if observed_subscriptions != {subscription_id.lower()}:
        raise EvidenceValidationError("all target resource IDs must share target.subscription_id")
    return result


def _required_details(details: dict[str, Any], *, record_type: str, prefix: str, contract: dict[str, Any], observed_at: datetime, generated_at: datetime, correlation_id: str) -> None:
    required = set(contract["record_detail_requirements"][record_type])
    missing = required - set(details)
    if missing:
        raise EvidenceValidationError(f"{prefix}.details missing required fields: {sorted(missing)}")
    if record_type == "guest_preflight":
        text(details.get("service_state"), f"{prefix}.details.service_state", 128)
        text(details.get("health_status"), f"{prefix}.details.health_status", 128)
        require(details.get("evidence_mount"), TARGET["evidence_mount"], f"{prefix}.details.evidence_mount")
        text(details.get("filesystem_uuid"), f"{prefix}.details.filesystem_uuid", 128)
        boolean(details.get("recent_evidence_readable"), f"{prefix}.details.recent_evidence_readable")
    elif record_type == "azure_control_plane_preflight":
        for field in ("vm_power_state", "nic_delete_option", "evidence_disk_delete_option", "os_disk_public_network_access"):
            text(details.get(field), f"{prefix}.details.{field}", 256)
        assignments = [text(item, f"{prefix}.details.observed_role_assignment_ids[]", 1024) for item in items(details.get("observed_role_assignment_ids"), f"{prefix}.details.observed_role_assignment_ids")]
        if len(assignments) != len(set(assignments)):
            raise EvidenceValidationError(f"{prefix}.details.observed_role_assignment_ids contains duplicates")
    elif record_type == "operation_attempt":
        text(details.get("operation"), f"{prefix}.details.operation", 256)
        text(details.get("authority_reference"), f"{prefix}.details.authority_reference", 512)
        started = timestamp(details.get("started_at"), f"{prefix}.details.started_at")
        finished = timestamp(details.get("finished_at"), f"{prefix}.details.finished_at")
        if not observed_at <= started <= finished <= generated_at:
            raise EvidenceValidationError(f"{prefix}.details operation timestamps are out of order")
    elif record_type == "state_observation":
        text(details.get("property"), f"{prefix}.details.property", 256)
        text(details.get("observation_source"), f"{prefix}.details.observation_source", 256)
    elif record_type == "consistency_checkpoint":
        text(details.get("checkpoint_id"), f"{prefix}.details.checkpoint_id", 256)
        patterned(details.get("checkpoint_sha256"), f"{prefix}.details.checkpoint_sha256", PATTERNS["sha256_pattern"])
        require(details.get("maintenance_correlation_id"), correlation_id, f"{prefix}.details.maintenance_correlation_id")
    elif record_type == "integrity_verification":
        text(details.get("verification"), f"{prefix}.details.verification", 256)
    elif record_type == "cleanup_commitment":
        text(details.get("owner"), f"{prefix}.details.owner", 256)
        deadline = timestamp(details.get("deadline"), f"{prefix}.details.deadline")
        if deadline <= observed_at:
            raise EvidenceValidationError(f"{prefix}.details.deadline must follow the observation")
        retention = integer(details.get("maximum_retention_hours"), f"{prefix}.details.maximum_retention_hours")
        if not 1 <= retention <= 24:
            raise EvidenceValidationError(f"{prefix}.details.maximum_retention_hours exceeds the contract")
        cost = number(details.get("approved_cost_ceiling_cad"), f"{prefix}.details.approved_cost_ceiling_cad")
        if not 0 <= cost <= 10.0:
            raise EvidenceValidationError(f"{prefix}.details.approved_cost_ceiling_cad exceeds the contract")
    elif record_type == "cleanup_verification":
        for field in ("removed_resource_ids", "retained_resource_ids"):
            values = [text(item, f"{prefix}.details.{field}[]", 1024) for item in items(details.get(field), f"{prefix}.details.{field}")]
            if len(values) != len(set(values)):
                raise EvidenceValidationError(f"{prefix}.details.{field} contains duplicates")
        verified_at = timestamp(details.get("verified_at"), f"{prefix}.details.verified_at")
        if not observed_at <= verified_at <= generated_at:
            raise EvidenceValidationError(f"{prefix}.details.verified_at is outside the package window")
        text(details.get("verifier_identity"), f"{prefix}.details.verifier_identity", 256)
        cost = number(details.get("actual_temporary_cost_cad"), f"{prefix}.details.actual_temporary_cost_cad")
        if not 0 <= cost <= 10.0:
            raise EvidenceValidationError(f"{prefix}.details.actual_temporary_cost_cad exceeds the contract")
    elif record_type == "decision":
        for field in ("decision", "reason", "authority", "safe_next_step"):
            text(details.get(field), f"{prefix}.details.{field}", 1024)
        boolean(details.get("rollback_required"), f"{prefix}.details.rollback_required")


def validate_record(record: dict[str, Any], *, index: int, contract: dict[str, Any], declared_phases: set[str], generated_at: datetime, resource_ids: set[str], correlation_id: str) -> tuple[str, str, str]:
    package = obj(contract["package"], "package")
    policy = obj(contract["redaction_policy"], "redaction_policy")
    prefix = f"records[{index}]"
    exact_keys(record, RECORD_FIELDS, prefix)
    record_id = patterned(record.get("record_id"), f"{prefix}.record_id", PATTERNS["record_id_pattern"])
    record_type = text(record.get("record_type"), f"{prefix}.record_type")
    if record_type not in RECORD_TYPES:
        raise EvidenceValidationError(f"{prefix}.record_type is unsupported")
    phase_id = text(record.get("phase_id"), f"{prefix}.phase_id")
    if phase_id not in declared_phases:
        raise EvidenceValidationError(f"{prefix}.phase_id was not declared")
    observed_at = timestamp(record.get("observed_at"), f"{prefix}.observed_at")
    if observed_at > generated_at:
        raise EvidenceValidationError(f"{prefix}.observed_at is after package generation")
    command = patterned(record.get("command_identity"), f"{prefix}.command_identity", PATTERNS["command_identity_pattern"])
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
    details = obj(record.get("details"), f"{prefix}.details")
    _required_details(details, record_type=record_type, prefix=prefix, contract=contract, observed_at=observed_at, generated_at=generated_at, correlation_id=correlation_id)
    patterned(record.get("evidence_sha256"), f"{prefix}.evidence_sha256", PATTERNS["sha256_pattern"])
    text(record.get("summary"), f"{prefix}.summary", 512)
    expected_paths = set()
    for field in ("before_state", "after_state", "details"):
        expected_paths.update(marker_paths(record[field], prefix=field, marker="[REDACTED]"))
    redactions = items(record.get("redactions"), f"{prefix}.redactions")
    observed_paths: set[str] = set()
    for redaction_index, value in enumerate(redactions):
        redaction = obj(value, f"{prefix}.redactions[{redaction_index}]")
        exact_keys(redaction, {"field_path", "marker", "original_sha256"}, f"{prefix}.redactions[{redaction_index}]")
        field_path = text(redaction.get("field_path"), "redaction.field_path", 512)
        if field_path in observed_paths:
            raise EvidenceValidationError(f"{prefix}.redactions contains duplicate field_path {field_path}")
        observed_paths.add(field_path)
        require(redaction.get("marker"), "[REDACTED]", "redaction.marker")
        patterned(redaction.get("original_sha256"), "redaction.original_sha256", PATTERNS["sha256_pattern"])
    if observed_paths != expected_paths:
        raise EvidenceValidationError(f"{prefix}.redactions do not exactly match redacted value paths: expected={sorted(expected_paths)}, observed={sorted(observed_paths)}")
    return record_id, record_type, status
