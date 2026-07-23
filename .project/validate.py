from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
ACTIVE_WORK = ROOT / "active-work.json"
REPOSITORY_EVENTS = ROOT / "repository-events.jsonl"
WORKSTREAM_CATALOG = ROOT / "workstream-catalog.json"
ENVIRONMENT_STATE = ROOT / "environment-state.json"
DEPLOYMENT_HISTORY = ROOT / "deployment-history.jsonl"
REQUIRED_DOCS = (ROOT / "README.md", ROOT / "decisions.md", ROOT / "handoffs/current-state.md")

CANONICAL_WORKSTREAM_IDS = {
    "architecture-and-design-decisions",
    "azure-resource-plan-and-iac",
    "deployment-evidence-and-screenshots",
    "cost-health-and-configuration-telemetry",
    "servicetracer-findings-and-reports",
    "portfolio-and-demo-narrative",
}
FORBIDDEN_LIVE_KEYS = {
    "repository_observation",
    "main_head",
    "open_pull_requests",
    "active_branch",
    "active_pull_request",
    "current_repository_head",
    "current_branch",
    "current_pull_request",
}
SHA = re.compile(r"^[0-9a-f]{40}$")


class ValidationError(RuntimeError):
    pass


def text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    return value.strip()


def sha(value: Any, field: str) -> str:
    result = text(value, field)
    if not SHA.fullmatch(result):
        raise ValidationError(f"{field} must be a lowercase 40-character SHA")
    return result


def positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValidationError(f"{field} must be a positive integer")
    return value


