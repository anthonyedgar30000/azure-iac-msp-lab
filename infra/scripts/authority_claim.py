#!/usr/bin/env python3
"""Deterministically validate an immutable single-use deployment authorization request.

This verifier intentionally does not authenticate to Azure and does not mutate GitHub.
The reusable workflow performs the atomic create-reference operation only after this
module has validated the exact request committed at the caller workflow's SHA.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import uuid
from typing import Any, Mapping


SCHEMA_VERSION = "project.deployment-authorization-request.v1"
DIGEST_PREFIX = "sha256:"
CLAIM_REF_PREFIX = "refs/tags/authority-consumed/"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

TOP_LEVEL_KEYS = {
    "schema_version",
    "request_id",
    "request_digest",
    "status",
    "active",
    "issued_at",
    "valid_until",
    "authorization_commit",
    "reviewed_source",
    "repository",
    "workflow",
    "target",
    "authority",
    "authorized_identity",
    "human_authority",
}
WORKFLOW_KEYS = {"path", "operation", "environment"}
TARGET_KEYS = {
    "subscription",
    "tenant",
    "resource_group",
    "location",
    "scope_hash",
}
AUTHORITY_KEYS = {
    "attempt_limit",
    "renewable",
    "transferable",
    "automatic_retry_authorized",
    "rollback_authorized",
    "cleanup_authorized",
    "rbac_mutation_authorized",
}
IDENTITY_KEYS = {"repository", "actor_path"}
HUMAN_AUTHORITY_KEYS = {"authority", "instruction", "interpretation"}


class ClaimValidationError(ValueError):
    """Raised when an authorization request fails closed."""


@dataclass(frozen=True)
class ClaimContext:
    repository: str
    authorization_commit: str
    caller_workflow_ref: str
    now: datetime


def canonical_request_bytes(request: Mapping[str, Any]) -> bytes:
    """Return deterministic JSON bytes excluding the self-referential digest."""
    payload = copy.deepcopy(dict(request))
    payload.pop("request_digest", None)
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def calculate_request_digest(request: Mapping[str, Any]) -> str:
    return DIGEST_PREFIX + hashlib.sha256(canonical_request_bytes(request)).hexdigest()


def _require_exact_keys(value: Any, expected: set[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimValidationError(f"{location} must be an object")
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise ClaimValidationError(
            f"{location} keys mismatch: missing={missing}, unknown={unknown}"
        )
    return value


def _require_nonempty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ClaimValidationError(f"{location} must be a non-empty string")
    if value != value.strip():
        raise ClaimValidationError(f"{location} must not contain surrounding whitespace")
    return value


def _require_sha1(value: Any, location: str) -> str:
    value = _require_nonempty_string(value, location)
    if not SHA1_RE.fullmatch(value):
        raise ClaimValidationError(f"{location} must be a lowercase 40-character commit SHA")
    return value


def _require_sha256(value: Any, location: str) -> str:
    value = _require_nonempty_string(value, location)
    if not SHA256_RE.fullmatch(value):
        raise ClaimValidationError(f"{location} must be formatted as sha256:<64 lowercase hex>")
    return value


def _parse_timestamp(value: Any, location: str) -> datetime:
    value = _require_nonempty_string(value, location)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ClaimValidationError(f"{location} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ClaimValidationError(f"{location} must include an explicit timezone")
    return parsed.astimezone(timezone.utc)


def _validate_request_id(value: Any) -> str:
    value = _require_nonempty_string(value, "request_id")
    try:
        parsed = uuid.UUID(value)
    except ValueError as exc:
        raise ClaimValidationError("request_id must be a valid UUID") from exc
    if parsed.version != 7:
        raise ClaimValidationError("request_id must be UUIDv7")
    if str(parsed) != value:
        raise ClaimValidationError("request_id must use canonical lowercase UUID form")
    return value


def _validate_repo_relative_path(value: Any, location: str) -> str:
    value = _require_nonempty_string(value, location)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ClaimValidationError(f"{location} must be a normalized repository-relative path")
    if str(path) != value:
        raise ClaimValidationError(f"{location} must use normalized POSIX separators")
    return value


def caller_workflow_path(repository: str, workflow_ref: str) -> str:
    repository = _require_nonempty_string(repository, "context.repository")
    workflow_ref = _require_nonempty_string(
        workflow_ref,
        "context.caller_workflow_ref",
    )
    prefix = repository + "/"
    if not workflow_ref.startswith(prefix) or "@" not in workflow_ref:
        raise ClaimValidationError(
            "caller workflow ref must use <repository>/<workflow-path>@<git-ref>"
        )
    path, git_ref = workflow_ref[len(prefix):].rsplit("@", 1)
    if not git_ref:
        raise ClaimValidationError("caller workflow ref must include a non-empty git ref")
    path = _validate_repo_relative_path(path, "caller workflow path")
    if not path.startswith(".github/workflows/") or not path.endswith((".yml", ".yaml")):
        raise ClaimValidationError("caller workflow must be under .github/workflows")
    return path


def _require_false(value: Any, location: str) -> None:
    if value is not False:
        raise ClaimValidationError(f"{location} must be false")


def validate_request(
    request: Mapping[str, Any],
    context: ClaimContext,
) -> dict[str, str]:
    """Validate request and return normalized outputs for the atomic claim step."""
    request = _require_exact_keys(request, TOP_LEVEL_KEYS, "request")
    workflow = _require_exact_keys(request["workflow"], WORKFLOW_KEYS, "workflow")
    target = _require_exact_keys(request["target"], TARGET_KEYS, "target")
    authority = _require_exact_keys(request["authority"], AUTHORITY_KEYS, "authority")
    identity = _require_exact_keys(
        request["authorized_identity"],
        IDENTITY_KEYS,
        "authorized_identity",
    )
    _require_exact_keys(
        request["human_authority"],
        HUMAN_AUTHORITY_KEYS,
        "human_authority",
    )

    if request["schema_version"] != SCHEMA_VERSION:
        raise ClaimValidationError(
            f"schema_version must equal {SCHEMA_VERSION!r}"
        )

    request_id = _validate_request_id(request["request_id"])
    supplied_digest = _require_sha256(request["request_digest"], "request_digest")
    calculated_digest = calculate_request_digest(request)
    if supplied_digest != calculated_digest:
        raise ClaimValidationError("request_digest does not match canonical request content")

    if request["status"] != "authorized_unconsumed":
        raise ClaimValidationError("status must be authorized_unconsumed")
    if request["active"] is not True:
        raise ClaimValidationError("active must be true")

    issued_at = _parse_timestamp(request["issued_at"], "issued_at")
    valid_until = _parse_timestamp(request["valid_until"], "valid_until")
    now = context.now.astimezone(timezone.utc)
    if not issued_at <= now <= valid_until:
        raise ClaimValidationError("request is not active at the current time")
    if issued_at >= valid_until:
        raise ClaimValidationError("issued_at must be earlier than valid_until")

    authorization_commit = _require_sha1(
        request["authorization_commit"],
        "authorization_commit",
    )
    expected_commit = _require_sha1(
        context.authorization_commit,
        "context.authorization_commit",
    )
    if authorization_commit != expected_commit:
        raise ClaimValidationError(
            "request authorization_commit must equal the caller workflow commit"
        )

    reviewed_source = _require_sha1(request["reviewed_source"], "reviewed_source")
    repository = _require_nonempty_string(request["repository"], "repository")
    if repository != context.repository:
        raise ClaimValidationError("request repository does not match the running repository")

    authorized_repository = _require_nonempty_string(
        identity["repository"],
        "authorized_identity.repository",
    )
    if authorized_repository != context.repository:
        raise ClaimValidationError(
            "authorized identity repository does not match the running repository"
        )
    if identity["actor_path"] != "github-actions/reusable-workflow":
        raise ClaimValidationError(
            "authorized_identity.actor_path must be github-actions/reusable-workflow"
        )

    expected_workflow_path = caller_workflow_path(
        context.repository,
        context.caller_workflow_ref,
    )
    workflow_path = _validate_repo_relative_path(workflow["path"], "workflow.path")
    if workflow_path != expected_workflow_path:
        raise ClaimValidationError(
            "request workflow.path does not match the caller workflow"
        )

    operation = _require_nonempty_string(workflow["operation"], "workflow.operation")
    environment = _require_nonempty_string(
        workflow["environment"],
        "workflow.environment",
    )

    subscription = _require_nonempty_string(
        target["subscription"],
        "target.subscription",
    )
    tenant = _require_nonempty_string(target["tenant"], "target.tenant")
    resource_group = _require_nonempty_string(
        target["resource_group"],
        "target.resource_group",
    )
    location = _require_nonempty_string(target["location"], "target.location")
    scope_hash = _require_sha256(target["scope_hash"], "target.scope_hash")

    if authority["attempt_limit"] != 1:
        raise ClaimValidationError("authority.attempt_limit must equal 1")
    _require_false(authority["renewable"], "authority.renewable")
    _require_false(authority["transferable"], "authority.transferable")
    _require_false(
        authority["automatic_retry_authorized"],
        "authority.automatic_retry_authorized",
    )
    _require_false(
        authority["rollback_authorized"],
        "authority.rollback_authorized",
    )
    _require_false(
        authority["cleanup_authorized"],
        "authority.cleanup_authorized",
    )
    _require_false(
        authority["rbac_mutation_authorized"],
        "authority.rbac_mutation_authorized",
    )

    human = request["human_authority"]
    _require_nonempty_string(human["authority"], "human_authority.authority")
    _require_nonempty_string(human["instruction"], "human_authority.instruction")
    _require_nonempty_string(
        human["interpretation"],
        "human_authority.interpretation",
    )

    claim_ref = CLAIM_REF_PREFIX + request_id
    return {
        "request_id": request_id,
        "request_digest": supplied_digest,
        "authorization_commit": authorization_commit,
        "reviewed_source": reviewed_source,
        "repository": repository,
        "caller_workflow_path": workflow_path,
        "operation": operation,
        "environment": environment,
        "subscription": subscription,
        "tenant": tenant,
        "resource_group": resource_group,
        "location": location,
        "scope_hash": scope_hash,
        "claim_ref": claim_ref,
    }


def build_validation_evidence(
    outputs: Mapping[str, str],
    *,
    validated_at: datetime,
) -> dict[str, Any]:
    return {
        "schema_version": "project.authorization-claim-validation-evidence.v1",
        "validated_at": validated_at.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "validation": "passed",
        "request_id": outputs["request_id"],
        "request_digest": outputs["request_digest"],
        "authorization_commit": outputs["authorization_commit"],
        "reviewed_source": outputs["reviewed_source"],
        "repository": outputs["repository"],
        "caller_workflow_path": outputs["caller_workflow_path"],
        "operation": outputs["operation"],
        "environment": outputs["environment"],
        "target_scope_hash": outputs["scope_hash"],
        "claim_ref": outputs["claim_ref"],
        "azure_oidc_requested": False,
        "github_mutation_performed_by_verifier": False,
    }


def _write_github_output(path: Path, outputs: Mapping[str, str]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        for key in sorted(outputs):
            value = outputs[key]
            if "\n" in value or "\r" in value:
                raise ClaimValidationError(f"output {key} contains a newline")
            stream.write(f"{key}={value}\n")


def _parse_now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    return _parse_timestamp(value, "--now")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--authorization-commit", required=True)
    parser.add_argument("--caller-workflow-ref", required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--evidence-output", type=Path)
    parser.add_argument("--now")
    args = parser.parse_args(argv)

    try:
        request_path = args.request
        normalized = _validate_repo_relative_path(
            request_path.as_posix(),
            "--request",
        )
        if not normalized.startswith(".project/deployment-requests/"):
            raise ClaimValidationError(
                "--request must be under .project/deployment-requests/"
            )
        if request_path.suffix != ".json":
            raise ClaimValidationError("--request must be a JSON file")

        request = json.loads(request_path.read_text(encoding="utf-8"))
        now = _parse_now(args.now)
        outputs = validate_request(
            request,
            ClaimContext(
                repository=args.repository,
                authorization_commit=args.authorization_commit,
                caller_workflow_ref=args.caller_workflow_ref,
                now=now,
            ),
        )
        evidence = build_validation_evidence(outputs, validated_at=now)

        if args.github_output:
            _write_github_output(args.github_output, outputs)
        if args.evidence_output:
            args.evidence_output.write_text(
                json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        json.dump(evidence, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (ClaimValidationError, json.JSONDecodeError, OSError) as exc:
        print(f"authorization claim validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
