#!/usr/bin/env python3
"""Validate a commit-bound, single-use deployment authorization request.

Version 2 removes the impossible self-reference from v1. The request binds an
exact reviewed source commit. The reusable claim workflow proves that the only
tree delta between that reviewed source and the executing commit is the exact
request file, then atomically consumes the request before Azure OIDC begins.
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

SCHEMA_VERSION = "project.deployment-authorization-request.v2"
DIGEST_PREFIX = "sha256:"
CLAIM_REF_PREFIX = "refs/tags/authority-consumed/"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

TOP_LEVEL_KEYS = {
    "schema_version", "request_id", "request_digest", "status", "active",
    "issued_at", "valid_until", "reviewed_source", "repository", "workflow",
    "target", "authority", "authorized_identity", "human_authority",
}
WORKFLOW_KEYS = {"path", "operation", "environment"}
TARGET_KEYS = {"subscription", "tenant", "resource_group", "location", "scope_hash"}
AUTHORITY_KEYS = {
    "attempt_limit", "renewable", "transferable", "automatic_retry_authorized",
    "rollback_authorized", "cleanup_authorized", "provider_registration_authorized",
    "resource_group_mutation_authorized", "rbac_mutation_authorized",
    "entra_application_mutation_authorized", "deployment_authorized",
    "verification_authorized",
}
IDENTITY_KEYS = {"repository", "actor_path"}
HUMAN_KEYS = {"authority", "instruction", "interpretation"}


class ClaimValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ClaimContext:
    repository: str
    caller_workflow_ref: str
    now: datetime


def canonical_request_bytes(request: Mapping[str, Any]) -> bytes:
    payload = copy.deepcopy(dict(request))
    payload.pop("request_digest", None)
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def calculate_request_digest(request: Mapping[str, Any]) -> str:
    return DIGEST_PREFIX + hashlib.sha256(canonical_request_bytes(request)).hexdigest()


def exact_object(value: Any, expected: set[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaimValidationError(f"{location} must be an object")
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        raise ClaimValidationError(f"{location} keys mismatch: missing={missing}, unknown={unknown}")
    return value


def nonempty(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ClaimValidationError(f"{location} must be a non-empty trimmed string")
    return value


def sha1(value: Any, location: str) -> str:
    value = nonempty(value, location)
    if not SHA1_RE.fullmatch(value):
        raise ClaimValidationError(f"{location} must be a lowercase 40-character commit SHA")
    return value


def sha256_value(value: Any, location: str) -> str:
    value = nonempty(value, location)
    if not SHA256_RE.fullmatch(value):
        raise ClaimValidationError(f"{location} must be sha256:<64 lowercase hex>")
    return value


def timestamp(value: Any, location: str) -> datetime:
    value = nonempty(value, location)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ClaimValidationError(f"{location} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ClaimValidationError(f"{location} must include a timezone")
    return parsed.astimezone(timezone.utc)


def request_id(value: Any) -> str:
    value = nonempty(value, "request_id")
    try:
        parsed = uuid.UUID(value)
    except ValueError as exc:
        raise ClaimValidationError("request_id must be a UUID") from exc
    if parsed.version != 7 or str(parsed) != value:
        raise ClaimValidationError("request_id must be canonical lowercase UUIDv7")
    return value


def repo_path(value: Any, location: str) -> str:
    value = nonempty(value, location)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts or str(path) != value:
        raise ClaimValidationError(f"{location} must be a normalized repository-relative path")
    return value


def caller_path(repository: str, workflow_ref: str) -> str:
    prefix = repository + "/"
    if not workflow_ref.startswith(prefix) or "@" not in workflow_ref:
        raise ClaimValidationError("caller workflow ref must be <repository>/<path>@<ref>")
    path, ref = workflow_ref[len(prefix):].rsplit("@", 1)
    if not ref:
        raise ClaimValidationError("caller workflow ref lacks a git ref")
    path = repo_path(path, "caller workflow path")
    if not path.startswith(".github/workflows/") or not path.endswith((".yml", ".yaml")):
        raise ClaimValidationError("caller workflow must be under .github/workflows")
    return path


def bool_value(value: Any, location: str) -> bool:
    if not isinstance(value, bool):
        raise ClaimValidationError(f"{location} must be boolean")
    return value


def validate_request(request: Mapping[str, Any], context: ClaimContext) -> dict[str, str]:
    request = exact_object(request, TOP_LEVEL_KEYS, "request")
    workflow = exact_object(request["workflow"], WORKFLOW_KEYS, "workflow")
    target = exact_object(request["target"], TARGET_KEYS, "target")
    authority = exact_object(request["authority"], AUTHORITY_KEYS, "authority")
    identity = exact_object(request["authorized_identity"], IDENTITY_KEYS, "authorized_identity")
    human = exact_object(request["human_authority"], HUMAN_KEYS, "human_authority")

    if request["schema_version"] != SCHEMA_VERSION:
        raise ClaimValidationError(f"schema_version must equal {SCHEMA_VERSION}")
    rid = request_id(request["request_id"])
    supplied_digest = sha256_value(request["request_digest"], "request_digest")
    if supplied_digest != calculate_request_digest(request):
        raise ClaimValidationError("request_digest does not match canonical request")
    if request["status"] != "authorized_unconsumed" or request["active"] is not True:
        raise ClaimValidationError("request must be active and authorized_unconsumed")

    issued = timestamp(request["issued_at"], "issued_at")
    expiry = timestamp(request["valid_until"], "valid_until")
    now = context.now.astimezone(timezone.utc)
    if not issued <= now <= expiry or issued >= expiry:
        raise ClaimValidationError("request is outside its validity window")

    reviewed = sha1(request["reviewed_source"], "reviewed_source")
    repository = nonempty(request["repository"], "repository")
    if repository != context.repository:
        raise ClaimValidationError("request repository does not match runtime repository")
    if identity["repository"] != repository or identity["actor_path"] != "github-actions/reusable-workflow-v2":
        raise ClaimValidationError("authorized identity boundary does not match v2 reusable workflow")

    expected_workflow = caller_path(context.repository, context.caller_workflow_ref)
    workflow_path = repo_path(workflow["path"], "workflow.path")
    if workflow_path != expected_workflow:
        raise ClaimValidationError("request workflow path does not match caller")

    if authority["attempt_limit"] != 1:
        raise ClaimValidationError("attempt_limit must equal 1")
    for key in AUTHORITY_KEYS - {"attempt_limit"}:
        bool_value(authority[key], f"authority.{key}")
    for key in ("renewable", "transferable", "automatic_retry_authorized", "rollback_authorized", "cleanup_authorized"):
        if authority[key]:
            raise ClaimValidationError(f"authority.{key} must be false")

    for key in HUMAN_KEYS:
        nonempty(human[key], f"human_authority.{key}")

    outputs = {
        "request_id": rid,
        "request_digest": supplied_digest,
        "reviewed_source": reviewed,
        "repository": repository,
        "caller_workflow_path": workflow_path,
        "operation": nonempty(workflow["operation"], "workflow.operation"),
        "environment": nonempty(workflow["environment"], "workflow.environment"),
        "subscription": nonempty(target["subscription"], "target.subscription"),
        "tenant": nonempty(target["tenant"], "target.tenant"),
        "resource_group": nonempty(target["resource_group"], "target.resource_group"),
        "location": nonempty(target["location"], "target.location"),
        "scope_hash": sha256_value(target["scope_hash"], "target.scope_hash"),
        "claim_ref": CLAIM_REF_PREFIX + rid,
    }
    for key in AUTHORITY_KEYS - {"attempt_limit"}:
        outputs[key] = "true" if authority[key] else "false"
    return outputs


def emit_github_output(path: Path, outputs: Mapping[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in outputs.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--caller-workflow-ref", required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--evidence-output", type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        outputs = validate_request(request, ClaimContext(args.repository, args.caller_workflow_ref, datetime.now(timezone.utc)))
    except (OSError, json.JSONDecodeError, ClaimValidationError) as exc:
        print(f"authorization validation failed: {exc}", file=sys.stderr)
        return 1
    if args.github_output:
        emit_github_output(args.github_output, outputs)
    if args.evidence_output:
        args.evidence_output.write_text(json.dumps({"validation":"passed", **outputs}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outputs, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
