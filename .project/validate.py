from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
ACTIVE_WORK_PATH = PROJECT_ROOT / "active-work.json"
WORKSTREAM_CATALOG_PATH = PROJECT_ROOT / "workstream-catalog.json"
ENVIRONMENT_STATE_PATH = PROJECT_ROOT / "environment-state.json"
DEPLOYMENT_HISTORY_PATH = PROJECT_ROOT / "deployment-history.jsonl"
REQUIRED_DOCS = (
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "decisions.md",
    PROJECT_ROOT / "handoffs" / "current-state.md",
)

ACTIVE_STATUSES = {
    "implementation_in_progress",
    "review_pending",
    "ci_pending",
    "ci_verified",
    "deployment_pending",
    "operational_verification_pending",
}
CANONICAL_WORKSTREAM_IDS = {
    "architecture-and-design-decisions",
    "azure-resource-plan-and-iac",
    "deployment-evidence-and-screenshots",
    "cost-health-and-configuration-telemetry",
    "servicetracer-findings-and-reports",
    "portfolio-and-demo-narrative",
}
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"Expected a JSON object in {path}")
    return value


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    return value.strip()


def validate_active_work(document: dict[str, Any]) -> int:
    if document.get("schema_version") != "project.active-work.v1":
        raise ValidationError("active-work.json has an unsupported schema_version")
    require_text(document.get("project"), "active-work.project")

    baseline = document.get("trusted_baseline")
    if not isinstance(baseline, dict):
        raise ValidationError("active-work.trusted_baseline must be an object")
    if baseline.get("branch") != "main":
        raise ValidationError("The trusted baseline branch must be main")
    commit = require_text(baseline.get("commit"), "active-work.trusted_baseline.commit")
    if not COMMIT_PATTERN.fullmatch(commit):
        raise ValidationError("The trusted baseline commit must be a 40-character lowercase SHA")

    workstreams = document.get("workstreams")
    if not isinstance(workstreams, list):
        raise ValidationError("active-work.workstreams must be a list")

    workstream_ids: set[str] = set()
    branches: set[str] = set()
    for index, workstream in enumerate(workstreams):
        prefix = f"active-work.workstreams[{index}]"
        if not isinstance(workstream, dict):
            raise ValidationError(f"{prefix} must be an object")
        workstream_id = require_text(workstream.get("workstream_id"), f"{prefix}.workstream_id")
        branch = require_text(workstream.get("branch"), f"{prefix}.branch")
        require_text(workstream.get("write_owner"), f"{prefix}.write_owner")
        require_text(workstream.get("scope"), f"{prefix}.scope")
        require_text(workstream.get("next_gate"), f"{prefix}.next_gate")
        status = require_text(workstream.get("status"), f"{prefix}.status")
        if status not in ACTIVE_STATUSES:
            raise ValidationError(f"{prefix}.status is not an allowed active status: {status}")
        if workstream_id in workstream_ids:
            raise ValidationError(f"Duplicate workstream_id: {workstream_id}")
        if branch in branches:
            raise ValidationError(f"Multiple active workstreams claim branch {branch}")
        workstream_ids.add(workstream_id)
        branches.add(branch)

        pull_request = workstream.get("pull_request")
        if pull_request is not None and (
            not isinstance(pull_request, int) or isinstance(pull_request, bool) or pull_request <= 0
        ):
            raise ValidationError(f"{prefix}.pull_request must be null or a positive integer")

    return len(workstreams)


