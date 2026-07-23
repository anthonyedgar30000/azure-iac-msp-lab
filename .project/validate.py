from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parent
SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
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
CANONICAL_WORKSTREAM_IDS = {
    "architecture-and-design-decisions",
    "azure-resource-plan-and-iac",
    "deployment-evidence-and-screenshots",
    "cost-health-and-configuration-telemetry",
    "servicetracer-findings-and-reports",
    "portfolio-and-demo-narrative",
}
REQUIRED_REPOSITORY_EVENTS = {
    "repository-pr-56-merged",
    "repository-pr-57-merged",
    "repository-pr-58-merged",
    "repository-pr-59-merged",
}
REQUIRED_DEPLOYMENT_EVENTS = {
    "demo-backend-api-deploy-30029515018-attempt-1",
    "collector-demo-api-what-if-30040676542",
    "collector-demo-api-deploy-30044644501",
}
REQUIRED_ENVIRONMENT_FACTS = {
    "operations-collector-control-plane",
    "azure-probe-scope-backends",
    "legacy-app-service-demo-partial-resources",
    "collector-demo-api-broad-what-if",
    "collector-demo-api-isolated-deployment-root",
    "collector-demo-api-public-endpoint",
    "collector-demo-api-isolated-what-if",
    "collector-demo-api-deployment-attempt",
    "frontend-live-demo-api-configuration",
    "actual-cost-and-credit",
}


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def text(value: Any, field: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{field} must be a non-empty string")
    return value.strip()


def sha(value: Any, field: str) -> str:
    result = text(value, field)
    require(bool(SHA.fullmatch(result)), f"{field} must be a lowercase 40-character SHA")
    return result


def digest(value: Any, field: str) -> str:
    result = text(value, field).removeprefix("sha256:")
    require(bool(SHA256.fullmatch(result)), f"{field} must be a lowercase SHA-256 digest")
    return result


def positive_int(value: Any, field: str) -> int:
    require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{field} must be a positive integer")
    return value


def object_value(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def list_value(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    require(isinstance(value, list), f"{field} must be an array")
    require(allow_empty or bool(value), f"{field} must not be empty")
    return value


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
    require(bool(lines), f"{label} must not be empty")
    result: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        try:
            result.append(object_value(json.loads(line), f"{label}[{number}]"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid JSONL at {path}:{number}: {exc}") from exc
    return result


def reject_live_keys(value: Any, path: str = "active-work") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(key not in FORBIDDEN_LIVE_KEYS, f"{path}.{key} persists live GitHub status")
            reject_live_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_live_keys(child, f"{path}[{index}]")


def validate_repository_events(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    pull_requests: set[int] = set()
    for index, event in enumerate(events, 1):
        prefix = f"repository-events[{index}]"
        event_id = text(event.get("event_id"), f"{prefix}.event_id")
        require(event_id not in by_id, f"Duplicate repository event_id: {event_id}")
        require(event.get("event_type") == "pull_request_merged", f"{prefix}.event_type must be pull_request_merged")
        pr = positive_int(event.get("pull_request"), f"{prefix}.pull_request")
        require(pr not in pull_requests, f"Duplicate repository pull request: {pr}")
        pull_requests.add(pr)
        text(event.get("repository"), f"{prefix}.repository")
        text(event.get("title"), f"{prefix}.title")
        sha(event.get("source_head"), f"{prefix}.source_head")
        sha(event.get("merge_commit"), f"{prefix}.merge_commit")
        if "ci_run_id" in event:
            positive_int(event.get("ci_run_id"), f"{prefix}.ci_run_id")
        for field in ("qualification", "evidence", "claim_boundary"):
            text(event.get(field), f"{prefix}.{field}")
        by_id[event_id] = event
    require(REQUIRED_REPOSITORY_EVENTS.issubset(by_id), "repository-events.jsonl is missing the PR #56-#59 reality-sync events")
    return by_id


def validate_active_work(active: dict[str, Any], repository_events: dict[str, dict[str, Any]]) -> None:
    require(active.get("schema_version") == "project.active-work.v3", "active-work.json must use project.active-work.v3")
    text(active.get("project"), "active-work.project")
    text(active.get("updated_on"), "active-work.updated_on")
    reject_live_keys(active)

    model = object_value(active.get("state_model"), "active-work.state_model")
    require(model.get("durable_event_log") == ".project/repository-events.jsonl", "active-work durable event log is invalid")
    require(model.get("live_repository_state_policy") == "query_live_github_never_persist_as_current_truth", "active-work live-state policy is invalid")
    require(set(list_value(model.get("forbidden_live_fields"), "active-work.state_model.forbidden_live_fields")) == FORBIDDEN_LIVE_KEYS, "active-work forbidden live fields differ from validator")

    for key, commit_field in (("last_substantive_baseline", "commit"), ("latest_promoted_repository_event", "merge_commit")):
        selected = object_value(active.get(key), f"active-work.{key}")
        event_id = text(selected.get("event_id"), f"active-work.{key}.event_id")
        event = repository_events.get(event_id)
        require(event is not None, f"active-work.{key} does not exist in repository-events.jsonl")
        require(event["pull_request"] == positive_int(selected.get("pull_request"), f"active-work.{key}.pull_request"), f"active-work.{key} pull request mismatch")
        require(event["merge_commit"] == sha(selected.get(commit_field), f"active-work.{key}.{commit_field}"), f"active-work.{key} commit mismatch")

    capabilities = object_value(active.get("repository_capabilities"), "active-work.repository_capabilities")
    for field in (
        "collector_hosted_demo_api_workflow_present_in_repository",
        "collector_demo_api_typed_readiness_assessor_present",
        "collector_demo_api_fail_closed_what_if_classifier_present",
        "collector_demo_api_isolated_bicep_root_present",
        "governed_persistence_controller_present",
        "legacy_app_service_demo_workflow_retired",
    ):
        require(capabilities.get(field) is True, f"active-work.repository_capabilities.{field} must be true")
    require(capabilities.get("demo_backend_api_workflow_present_in_repository") is False, "legacy demo workflow must remain retired")

    grants = list_value(active.get("bounded_authority_grants"), "active-work.bounded_authority_grants")
    require(len(grants) == 1, "Exactly one durable bounded authority grant is expected")
    grant = object_value(grants[0], "active-work.bounded_authority_grants[0]")
    require(grant.get("operation") == "read_only_azure_planning", "Durable grant must remain read-only planning")
    require(grant.get("azure_mutations_authorized") is False, "Durable grant must not authorize Azure mutation")

    defaults = object_value(active.get("authority_defaults"), "active-work.authority_defaults")
    for field in ("workflow_dispatch_authorized", "azure_authentication_authorized", "azure_mutations_authorized", "guest_command_authorized", "cleanup_authorized"):
        require(defaults.get(field) is False, f"active-work.authority_defaults.{field} must be false")

    deployment = object_value(active.get("deployment_state"), "active-work.deployment_state")
    collector_api = object_value(deployment.get("collector_hosted_demo_api"), "active-work.deployment_state.collector_hosted_demo_api")
    require(collector_api.get("last_observed_run_id") == 30044644501, "Latest collector API run must be 30044644501")
    require(collector_api.get("broad_unsafe_what_if_observed") is True, "Unsafe broad What-If must remain recorded")
    require(collector_api.get("isolated_what_if_observed") is True, "Accepted isolated What-If must remain recorded")
    require(collector_api.get("isolated_what_if_accepted") is True, "Isolated What-If acceptance must remain recorded")
    require(collector_api.get("deployment_attempt_observed") is True, "Deployment attempt must remain recorded")
    require(collector_api.get("deployment_succeeded") is False, "Failed deployment must not be promoted to success")
    require(collector_api.get("post_failure_azure_mutation_state") == "not_proven", "Post-failure Azure mutation state must remain unproven")
    for field in ("deployed", "tls_verified", "health_verified", "transactions_verified", "cors_verified", "frontend_live_verified"):
        require(collector_api.get(field) is False, f"collector_hosted_demo_api.{field} must remain false without new evidence")

    configuration = object_value(active.get("configuration_state"), "active-work.configuration_state")
    require(configuration.get("committed_live_report_url_present") is False, "Unverified live report URL must not be committed")
    require(configuration.get("committed_live_demo_api_url_present") is False, "Unverified live demo API URL must not be committed")

    latest = object_value(active.get("latest_promoted_evidence"), "active-work.latest_promoted_evidence")
    require(latest.get("event_id") == "collector-demo-api-deploy-30044644501", "Latest promoted evidence is not the full-sync Azure watermark")
    require(latest.get("run_id") == 30044644501, "Latest promoted evidence run mismatch")
    digest(latest.get("artifact_sha256"), "active-work.latest_promoted_evidence.artifact_sha256")
    require(latest.get("azure_mutations_authorized") is True, "Recorded deploy run must preserve its explicit mutation authority")
    require(latest.get("azure_mutations_performed") == "not_proven", "Failed deploy must not claim zero or successful Azure mutation")
    require(latest.get("deployment_succeeded") is False, "Latest failed deploy must remain unsuccessful")


def validate_environment_state(document: dict[str, Any]) -> int:
    require(document.get("schema_version") == "project.environment-state.v1", "environment-state schema is invalid")
    facts = list_value(document.get("facts"), "environment-state.facts")
    ids: set[str] = set()
    for index, raw in enumerate(facts):
        fact = object_value(raw, f"environment-state.facts[{index}]")
        fact_id = text(fact.get("fact_id"), f"environment-state.facts[{index}].fact_id")
        require(fact_id not in ids, f"Duplicate environment fact_id: {fact_id}")
        ids.add(fact_id)
        for field in ("value", "status", "last_observed_on", "source", "notes"):
            text(fact.get(field), f"environment-state.facts[{index}].{field}")
    require(REQUIRED_ENVIRONMENT_FACTS.issubset(ids), "environment-state.json is missing full-sync facts")
    return len(facts)


def validate_deployment_history(events: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    for index, event in enumerate(events, 1):
        prefix = f"deployment-history[{index}]"
        event_id = text(event.get("event_id"), f"{prefix}.event_id")
        require(event_id not in ids, f"Duplicate deployment event_id: {event_id}")
        ids.add(event_id)
        for field in ("event_type", "component", "status", "evidence", "notes"):
            text(event.get(field), f"{prefix}.{field}")
        for field in ("workflow_run_id", "run_attempt", "artifact_id"):
            if field in event:
                positive_int(event.get(field), f"{prefix}.{field}")
        if "repository_commit" in event:
            sha(event.get("repository_commit"), f"{prefix}.repository_commit")
        if "artifact_sha256" in event:
            digest(event.get("artifact_sha256"), f"{prefix}.artifact_sha256")
    require(REQUIRED_DEPLOYMENT_EVENTS.issubset(ids), "deployment-history.jsonl is missing required Azure events")


def validate_workstream_catalog(document: dict[str, Any]) -> int:
    require(document.get("schema_version") == "project.workstream-catalog.v1", "workstream-catalog schema is invalid")
    workstreams = list_value(document.get("workstreams"), "workstream-catalog.workstreams")
    ids = {text(object_value(item, "workstream").get("workstream_id"), "workstream.workstream_id") for item in workstreams}
    require(ids == CANONICAL_WORKSTREAM_IDS, "workstream-catalog must contain exactly the six canonical workstreams")
    return len(workstreams)


def validate_frontend_configuration() -> None:
    source = load_json(REPOSITORY_ROOT / "docs" / "report-source.json")
    require(source.get("schema_version") == "servicetracer.report-source.v1", "report-source schema is invalid")
    require(source.get("live_report_url") == "", "Unverified live report URL must be blank")
    require(source.get("live_demo_api_url") == "", "Unverified live demo API URL must be blank")
    text(source.get("fallback_report_url"), "report-source.fallback_report_url")


def validate_current_documents() -> None:
    handoff = (ROOT / "handoffs" / "current-state.md").read_text(encoding="utf-8")
    implementation = (REPOSITORY_ROOT / "docs" / "implementation-status.md").read_text(encoding="utf-8")
    overview = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    helix = load_json(REPOSITORY_ROOT / ".helix" / "repository-context.json")

    for marker in ("30044644501", "PR #56", "PR #58", "PR #59", "fresh Azure inventory and isolated What-If"):
        require(marker in handoff, f"current handoff is missing marker: {marker}")
    require("collector-hosted" in implementation.lower(), "implementation status does not describe the active collector-hosted architecture")
    require("PR #41 is a draft" not in implementation, "implementation status retains superseded PR #41 state")
    require("empty VPN backend pool" not in overview, "README retains the pre-deployment empty-backend claim")
    require(helix.get("classified_on") == "2026-07-23", ".helix repository context was not refreshed by the full sync")


def main() -> int:
    try:
        active = load_json(ROOT / "active-work.json")
        repository_events = load_jsonl(ROOT / "repository-events.jsonl", "repository-events")
        repository_by_id = validate_repository_events(repository_events)
        validate_active_work(active, repository_by_id)
        fact_count = validate_environment_state(load_json(ROOT / "environment-state.json"))
        deployment_events = load_jsonl(ROOT / "deployment-history.jsonl", "deployment-history")
        validate_deployment_history(deployment_events)
        workstream_count = validate_workstream_catalog(load_json(ROOT / "workstream-catalog.json"))
        validate_frontend_configuration()
        validate_current_documents()
        for path in (ROOT / "README.md", ROOT / "decisions.md", ROOT / "handoffs" / "current-state.md"):
            require(path.is_file() and bool(path.read_text(encoding="utf-8").strip()), f"Missing or empty required document: {path}")
    except (ValidationError, OSError) as exc:
        print(f"workflow-observability validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "workflow-observability validation passed: "
        f"{len(repository_events)} repository event(s), "
        f"{workstream_count} canonical workstream(s), "
        f"{fact_count} environment fact(s), "
        f"{len(deployment_events)} deployment event(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