def object_value(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{field} must be an object")
    return value


def list_value(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValidationError(f"{field} must be a list")
    return value


def text_list(value: Any, field: str) -> list[str]:
    result = [text(item, f"{field}[{index}]") for index, item in enumerate(list_value(value, field))]
    if len(result) != len(set(result)):
        raise ValidationError(f"{field} contains duplicates")
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc
    return object_value(value, str(path))


def load_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing required file: {path}") from exc
    if not lines:
        raise ValidationError(f"{label} must contain at least one event")
    events: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid JSONL at {path}:{number}: {exc}") from exc
        events.append(object_value(event, f"{label}[{number}]"))
    return events


def reject_live_keys(value: Any, path: str = "active-work") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_LIVE_KEYS:
                raise ValidationError(f"{path}.{key} persists live GitHub status")
            reject_live_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_live_keys(item, f"{path}[{index}]")


def require_false_fields(value: dict[str, Any], fields: tuple[str, ...], prefix: str) -> None:
    for field in fields:
        if value.get(field) is not False:
            raise ValidationError(f"{prefix}.{field} must be false")


def validate_active_work(document: dict[str, Any]) -> None:
    if document.get("schema_version") != "project.active-work.v3":
        raise ValidationError("active-work.json must use project.active-work.v3")
    text(document.get("project"), "active-work.project")
    text(document.get("updated_on"), "active-work.updated_on")
    reject_live_keys(document)

    model = object_value(document.get("state_model"), "active-work.state_model")
    if model.get("durable_event_log") != ".project/repository-events.jsonl":
        raise ValidationError("active-work.state_model.durable_event_log is invalid")
    if model.get("event_log_semantics") != "curated_non_exhaustive_history":
        raise ValidationError("active-work.state_model.event_log_semantics is invalid")
    if model.get("live_repository_state_policy") != "query_live_github_never_persist_as_current_truth":
        raise ValidationError("active-work.state_model.live_repository_state_policy is invalid")
    if set(text_list(model.get("forbidden_live_fields"), "active-work.state_model.forbidden_live_fields")) != FORBIDDEN_LIVE_KEYS:
        raise ValidationError("active-work.state_model.forbidden_live_fields does not match the validator")
    distinctions = set(text_list(model.get("canonical_distinctions"), "active-work.state_model.canonical_distinctions"))
    required = {
        "promoted_repository_event != current_repository_head",
        "durable_history != live_status",
        "pull_request_merged != Azure_deployed",
        "workflow_present != workflow_dispatched",
        "CI_passed != service_validated",
    }
    if not required.issubset(distinctions):
        raise ValidationError("active-work.state_model.canonical_distinctions is incomplete")
    text(model.get("claim_boundary"), "active-work.state_model.claim_boundary")

    baseline = object_value(document.get("last_substantive_baseline"), "active-work.last_substantive_baseline")
    text(baseline.get("event_id"), "active-work.last_substantive_baseline.event_id")
    if baseline.get("branch") != "main":
        raise ValidationError("last_substantive_baseline.branch must be main")
    sha(baseline.get("commit"), "active-work.last_substantive_baseline.commit")
    positive_int(baseline.get("pull_request"), "active-work.last_substantive_baseline.pull_request")
    for field in ("title", "qualification", "claim_boundary"):
        text(baseline.get(field), f"active-work.last_substantive_baseline.{field}")

    promoted = object_value(document.get("latest_promoted_repository_event"), "active-work.latest_promoted_repository_event")
    text(promoted.get("event_id"), "active-work.latest_promoted_repository_event.event_id")
    positive_int(promoted.get("pull_request"), "active-work.latest_promoted_repository_event.pull_request")
    sha(promoted.get("merge_commit"), "active-work.latest_promoted_repository_event.merge_commit")
    for field in ("title", "merged_at", "qualification", "claim_boundary"):
        text(promoted.get(field), f"active-work.latest_promoted_repository_event.{field}")

    ownership = object_value(document.get("work_ownership_resolution"), "active-work.work_ownership_resolution")
    if ownership.get("state_semantics") != "resolve_live_from_git_and_github":
        raise ValidationError("work_ownership_resolution.state_semantics is invalid")
    require_false_fields(
        ownership,
        ("persist_active_branch", "persist_active_pull_request", "persist_current_ci_status"),
        "active-work.work_ownership_resolution",
    )
    text(ownership.get("rule"), "active-work.work_ownership_resolution.rule")

    capabilities = object_value(document.get("repository_capabilities"), "active-work.repository_capabilities")
    for field in (
        "demo_backend_api_workflow_present_in_repository",
        "publication_plan_workflow_present_in_repository",
        "publication_readiness_workflow_present_in_repository",
        "publication_execution_workflow_present_in_repository",
    ):
        if capabilities.get(field) is not True:
            raise ValidationError(f"active-work.repository_capabilities.{field} must be true")
    if capabilities.get("state_semantics") != "repository_declaration_not_runtime_proof":
        raise ValidationError("repository_capabilities.state_semantics is invalid")
    text(capabilities.get("claim_boundary"), "active-work.repository_capabilities.claim_boundary")

    grants = list_value(document.get("bounded_authority_grants"), "active-work.bounded_authority_grants")
    if len(grants) != 1:
        raise ValidationError("active-work.bounded_authority_grants must contain exactly one grant")
    grant = object_value(grants[0], "active-work.bounded_authority_grants[0]")
    for field in ("grant_id", "workflow_path", "operation", "authorized_by", "authorized_on",
                  "authorization_source", "protected_environment", "required_commit_semantics",
                  "required_confirmation", "state_semantics", "claim_boundary"):
        text(grant.get(field), f"active-work.bounded_authority_grants[0].{field}")
    for field in ("active_workflow_authorized", "dispatch_authorized", "azure_authentication_authorized"):
        if grant.get(field) is not True:
            raise ValidationError(f"active-work.bounded_authority_grants[0].{field} must be true")
    if grant.get("azure_mutations_authorized") is not False:
        raise ValidationError("bounded grant must keep azure_mutations_authorized false")
    if grant.get("state_semantics") != "bounded_exception_to_false_defaults":
        raise ValidationError("bounded grant state_semantics is invalid")
    text_list(grant.get("permitted_azure_operations"), "active-work.bounded_authority_grants[0].permitted_azure_operations")

    authority = object_value(document.get("authority_defaults"), "active-work.authority_defaults")
    require_false_fields(
        authority,
        ("workflow_dispatch_authorized", "azure_authentication_authorized",
         "azure_mutations_authorized", "guest_command_authorized"),
        "active-work.authority_defaults",
    )
    text(authority.get("rule"), "active-work.authority_defaults.rule")

    deployment = object_value(document.get("deployment_state"), "active-work.deployment_state")
    require_false_fields(
        deployment,
        ("demo_backend_api_dispatch_observed", "scoped_demo_what_if_observed",
         "azure_deployment_observed", "rbac_mutation_observed", "demo_backends_deployed",
         "demo_backend_listeners_verified", "demo_api_deployed", "demo_api_verified",
         "managed_identity_publication_observed", "blob_endpoint_verified",
         "browser_rendering_verified", "operationally_verified"),
        "active-work.deployment_state",
    )
    if deployment.get("state_semantics") != "promoted_evidence_only":
        raise ValidationError("deployment_state.state_semantics is invalid")
    text(deployment.get("claim_boundary"), "active-work.deployment_state.claim_boundary")

    evidence = object_value(document.get("latest_promoted_evidence"), "active-work.latest_promoted_evidence")
    for field in ("event_id", "workflow", "artifact", "artifact_sha256", "observed_on", "status", "freshness_boundary"):
        text(evidence.get(field), f"active-work.latest_promoted_evidence.{field}")
    positive_int(evidence.get("run_id"), "active-work.latest_promoted_evidence.run_id")
    sha(evidence.get("commit"), "active-work.latest_promoted_evidence.commit")
    require_false_fields(evidence, ("azure_mutations_authorized", "azure_mutations_performed"), "active-work.latest_promoted_evidence")

    resolution = object_value(document.get("live_state_resolution"), "active-work.live_state_resolution")
    for field in ("repository", "pull_requests", "ci", "azure"):
        text(resolution.get(field), f"active-work.live_state_resolution.{field}")
    if resolution.get("canonical_distinction") != "latest_promoted_repository_event != current_repository_head":
        raise ValidationError("live_state_resolution.canonical_distinction is invalid")


def validate_repository_events(events: list[dict[str, Any]], active: dict[str, Any]) -> None:
    event_ids: set[str] = set()
    pull_requests: set[int] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for index, event in enumerate(events, start=1):
        prefix = f"repository-events[{index}]"
        event_id = text(event.get("event_id"), f"{prefix}.event_id")
        if event_id in event_ids:
            raise ValidationError(f"Duplicate repository event_id: {event_id}")
        event_ids.add(event_id)
        by_id[event_id] = event
        if event.get("event_type") != "pull_request_merged":
            raise ValidationError(f"{prefix}.event_type must be pull_request_merged")
        text(event.get("repository"), f"{prefix}.repository")
        pull_request = positive_int(event.get("pull_request"), f"{prefix}.pull_request")
        if pull_request in pull_requests:
            raise ValidationError(f"Duplicate repository pull request: {pull_request}")
        pull_requests.add(pull_request)
        text(event.get("title"), f"{prefix}.title")
        sha(event.get("merge_commit"), f"{prefix}.merge_commit")
        if "source_head" in event:
            sha(event.get("source_head"), f"{prefix}.source_head")
        if "ci_run_id" in event:
            positive_int(event.get("ci_run_id"), f"{prefix}.ci_run_id")
        for field in ("qualification", "evidence", "claim_boundary"):
            text(event.get(field), f"{prefix}.{field}")

    for active_key, event_commit_key in (
        ("last_substantive_baseline", "commit"),
        ("latest_promoted_repository_event", "merge_commit"),
    ):
        selected = active[active_key]
        event = by_id.get(selected["event_id"])
        if event is None:
            raise ValidationError(f"{active_key}.event_id is missing from repository-events")
        if event["pull_request"] != selected["pull_request"] or event["merge_commit"] != selected[event_commit_key]:
            raise ValidationError(f"{active_key} does not match repository-events")


def validate_workstream_catalog(document: dict[str, Any]) -> int:
    if document.get("schema_version") != "project.workstream-catalog.v1":
        raise ValidationError("workstream-catalog.json schema is invalid")
    text(document.get("project"), "workstream-catalog.project")
    authority = object_value(document.get("workspace_authority"), "workstream-catalog.workspace_authority")
    for field in ("canonical_conversation_workspace", "implementation_authority", "azure_authority", "conflict_rule"):
        text(authority.get(field), f"workstream-catalog.workspace_authority.{field}")

    workstreams = list_value(document.get("workstreams"), "workstream-catalog.workstreams")
    ids: set[str] = set()
    for index, workstream_value in enumerate(workstreams):
        workstream = object_value(workstream_value, f"workstream-catalog.workstreams[{index}]")
        workstream_id = text(workstream.get("workstream_id"), f"workstream-catalog.workstreams[{index}].workstream_id")
        text(workstream.get("title"), f"workstream-catalog.workstreams[{index}].title")
        text(workstream.get("purpose"), f"workstream-catalog.workstreams[{index}].purpose")
        text(workstream.get("claim_boundary"), f"workstream-catalog.workstreams[{index}].claim_boundary")
        paths = text_list(workstream.get("primary_paths"), f"workstream-catalog.workstreams[{index}].primary_paths")
        if workstream_id == "deployment-evidence-and-screenshots" and ".project/repository-events.jsonl" not in paths:
            raise ValidationError("deployment evidence workstream must include repository-events.jsonl")
        if workstream_id in ids:
            raise ValidationError(f"Duplicate workstream_id: {workstream_id}")
        ids.add(workstream_id)
    if ids != CANONICAL_WORKSTREAM_IDS:
        raise ValidationError("workstream-catalog does not contain the six canonical workstreams")
    return len(workstreams)


def validate_environment_state(document: dict[str, Any]) -> int:
    if document.get("schema_version") != "project.environment-state.v1":
        raise ValidationError("environment-state.json schema is invalid")
    text(document.get("project"), "environment-state.project")
    facts = list_value(document.get("facts"), "environment-state.facts")
    ids: set[str] = set()
    for index, fact_value in enumerate(facts):
        fact = object_value(fact_value, f"environment-state.facts[{index}]")
        fact_id = text(fact.get("fact_id"), f"environment-state.facts[{index}].fact_id")
        for field in ("value", "status", "last_observed_on", "source"):
            text(fact.get(field), f"environment-state.facts[{index}].{field}")
        if fact_id in ids:
            raise ValidationError(f"Duplicate environment fact_id: {fact_id}")
        ids.add(fact_id)
    return len(facts)


def validate_deployment_history(events: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    for index, event in enumerate(events, start=1):
        event_id = text(event.get("event_id"), f"deployment-history[{index}].event_id")
        for field in ("event_type", "component", "status", "evidence"):
            text(event.get(field), f"deployment-history[{index}].{field}")
        if event_id in ids:
            raise ValidationError(f"Duplicate deployment event_id: {event_id}")
        ids.add(event_id)


def main() -> int:
    try:
        active = load_json(ACTIVE_WORK)
        validate_active_work(active)
        repository_events = load_jsonl(REPOSITORY_EVENTS, "repository-events")
        validate_repository_events(repository_events, active)
        workstream_count = validate_workstream_catalog(load_json(WORKSTREAM_CATALOG))
        fact_count = validate_environment_state(load_json(ENVIRONMENT_STATE))
        deployment_events = load_jsonl(DEPLOYMENT_HISTORY, "deployment-history")
        validate_deployment_history(deployment_events)
        for path in REQUIRED_DOCS:
            if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                raise ValidationError(f"Missing or empty required document: {path}")
    except ValidationError as exc:
        print(f"workflow-observability validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "workflow-observability validation passed: "
        f"{len(repository_events)} promoted repository event(s), "
        f"{workstream_count} canonical workstream(s), "
        f"{fact_count} environment fact(s), "
        f"{len(deployment_events)} deployment event(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