def validate_workstream_catalog(document: dict[str, Any]) -> int:
    if document.get("schema_version") != "project.workstream-catalog.v1":
        raise ValidationError("workstream-catalog.json has an unsupported schema_version")
    require_text(document.get("project"), "workstream-catalog.project")

    authority = document.get("workspace_authority")
    if not isinstance(authority, dict):
        raise ValidationError("workstream-catalog.workspace_authority must be an object")
    for field in (
        "canonical_conversation_workspace",
        "implementation_authority",
        "azure_authority",
        "conflict_rule",
    ):
        require_text(authority.get(field), f"workstream-catalog.workspace_authority.{field}")

    workstreams = document.get("workstreams")
    if not isinstance(workstreams, list):
        raise ValidationError("workstream-catalog.workstreams must be a list")

    observed_ids: set[str] = set()
    for index, workstream in enumerate(workstreams):
        prefix = f"workstream-catalog.workstreams[{index}]"
        if not isinstance(workstream, dict):
            raise ValidationError(f"{prefix} must be an object")
        workstream_id = require_text(workstream.get("workstream_id"), f"{prefix}.workstream_id")
        require_text(workstream.get("title"), f"{prefix}.title")
        require_text(workstream.get("purpose"), f"{prefix}.purpose")
        require_text(workstream.get("claim_boundary"), f"{prefix}.claim_boundary")
        primary_paths = workstream.get("primary_paths")
        if not isinstance(primary_paths, list) or not primary_paths:
            raise ValidationError(f"{prefix}.primary_paths must be a non-empty list")
        for path_index, path in enumerate(primary_paths):
            require_text(path, f"{prefix}.primary_paths[{path_index}]")
        if workstream_id in observed_ids:
            raise ValidationError(f"Duplicate canonical workstream_id: {workstream_id}")
        observed_ids.add(workstream_id)

    if observed_ids != CANONICAL_WORKSTREAM_IDS:
        missing = sorted(CANONICAL_WORKSTREAM_IDS - observed_ids)
        unexpected = sorted(observed_ids - CANONICAL_WORKSTREAM_IDS)
        raise ValidationError(
            "workstream-catalog must contain exactly the six canonical workstreams; "
            f"missing={missing}, unexpected={unexpected}"
        )

    return len(workstreams)


def validate_environment_state(document: dict[str, Any]) -> int:
    if document.get("schema_version") != "project.environment-state.v1":
        raise ValidationError("environment-state.json has an unsupported schema_version")
    require_text(document.get("project"), "environment-state.project")

    facts = document.get("facts")
    if not isinstance(facts, list) or not facts:
        raise ValidationError("environment-state.facts must be a non-empty list")

    fact_ids: set[str] = set()
    for index, fact in enumerate(facts):
        prefix = f"environment-state.facts[{index}]"
        if not isinstance(fact, dict):
            raise ValidationError(f"{prefix} must be an object")
        fact_id = require_text(fact.get("fact_id"), f"{prefix}.fact_id")
        require_text(fact.get("value"), f"{prefix}.value")
        require_text(fact.get("status"), f"{prefix}.status")
        require_text(fact.get("last_observed_on"), f"{prefix}.last_observed_on")
        require_text(fact.get("source"), f"{prefix}.source")
        if fact_id in fact_ids:
            raise ValidationError(f"Duplicate fact_id: {fact_id}")
        fact_ids.add(fact_id)

    return len(facts)


def validate_deployment_history(path: Path) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing required file: {path}") from exc

    populated_lines = [line for line in lines if line.strip()]
    if not populated_lines:
        raise ValidationError("deployment-history.jsonl must contain at least one event")

    event_ids: set[str] = set()
    for line_number, line in enumerate(populated_lines, start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(
                f"Invalid JSONL event at {path}:{line_number}: {exc}"
            ) from exc
        if not isinstance(event, dict):
            raise ValidationError(f"Deployment event at line {line_number} must be an object")
        event_id = require_text(event.get("event_id"), f"deployment event {line_number}.event_id")
        require_text(event.get("event_type"), f"deployment event {line_number}.event_type")
        require_text(event.get("component"), f"deployment event {line_number}.component")
        require_text(event.get("status"), f"deployment event {line_number}.status")
        require_text(event.get("evidence"), f"deployment event {line_number}.evidence")
        if event_id in event_ids:
            raise ValidationError(f"Duplicate deployment event_id: {event_id}")
        event_ids.add(event_id)

    return len(populated_lines)


def validate_required_docs() -> None:
    for path in REQUIRED_DOCS:
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise ValidationError(f"Missing or empty required document: {path}")


def main() -> int:
    try:
        active_count = validate_active_work(load_json(ACTIVE_WORK_PATH))
        catalog_count = validate_workstream_catalog(load_json(WORKSTREAM_CATALOG_PATH))
        fact_count = validate_environment_state(load_json(ENVIRONMENT_STATE_PATH))
        event_count = validate_deployment_history(DEPLOYMENT_HISTORY_PATH)
        validate_required_docs()
    except ValidationError as exc:
        print(f"workflow-observability validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "workflow-observability validation passed: "
        f"{active_count} active workstream(s), {catalog_count} canonical workstream(s), "
        f"{fact_count} environment fact(s), {event_count} deployment event(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
