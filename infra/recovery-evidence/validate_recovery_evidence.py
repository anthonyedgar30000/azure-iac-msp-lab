from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

DESIGN_VERSION = "servicetracer.collector-recovery-evidence-design.v1"
BUNDLE_VERSION = "servicetracer.collector-recovery.evidence-bundle.v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_ID = re.compile(r"^ev-[a-z0-9][a-z0-9-]{7,95}$")
MAINTENANCE_ID = re.compile(r"^maint-[a-z0-9][a-z0-9-]{7,95}$")
OPERATION_ID = re.compile(r"^op-[a-z0-9][a-z0-9-]{7,95}$")
SCHEMAS = {
    "guest_preflight": (
        "https://schemas.servicetracer.local/collector-recovery/guest-preflight.v1.json",
        "infra/recovery-evidence/schemas/guest-preflight.schema.json",
        "servicetracer.collector-recovery.guest-preflight.v1",
    ),
    "azure_control_plane_preflight": (
        "https://schemas.servicetracer.local/collector-recovery/azure-control-plane-preflight.v1.json",
        "infra/recovery-evidence/schemas/azure-control-plane-preflight.schema.json",
        "servicetracer.collector-recovery.azure-control-plane-preflight.v1",
    ),
    "phase_failure": (
        "https://schemas.servicetracer.local/collector-recovery/phase-failure.v1.json",
        "infra/recovery-evidence/schemas/phase-failure.schema.json",
        "servicetracer.collector-recovery.phase-failure.v1",
    ),
    "rollback_outcome": (
        "https://schemas.servicetracer.local/collector-recovery/rollback-outcome.v1.json",
        "infra/recovery-evidence/schemas/rollback-outcome.schema.json",
        "servicetracer.collector-recovery.rollback-outcome.v1",
    ),
    "bundle": (
        "https://schemas.servicetracer.local/collector-recovery/evidence-bundle.v1.json",
        "infra/recovery-evidence/schemas/recovery-evidence-bundle.schema.json",
        BUNDLE_VERSION,
    ),
}
TARGET = {
    "resource_group": "rg-servicetracer-dev-westus2",
    "location": "westus2",
    "collector_vm": "vm-stcollector-mst-dev",
    "collector_nic": "nic-stcollector-mst-dev",
    "collector_evidence_disk": "disk-stcollector-evidence-mst-dev",
    "collector_os_disk": "disk-stcollector-os-mst-dev",
    "evidence_mount": "/var/lib/servicetracer",
}
REVIEWS = {"evidence-quality", "operations-and-recovery", "security-and-identity", "azure-cost"}
NEGATIVE_TESTS = {
    "missing required observation kind",
    "duplicate evidence identity",
    "correlation mismatch",
    "target mismatch",
    "stale evidence",
    "success with non-zero exit code",
    "preflight state mutation",
    "Azure mutation authorization enabled",
    "sanitized record missing resource digest",
    "unredacted secret marker",
    "failure without failure record",
    "rollback success claimed without authorized runtime evidence",
}


class RecoveryEvidenceValidationError(RuntimeError):
    pass


