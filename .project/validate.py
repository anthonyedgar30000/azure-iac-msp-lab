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

CANONICAL_WORKSTREAM_IDS = {
    "architecture-and-design-decisions",
    "azure-resource-plan-and-iac",
    "deployment-evidence-and-screenshots",
    "cost-health-and-configuration-telemetry",
    "servicetracer-findings-and-reports",
    "portfolio-and-demo-narrative",
}
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
LEGACY_SELF_REFERENTIAL_FIELDS = {
    "trusted_baseline",
    "workstreams",
    "known_open_pull_requests",
    "next_bounded_operation",
}


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


def require_commit(value: Any, field: str) -> str:
    commit = require_text(value, field)
    if not COMMIT_PATTERN.fullmatch(commit):
        raise ValidationError(f"{field} must be a 40-character lowercase SHA")
    return commit


def require_positive_int(value: Any, field: str, *, nullable: bool = False) -> int | None:
    if nullable and value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        suffix = "null or a positive integer" if nullable else "a positive integer"
        raise ValidationError(f"{field} must be {suffix}")
    return value


def require_text_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        suffix = "a list" if allow_empty else "a non-empty list"
        raise ValidationError(f"{field} must be {suffix}")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(require_text(item, f"{field}[{index}]"))
    return result


def validate_active_work(document: dict[str, Any]) -> int:
    if document.get("schema_version") != "project.active-work.v2":
        raise ValidationError("active-work.json has an unsupported schema_version")
    require_text(document.get("project"), "active-work.project")
    require_text(document.get("updated_on"), "active-work.updated_on")

    legacy_fields = sorted(LEGACY_SELF_REFERENTIAL_FIELDS.intersection(document))
    if legacy_fields:
        raise ValidationError(
            "active-work.json contains retired self-referential fields: "
            f"{legacy_fields}"
        )

    baseline = document.get("last_substantive_baseline")
    if not isinstance(baseline, dict):
        raise ValidationError("active-work.last_substantive_baseline must be an object")
    if baseline.get("branch") != "main":
        raise ValidationError("The last substantive baseline branch must be main")
    require_commit(baseline.get("commit"), "active-work.last_substantive_baseline.commit")
    require_positive_int(
        baseline.get("pull_request"),
        "active-work.last_substantive_baseline.pull_request",
    )
    for field in ("title", "qualification", "claim_boundary"):
        require_text(
            baseline.get(field),
            f"active-work.last_substantive_baseline.{field}",
        )

    observation = document.get("repository_observation")
    if not isinstance(observation, dict):
        raise ValidationError("active-work.repository_observation must be an object")
    require_text(observation.get("observed_on"), "active-work.repository_observation.observed_on")
    if observation.get("source") != "live_github":
        raise ValidationError("active-work.repository_observation.source must be live_github")
    require_commit(
        observation.get("main_head"),
        "active-work.repository_observation.main_head",
    )
    for field in ("head_semantics", "claim_boundary"):
        require_text(
            observation.get(field),
            f"active-work.repository_observation.{field}",
        )
    open_pull_requests = observation.get("open_pull_requests")
    if not isinstance(open_pull_requests, list):
        raise ValidationError(
            "active-work.repository_observation.open_pull_requests must be a list"
        )
    observed_prs: set[int] = set()
    for index, pull_request in enumerate(open_pull_requests):
        value = require_positive_int(
            pull_request,
            f"active-work.repository_observation.open_pull_requests[{index}]",
        )
        assert value is not None
        if value in observed_prs:
            raise ValidationError(
                "active-work.repository_observation.open_pull_requests contains duplicates"
            )
        observed_prs.add(value)

    change = document.get("authored_change")
    if not isinstance(change, dict):
        raise ValidationError("active-work.authored_change must be an object")
    for field in (
        "change_id",
        "branch",
        "write_owner",
        "scope",
        "authority",
        "failure_behavior",
        "rollback",
    ):
        require_text(change.get(field), f"active-work.authored_change.{field}")
    require_positive_int(
        change.get("pull_request"),
        "active-work.authored_change.pull_request",
        nullable=True,
    )
    if change.get("state_semantics") != "declaration_not_live_status":
        raise ValidationError(
            "active-work.authored_change.state_semantics must be "
            "declaration_not_live_status"
        )
    permitted_paths = require_text_list(
        change.get("permitted_paths"),
        "active-work.authored_change.permitted_paths",
    )
    if len(permitted_paths) != len(set(permitted_paths)):
        raise ValidationError(
            "active-work.authored_change.permitted_paths contains duplicates"
        )
    require_text_list(
        change.get("verification_criteria"),
        "active-work.authored_change.verification_criteria",
    )

    authority = document.get("authority_defaults")
    if not isinstance(authority, dict):
        raise ValidationError("active-work.authority_defaults must be an object")
    for field in (
        "active_workflow_present",
        "dispatch_authorized",
        "azure_authentication_authorized",
        "azure_mutations_authorized",
    ):
        if authority.get(field) is not False:
            raise ValidationError(f"active-work.authority_defaults.{field} must be false")
    require_text(authority.get("rule"), "active-work.authority_defaults.rule")

    resolution = document.get("live_state_resolution")
    if not isinstance(resolution, dict):
        raise ValidationError("active-work.live_state_resolution must be an object")
    for field in ("repository_head", "pull_requests", "ci", "azure"):
        require_text(resolution.get(field), f"active-work.live_state_resolution.{field}")
    if resolution.get("canonical_distinction") != (
        "last_substantive_baseline != current_repository_head"
    ):
        raise ValidationError(
            "active-work.live_state_resolution.canonical_distinction is invalid"
        )

    evidence = document.get("latest_promoted_evidence")
    if not isinstance(evidence, dict):
        raise ValidationError("active-work.latest_promoted_evidence must be an object")
    for field in (
        "event_id",
        "workflow",
        "commit",
        "artifact",
        "artifact_sha256",
        "observed_on",
        "status",
        "freshness_boundary",
    ):
        require_text(evidence.get(field), f"active-work.latest_promoted_evidence.{field}")
    require_positive_int(
        evidence.get("run_id"),
        "active-work.latest_promoted_evidence.run_id",
    )
    require_commit(
        evidence.get("commit"),
        "active-work.latest_promoted_evidence.commit",
    )
    if evidence.get("azure_mutations_authorized") is not False:
        raise ValidationError(
            "active-work.latest_promoted_evidence.azure_mutations_authorized must be false"
        )
    if evidence.get("azure_mutations_performed") is not False:
        raise ValidationError(
            "active-work.latest_promoted_evidence.azure_mutations_performed must be false"
        )

    return 1


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
        declaration_count = validate_active_work(load_json(ACTIVE_WORK_PATH))
        catalog_count = validate_workstream_catalog(load_json(WORKSTREAM_CATALOG_PATH))
        fact_count = validate_environment_state(load_json(ENVIRONMENT_STATE_PATH))
        event_count = validate_deployment_history(DEPLOYMENT_HISTORY_PATH)
        validate_required_docs()
    except ValidationError as exc:
        print(f"workflow-observability validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "workflow-observability validation passed: "
        f"{declaration_count} authored change declaration(s), "
        f"{catalog_count} canonical workstream(s), "
        f"{fact_count} environment fact(s), {event_count} deployment event(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
