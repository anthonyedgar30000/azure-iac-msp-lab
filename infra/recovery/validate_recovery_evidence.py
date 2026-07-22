from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from recovery_evidence_core import (
    CLAIMS,
    PACKAGE_SCHEMA,
    PHASES,
    EvidenceValidationError,
    canonical_size,
    exact_keys,
    items,
    obj,
    patterned,
    text,
    timestamp,
    validate_contract,
    validate_record,
    validate_target,
)


def _validate_supersession(
    package_value: dict[str, Any],
    *,
    package_status: str,
    package_id: str,
    package_contract: dict[str, Any],
) -> dict[str, str] | None:
    value = package_value.get("supersession")
    if package_status != "superseded":
        if value is not None:
            raise EvidenceValidationError("package.supersession must be null unless package_status is superseded")
        return None
    supersession = obj(value, "package.supersession")
    exact_keys(
        supersession,
        {"superseded_by_package_id", "reason", "evidence_sha256"},
        "package.supersession",
    )
    superseded_by = patterned(
        supersession.get("superseded_by_package_id"),
        "package.supersession.superseded_by_package_id",
        package_contract["record_id_pattern"],
    )
    if superseded_by == package_id:
        raise EvidenceValidationError("package cannot be superseded by itself")
    reason = text(supersession.get("reason"), "package.supersession.reason", 1024)
    digest = patterned(
        supersession.get("evidence_sha256"),
        "package.supersession.evidence_sha256",
        package_contract["sha256_pattern"],
    )
    return {
        "superseded_by_package_id": superseded_by,
        "reason": reason,
        "evidence_sha256": digest,
    }


def validate_evidence_package(package_value: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    validate_contract(contract)
    package_contract = obj(contract["package"], "package")
    if canonical_size(package_value) > package_contract["maximum_package_bytes"]:
        raise EvidenceValidationError("evidence package exceeds maximum_package_bytes")
    exact_keys(package_value, set(package_contract["required_top_level_fields"]), "package")
    if package_value.get("schema_version") != PACKAGE_SCHEMA:
        raise EvidenceValidationError("package.schema_version changed")

    package_id = patterned(package_value.get("package_id"), "package.package_id", package_contract["record_id_pattern"])
    generated_at = timestamp(package_value.get("generated_at"), "package.generated_at")
    correlation_id = patterned(
        package_value.get("maintenance_correlation_id"),
        "package.maintenance_correlation_id",
        package_contract["maintenance_correlation_id_pattern"],
    )
    resource_ids = validate_target(obj(package_value.get("target"), "package.target"), obj(contract["target"], "target"))

    declared_list = items(package_value.get("declared_phase_ids"), "package.declared_phase_ids")
    declared = {text(value, "package.declared_phase_ids[]") for value in declared_list}
    if len(declared) != len(declared_list):
        raise EvidenceValidationError("declared_phase_ids contains duplicates")
    unknown = declared - set(PHASES)
    if not declared or unknown:
        raise EvidenceValidationError(f"unknown or empty declared phase IDs: {sorted(unknown)}")

    package_status = text(package_value.get("package_status"), "package.package_status")
    if package_status not in set(package_contract["package_statuses"]):
        raise EvidenceValidationError("unsupported package_status")
    supersession = _validate_supersession(
        package_value,
        package_status=package_status,
        package_id=package_id,
        package_contract=package_contract,
    )

    records = items(package_value.get("records"), "package.records")
    if not records or len(records) > package_contract["maximum_records"]:
        raise EvidenceValidationError("record count is outside the bounded range")

    record_ids: set[str] = set()
    by_phase = {phase: set() for phase in declared}
    record_types: set[str] = set()
    statuses: list[str] = []
    for index, value in enumerate(records):
        record = obj(value, f"records[{index}]")
        record_id, record_type, status = validate_record(
            record,
            index=index,
            contract=contract,
            declared_phases=declared,
            generated_at=generated_at,
            resource_ids=resource_ids,
        )
        if record_id in record_ids:
            raise EvidenceValidationError(f"duplicate record_id: {record_id}")
        record_ids.add(record_id)
        by_phase[record["phase_id"]].add(record_type)
        record_types.add(record_type)
        statuses.append(status)

    missing = {
        phase: sorted(PHASES[phase] - by_phase[phase])
        for phase in sorted(declared)
        if PHASES[phase] - by_phase[phase]
    }
    complete = not missing
    if package_status == "complete" and not complete:
        raise EvidenceValidationError(f"complete package is missing declared phase evidence: {missing}")
    if package_status == "complete" and any(value in {"failed", "aborted"} for value in statuses):
        raise EvidenceValidationError("complete package contains failed or aborted evidence")

    if package_status in {"failed", "aborted"}:
        required_types = set(contract["failure_and_abort_requirements"]["required_failed_or_aborted_record_types"])
        if not required_types.issubset(record_types):
            raise EvidenceValidationError("failed or aborted package lacks operation_attempt and decision evidence")
        terminal = [
            record for record in records
            if record["record_type"] == "decision" and record["status"] in {"failed", "aborted"}
        ]
        if not terminal:
            raise EvidenceValidationError("failed or aborted package lacks a terminal decision")

    claims = obj(package_value.get("claims"), "package.claims")
    exact_keys(claims, CLAIMS, "package.claims")
    verified: list[str] = []
    for claim, status_value in claims.items():
        claim_status = text(status_value, f"package.claims.{claim}")
        if claim_status not in set(package_contract["claim_statuses"]):
            raise EvidenceValidationError(f"unsupported claim status for {claim}")
        if package_status == "superseded" and claim_status == "verified":
            raise EvidenceValidationError("superseded packages cannot retain verified claims")
        if claim_status != "verified":
            continue
        if package_status != "complete":
            raise EvidenceValidationError(f"verified {claim} claim requires a complete package")
        requirements = obj(contract["claim_requirements"][claim], f"claim_requirements.{claim}")
        required_phases = set(requirements["required_phases"])
        required_types = set(requirements["required_record_types"])
        if not required_phases.issubset(declared):
            raise EvidenceValidationError(f"verified {claim} claim lacks required phases")
        passing_types = {
            record["record_type"] for record in records
            if record["phase_id"] in required_phases and record["status"] == "passed"
        }
        if not required_types.issubset(passing_types):
            raise EvidenceValidationError(f"verified {claim} claim lacks passing record types")
        accepted = any(
            record["record_type"] == "decision"
            and record["phase_id"] == "human_recovery_acceptance"
            and record["status"] == "passed"
            and record["details"].get("decision") == "accepted"
            for record in records
        )
        if not accepted:
            raise EvidenceValidationError(f"verified {claim} claim lacks accepted human recovery decision")
        verified.append(claim)

    text(package_value.get("claim_boundary"), "package.claim_boundary", 1024)
    return {
        "package_valid": True,
        "package_id": package_id,
        "maintenance_correlation_id": correlation_id,
        "package_status": package_status,
        "superseded_by_package_id": supersession["superseded_by_package_id"] if supersession else None,
        "complete_for_declared_scope": complete,
        "missing_evidence_by_phase": missing,
        "record_count": len(records),
        "verified_claims": sorted(verified),
        "authority_granted": False,
        "azure_mutations_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the collector recovery evidence contract and package.")
    parser.add_argument("--contract", type=Path, default=Path(__file__).with_name("collector-recovery-evidence-contract.json"))
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = validate_contract(contract)
    if args.package:
        result = validate_evidence_package(json.loads(args.package.read_text(encoding="utf-8")), contract)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