def obj(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RecoveryEvidenceValidationError(f"{field} must be an object")
    return value


def arr(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise RecoveryEvidenceValidationError(f"{field} must be a list")
    return value


def text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecoveryEvidenceValidationError(f"{field} must be non-empty text")
    return value.strip()


def require(value: Any, expected: Any, field: str) -> None:
    if value != expected:
        raise RecoveryEvidenceValidationError(f"{field} must equal {expected!r}")


def require_fields(value: dict[str, Any], fields: list[str], field: str) -> None:
    missing = [name for name in fields if name not in value]
    if missing:
        raise RecoveryEvidenceValidationError(f"{field} missing fields: {missing}")


def digest(value: Any, field: str) -> str:
    result = text(value, field)
    if not HEX64.fullmatch(result):
        raise RecoveryEvidenceValidationError(f"{field} must be a lowercase SHA-256 digest")
    return result


def timestamp(value: Any, field: str) -> datetime:
    result = text(value, field)
    if not result.endswith("Z"):
        raise RecoveryEvidenceValidationError(f"{field} must be RFC3339 UTC with Z")
    try:
        return datetime.fromisoformat(result[:-1] + "+00:00")
    except ValueError as exc:
        raise RecoveryEvidenceValidationError(f"{field} is invalid") from exc


def validate_contract(contract: dict[str, Any], schemas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    require(contract.get("schema_version"), DESIGN_VERSION, "schema_version")
    require(contract.get("state"), "design_only", "state")
    activation = obj(contract.get("activation"), "activation")
    require(activation.get("validator"), "infra/recovery-evidence/validate_recovery_evidence.py", "activation.validator")
    for field in ("active_workflow_present", "dispatch_authorized", "azure_authentication_authorized", "azure_mutations_authorized"):
        require(activation.get(field), False, f"activation.{field}")
    require(activation.get("promotion_requires_separate_pull_request"), True, "activation.promotion_requires_separate_pull_request")
    if set(arr(activation.get("promotion_requires_reviews"), "activation.promotion_requires_reviews")) != REVIEWS:
        raise RecoveryEvidenceValidationError("all four review lenses are required")
    require(contract.get("target"), TARGET, "target")

    declared = obj(contract.get("schemas"), "schemas")
    if set(declared) != set(SCHEMAS) or set(schemas) != set(SCHEMAS):
        raise RecoveryEvidenceValidationError("the five-schema set is required")
    for key, (schema_id, path, version) in SCHEMAS.items():
        item = obj(declared.get(key), f"schemas.{key}")
        require(item.get("schema_id"), schema_id, f"schemas.{key}.schema_id")
        require(item.get("path"), path, f"schemas.{key}.path")
        require(item.get("schema_version"), version, f"schemas.{key}.schema_version")
        schema = schemas[key]
        require(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema", f"{key}.$schema")
        require(schema.get("$id"), schema_id, f"{key}.$id")
        require(schema.get("type"), "object", f"{key}.type")
        require(schema.get("additionalProperties"), False, f"{key}.additionalProperties")
        version_schema = obj(obj(schema.get("properties"), f"{key}.properties").get("schema_version"), f"{key}.properties.schema_version")
        require(version_schema.get("const"), version, f"{key}.schema_version.const")

    guest_kinds = arr(declared["guest_preflight"].get("required_observation_kinds"), "guest kinds")
    azure_kinds = arr(declared["azure_control_plane_preflight"].get("required_observation_kinds"), "Azure kinds")
    if len(guest_kinds) != len(set(guest_kinds)) or len(azure_kinds) != len(set(azure_kinds)):
        raise RecoveryEvidenceValidationError("observation kinds must be unique")
    require(declared["guest_preflight"].get("maximum_age_seconds"), 900, "guest maximum age")
    require(declared["azure_control_plane_preflight"].get("maximum_age_seconds"), 900, "Azure maximum age")

    common = obj(contract.get("common_envelope"), "common_envelope")
    require(common.get("maximum_clock_skew_seconds"), 120, "maximum clock skew")
    require(common.get("preflight_state_changed_must_be_false"), True, "preflight state rule")
    correlation = obj(contract.get("correlation_contract"), "correlation_contract")
    require(correlation.get("all_preflight_records_share_maintenance_correlation_id"), True, "shared correlation")
    require(correlation.get("all_records_target_same_collector"), True, "shared target")
    require(correlation.get("duplicate_evidence_ids_allowed"), False, "duplicate evidence IDs")
    command = obj(contract.get("command_provenance"), "command_provenance")
    require(command.get("success_requires_exit_code_zero"), True, "success exit code")
    require(command.get("raw_stdout_or_stderr_embedded"), False, "raw output embedding")
    identity = obj(contract.get("target_identity"), "target_identity")
    for field in ("raw_private_requires_exact_resource_id", "sanitized_review_requires_resource_id_sha256", "sanitized_review_forbids_exact_subscription_id", "sanitized_review_forbids_exact_tenant_id"):
        require(identity.get(field), True, f"target_identity.{field}")
    redaction = obj(contract.get("redaction_contract"), "redaction_contract")
    require(redaction.get("raw_private_repository_promotion_allowed"), False, "raw private promotion")
    require(redaction.get("sanitized_examples_only_in_repository"), True, "sanitized examples")
    bundle = obj(contract.get("bundle_contract"), "bundle_contract")
    require(bundle.get("guest_records_required"), len(guest_kinds), "guest record count")
    require(bundle.get("azure_control_plane_records_required"), len(azure_kinds), "Azure record count")
    require(bundle.get("runtime_execution_authorized_by_bundle"), False, "bundle execution authority")
    require(obj(contract.get("failure_contract"), "failure_contract").get("required_when_any_record_fails"), True, "failure record rule")
    rollback = obj(contract.get("rollback_contract"), "rollback_contract")
    require(rollback.get("operationally_tested_default"), False, "rollback default")
    require(rollback.get("operational_success_requires_separate_authorized_runtime_evidence"), True, "rollback authority rule")
    cost = obj(contract.get("cost_and_retention"), "cost_and_retention")
    require(cost.get("schema_design_increment_cost_cad"), 0.0, "schema design cost")
    require(cost.get("runtime_raw_evidence_maximum_retention_hours"), 24, "raw evidence retention")
    validation = obj(contract.get("validation"), "validation")
    require(validation.get("fail_closed"), True, "validation.fail_closed")
    require(validation.get("external_python_dependencies_required"), False, "validation dependencies")
    if set(arr(validation.get("negative_tests_required"), "negative tests")) != NEGATIVE_TESTS:
        raise RecoveryEvidenceValidationError("negative-test contract changed")
    return {
        "design_valid": True,
        "design_state": "fail_closed_design_only",
        "schema_count": 5,
        "guest_required_kinds": guest_kinds,
        "azure_required_kinds": azure_kinds,
        "azure_authentication_authorized": False,
        "azure_mutations_authorized": False,
        "runtime_execution_authorized": False,
    }


def build_design_fixture(contract: dict[str, Any]) -> dict[str, Any]:
    guest_kinds = contract["schemas"]["guest_preflight"]["required_observation_kinds"]
    azure_kinds = contract["schemas"]["azure_control_plane_preflight"]["required_observation_kinds"]
    correlation = {"maintenance_correlation_id": "maint-recovery-design-fixture", "operation_id": "op-preflight-design-fixture", "phase_id": "guest_and_control_plane_preflight"}
    target = {"resource_group": TARGET["resource_group"], "vm_name": TARGET["collector_vm"], "resource_id_sha256": "b" * 64, "guest_hostname_hash": "a" * 64}
    common = {
        "visibility": "sanitized_review",
        "correlation": correlation,
        "timestamps": {"observed_at": "2026-07-22T17:45:00Z", "recorded_at": "2026-07-22T17:45:05Z"},
        "target": target,
        "result": {"status": "success", "exit_code": 0, "assertion": "generated design fixture", "error_code": None, "retryable": False},
        "state": {"before": {"observation": "unknown"}, "after": {"observation": "captured"}, "changed": False},
        "redaction": {"applied": True, "fields": ["subscription_id", "tenant_id", "principal_id", "resource_id"], "method": "placeholder-and-sha256-binding", "secrets_detected": False},
        "authority": {"read_only": True, "azure_authentication_authorized": False, "azure_mutations_authorized": False, "execution_authorization_reference": None},
        "provenance": {"repository_commit": "bb1351da492548242382a86db5293f44dabfb1f7", "collector_version": "generated-design-fixture-1", "artifact_sha256": "d" * 64, "workflow_run_id": None},
    }
    guest_records = []
    for index, kind in enumerate(guest_kinds, 1):
        record = json.loads(json.dumps(common))
        record.update({
            "schema_version": contract["schemas"]["guest_preflight"]["schema_version"],
            "evidence_id": f"ev-guest-{index:02d}-{kind.replace('_', '-')}",
            "evidence_class": "guest_preflight",
            "command": {"executable": "/usr/bin/read-only-probe", "arguments_redacted": ["--kind", kind, "--target", "<redacted>"], "command_sha256": "c" * 64, "run_as_identity": "servicetracer-preflight", "shell": "/bin/bash", "exit_code": 0, "duration_ms": index, "stdout_sha256": "a" * 64, "stderr_sha256": "e" * 64},
            "guest_observation": {"kind": kind, "value": {"design_fixture": True}, "freshness_seconds": 5},
        })
        guest_records.append(record)
    azure_records = []
    for index, kind in enumerate(azure_kinds, 1):
        record = json.loads(json.dumps(common))
        record.update({
            "schema_version": contract["schemas"]["azure_control_plane_preflight"]["schema_version"],
            "evidence_id": f"ev-azure-{index:02d}-{kind.replace('_', '-')}",
            "evidence_class": "azure_control_plane_preflight",
            "command": {"tool": "azure-cli", "command_group": "read-only-design-probe", "arguments_redacted": ["--kind", kind, "--subscription", "<redacted>", "--resource-id", "<redacted>"], "command_sha256": "c" * 64, "authenticated_principal_hash": "e" * 64, "exit_code": 0, "duration_ms": index, "stdout_sha256": "a" * 64, "stderr_sha256": "e" * 64},
            "azure_observation": {"kind": kind, "value": {"design_fixture": True}, "freshness_seconds": 5},
        })
        azure_records.append(record)
    return {
        "schema_version": BUNDLE_VERSION,
        "bundle_id": "bundle-recovery-design-fixture",
        "state": "design_fixture",
        "correlation": correlation,
        "target": target,
        "generated_at": "2026-07-22T17:45:10Z",
        "guest_preflight": guest_records,
        "azure_control_plane_preflight": azure_records,
        "failures": [],
        "rollbacks": [],
        "authority": common["authority"],
        "redaction_summary": {"sanitized": True, "raw_records_promoted": False, "secrets_detected": False},
    }


def validate_record(record: dict[str, Any], contract: dict[str, Any], evidence_class: str) -> tuple[str, str, str]:
    common_fields = arr(contract["common_envelope"]["required_fields"], "common fields")
    require_fields(record, common_fields + ["command"], "record")
    expected_version = contract["schemas"][evidence_class]["schema_version"]
    require(record.get("schema_version"), expected_version, "record.schema_version")
    require(record.get("evidence_class"), evidence_class, "record.evidence_class")
    evidence_id = text(record.get("evidence_id"), "record.evidence_id")
    if not EVIDENCE_ID.fullmatch(evidence_id):
        raise RecoveryEvidenceValidationError("evidence ID format is invalid")
    correlation = obj(record.get("correlation"), "record.correlation")
    maintenance_id = text(correlation.get("maintenance_correlation_id"), "maintenance correlation")
    operation_id = text(correlation.get("operation_id"), "operation ID")
    if not MAINTENANCE_ID.fullmatch(maintenance_id) or not OPERATION_ID.fullmatch(operation_id):
        raise RecoveryEvidenceValidationError("correlation format is invalid")
    times = obj(record.get("timestamps"), "record.timestamps")
    observed = timestamp(times.get("observed_at"), "observed_at")
    recorded = timestamp(times.get("recorded_at"), "recorded_at")
    if recorded < observed or (recorded - observed).total_seconds() > 120:
        raise RecoveryEvidenceValidationError("timestamp ordering or skew is invalid")
    target = obj(record.get("target"), "record.target")
    require(target.get("resource_group"), TARGET["resource_group"], "record.target.resource_group")
    require(target.get("vm_name"), TARGET["collector_vm"], "record.target.vm_name")
    if record.get("visibility") == "sanitized_review":
        digest(target.get("resource_id_sha256"), "record.target.resource_id_sha256")
        if "resource_id" in target:
            raise RecoveryEvidenceValidationError("sanitized evidence must not include exact resource ID")
    result = obj(record.get("result"), "record.result")
    command = obj(record.get("command"), "record.command")
    if result.get("status") == "success" and result.get("exit_code") != 0:
        raise RecoveryEvidenceValidationError("success requires exit code zero")
    if command.get("exit_code") != result.get("exit_code"):
        raise RecoveryEvidenceValidationError("command and result exit codes differ")
    for field in ("command_sha256", "stdout_sha256", "stderr_sha256"):
        digest(command.get(field), f"record.command.{field}")
    state = obj(record.get("state"), "record.state")
    require(state.get("changed"), False, "preflight state.changed")
    redaction = obj(record.get("redaction"), "record.redaction")
    require(redaction.get("secrets_detected"), False, "redaction.secrets_detected")
    if record.get("visibility") == "sanitized_review":
        require(redaction.get("applied"), True, "redaction.applied")
    authority = obj(record.get("authority"), "record.authority")
    require(authority.get("read_only"), True, "authority.read_only")
    require(authority.get("azure_mutations_authorized"), False, "authority.azure_mutations_authorized")
    provenance = obj(record.get("provenance"), "record.provenance")
    if not SHA40.fullmatch(text(provenance.get("repository_commit"), "repository commit")):
        raise RecoveryEvidenceValidationError("repository commit format is invalid")
    digest(provenance.get("artifact_sha256"), "artifact digest")
    serialized = json.dumps(record, sort_keys=True).lower()
    for marker in contract["redaction_contract"]["forbidden_content_markers_case_insensitive"]:
        if marker.lower() in serialized:
            raise RecoveryEvidenceValidationError(f"forbidden content marker: {marker}")
    observation_name = "guest_observation" if evidence_class == "guest_preflight" else "azure_observation"
    observation = obj(record.get(observation_name), observation_name)
    kind = text(observation.get("kind"), f"{observation_name}.kind")
    allowed = contract["schemas"][evidence_class]["required_observation_kinds"]
    if kind not in allowed:
        raise RecoveryEvidenceValidationError("unsupported observation kind")
    freshness = observation.get("freshness_seconds")
    if not isinstance(freshness, int) or isinstance(freshness, bool) or freshness < 0 or freshness > 900:
        raise RecoveryEvidenceValidationError("evidence is stale or freshness is invalid")
    return evidence_id, maintenance_id, kind


def validate_bundle(bundle: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    require(bundle.get("schema_version"), BUNDLE_VERSION, "bundle.schema_version")
    require(bundle.get("state"), "design_fixture", "bundle.state")
    timestamp(bundle.get("generated_at"), "bundle.generated_at")
    authority = obj(bundle.get("authority"), "bundle.authority")
    require(authority.get("read_only"), True, "bundle.authority.read_only")
    require(authority.get("azure_authentication_authorized"), False, "bundle Azure authentication")
    require(authority.get("azure_mutations_authorized"), False, "bundle Azure mutations")
    require(authority.get("execution_authorization_reference"), None, "bundle execution authority")
    redaction = obj(bundle.get("redaction_summary"), "bundle.redaction_summary")
    require(redaction.get("sanitized"), True, "bundle sanitized")
    require(redaction.get("raw_records_promoted"), False, "raw records promoted")
    require(redaction.get("secrets_detected"), False, "bundle secrets detected")
    correlation = obj(bundle.get("correlation"), "bundle.correlation")
    maintenance_id = text(correlation.get("maintenance_correlation_id"), "bundle maintenance correlation")
    target_digest = digest(obj(bundle.get("target"), "bundle.target").get("resource_id_sha256"), "bundle target digest")
    guest_records = arr(bundle.get("guest_preflight"), "guest records")
    azure_records = arr(bundle.get("azure_control_plane_preflight"), "Azure records")
    failures = arr(bundle.get("failures"), "failure records")
    rollbacks = arr(bundle.get("rollbacks"), "rollback records")
    seen: set[str] = set()
    guest_kinds: list[str] = []
    azure_kinds: list[str] = []
    failed = 0
    for record in guest_records:
        evidence_id, record_correlation, kind = validate_record(obj(record, "guest record"), contract, "guest_preflight")
        if record_correlation != maintenance_id or record["target"]["resource_id_sha256"] != target_digest:
            raise RecoveryEvidenceValidationError("guest correlation or target mismatch")
        if evidence_id in seen:
            raise RecoveryEvidenceValidationError("duplicate evidence identity")
        seen.add(evidence_id)
        guest_kinds.append(kind)
        failed += int(record["result"]["status"] == "failure")
    for record in azure_records:
        evidence_id, record_correlation, kind = validate_record(obj(record, "Azure record"), contract, "azure_control_plane_preflight")
        if record_correlation != maintenance_id or record["target"]["resource_id_sha256"] != target_digest:
            raise RecoveryEvidenceValidationError("Azure correlation or target mismatch")
        if evidence_id in seen:
            raise RecoveryEvidenceValidationError("duplicate evidence identity")
        seen.add(evidence_id)
        azure_kinds.append(kind)
        failed += int(record["result"]["status"] == "failure")
    required_guest = contract["schemas"]["guest_preflight"]["required_observation_kinds"]
    required_azure = contract["schemas"]["azure_control_plane_preflight"]["required_observation_kinds"]
    if sorted(guest_kinds) != sorted(required_guest) or len(guest_kinds) != len(required_guest):
        raise RecoveryEvidenceValidationError("guest observation coverage is incomplete or duplicated")
    if sorted(azure_kinds) != sorted(required_azure) or len(azure_kinds) != len(required_azure):
        raise RecoveryEvidenceValidationError("Azure observation coverage is incomplete or duplicated")
    if failed and not failures:
        raise RecoveryEvidenceValidationError("failure record required")
    if not failed and failures:
        raise RecoveryEvidenceValidationError("fixture must not invent failure records")
    for record in rollbacks:
        record = obj(record, "rollback record")
        body = obj(record.get("rollback"), "rollback body")
        if body.get("outcome") == "succeeded" or body.get("operationally_tested") is True:
            rollback_authority = obj(record.get("authority"), "rollback authority")
            require(rollback_authority.get("azure_authentication_authorized"), True, "rollback Azure authentication")
            require(rollback_authority.get("azure_mutations_authorized"), True, "rollback Azure mutations")
            text(rollback_authority.get("execution_authorization_reference"), "rollback authorization reference")
    return {
        "bundle_valid": True,
        "bundle_state": contract["bundle_contract"]["bundle_status_when_complete"],
        "guest_record_count": len(guest_records),
        "azure_record_count": len(azure_records),
        "evidence_identity_count": len(seen),
        "failure_record_count": len(failures),
        "rollback_record_count": len(rollbacks),
        "runtime_execution_authorized": False,
        "azure_mutations_authorized": False,
    }


def load_design(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    contract = json.loads((root / "infra/recovery-evidence/collector-recovery-evidence-contract.json").read_text(encoding="utf-8"))
    schemas = {key: json.loads((root / value["path"]).read_text(encoding="utf-8")) for key, value in contract["schemas"].items()}
    return contract, schemas, build_design_fixture(contract)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the design-only collector recovery evidence contract")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        contract, schemas, fixture = load_design(args.root)
        result = {"design": validate_contract(contract, schemas), "bundle": validate_bundle(fixture, contract)}
    except (OSError, json.JSONDecodeError, RecoveryEvidenceValidationError) as exc:
        print(f"collector recovery evidence validation failed: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
