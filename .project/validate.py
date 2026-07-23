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
    "architecture-and-design-decisions", "azure-resource-plan-and-iac",
    "deployment-evidence-and-screenshots", "cost-health-and-configuration-telemetry",
    "servicetracer-findings-and-reports", "portfolio-and-demo-narrative",
}
FORBIDDEN_LIVE_KEYS = {
    "repository_observation", "main_head", "open_pull_requests", "active_branch",
    "active_pull_request", "current_repository_head", "current_branch", "current_pull_request",
}
SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


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


def digest(value: Any, field: str) -> str:
    result = text(value, field).removeprefix("sha256:")
    if not SHA256.fullmatch(result):
        raise ValidationError(f"{field} must be a lowercase SHA-256 digest")
    return result


def posint(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValidationError(f"{field} must be a positive integer")
    return value


def nonneg(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValidationError(f"{field} must be a non-negative integer")
    return value


def boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be a boolean")
    return value


def obj(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{field} must be an object")
    return value


def items(value: Any, field: str, *, empty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (not empty and not value):
        raise ValidationError(f"{field} must be a list")
    return value


def texts(value: Any, field: str) -> list[str]:
    result = [text(item, f"{field}[{i}]") for i, item in enumerate(items(value, field))]
    if len(result) != len(set(result)):
        raise ValidationError(f"{field} contains duplicates")
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        return obj(json.loads(path.read_text(encoding="utf-8")), str(path))
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc


def load_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing required file: {path}") from exc
    if not lines:
        raise ValidationError(f"{label} must contain at least one event")
    result: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        try:
            result.append(obj(json.loads(line), f"{label}[{number}]"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid JSONL at {path}:{number}: {exc}") from exc
    return result


def reject_live_keys(value: Any, path: str = "active-work") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_LIVE_KEYS:
                raise ValidationError(f"{path}.{key} persists live GitHub status")
            reject_live_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_live_keys(child, f"{path}[{index}]")


def false_fields(value: dict[str, Any], fields: tuple[str, ...], prefix: str) -> None:
    for field in fields:
        if value.get(field) is not False:
            raise ValidationError(f"{prefix}.{field} must be false")


def evidence(value: dict[str, Any], prefix: str) -> None:
    for field in ("event_id", "workflow", "status", "freshness_boundary"):
        text(value.get(field), f"{prefix}.{field}")
    posint(value.get("run_id"), f"{prefix}.run_id")
    digest(value.get("artifact_sha256"), f"{prefix}.artifact_sha256")
    false_fields(value, ("azure_mutations_authorized", "azure_mutations_performed"), prefix)
    if any(key in value for key in ("artifact_id", "reviewed_commit", "generated_at")):
        posint(value.get("artifact_id"), f"{prefix}.artifact_id")
        posint(value.get("run_attempt"), f"{prefix}.run_attempt")
        sha(value.get("reviewed_commit"), f"{prefix}.reviewed_commit")
        text(value.get("generated_at"), f"{prefix}.generated_at")
        for field in ("arm_validation_observed", "arm_what_if_observed"):
            if field in value:
                boolean(value.get(field), f"{prefix}.{field}")
    else:
        text(value.get("artifact"), f"{prefix}.artifact")
        sha(value.get("commit"), f"{prefix}.commit")
        text(value.get("observed_on"), f"{prefix}.observed_on")


def validate_active_work(document: dict[str, Any]) -> None:
    if document.get("schema_version") != "project.active-work.v3":
        raise ValidationError("active-work.json must use project.active-work.v3")
    text(document.get("project"), "active-work.project")
    text(document.get("updated_on"), "active-work.updated_on")
    reject_live_keys(document)

    model = obj(document.get("state_model"), "active-work.state_model")
    expected_model = {
        "durable_event_log": ".project/repository-events.jsonl",
        "event_log_semantics": "curated_non_exhaustive_history",
        "live_repository_state_policy": "query_live_github_never_persist_as_current_truth",
    }
    for field, expected in expected_model.items():
        if model.get(field) != expected:
            raise ValidationError(f"active-work.state_model.{field} is invalid")
    if set(texts(model.get("forbidden_live_fields"), "active-work.state_model.forbidden_live_fields")) != FORBIDDEN_LIVE_KEYS:
        raise ValidationError("active-work.state_model.forbidden_live_fields does not match the validator")
    required = {
        "promoted_repository_event != current_repository_head", "durable_history != live_status",
        "pull_request_merged != Azure_deployed", "workflow_present != workflow_dispatched",
        "CI_passed != service_validated",
    }
    if not required.issubset(set(texts(model.get("canonical_distinctions"), "active-work.state_model.canonical_distinctions"))):
        raise ValidationError("active-work.state_model.canonical_distinctions is incomplete")
    text(model.get("claim_boundary"), "active-work.state_model.claim_boundary")

    baseline = obj(document.get("last_substantive_baseline"), "active-work.last_substantive_baseline")
    text(baseline.get("event_id"), "active-work.last_substantive_baseline.event_id")
    if baseline.get("branch") != "main":
        raise ValidationError("last_substantive_baseline.branch must be main")
    sha(baseline.get("commit"), "active-work.last_substantive_baseline.commit")
    posint(baseline.get("pull_request"), "active-work.last_substantive_baseline.pull_request")
    for field in ("title", "qualification", "claim_boundary"):
        text(baseline.get(field), f"active-work.last_substantive_baseline.{field}")

    promoted = obj(document.get("latest_promoted_repository_event"), "active-work.latest_promoted_repository_event")
    text(promoted.get("event_id"), "active-work.latest_promoted_repository_event.event_id")
    posint(promoted.get("pull_request"), "active-work.latest_promoted_repository_event.pull_request")
    sha(promoted.get("merge_commit"), "active-work.latest_promoted_repository_event.merge_commit")
    if "source_head" in promoted:
        sha(promoted.get("source_head"), "active-work.latest_promoted_repository_event.source_head")
    if "ci_run_id" in promoted:
        posint(promoted.get("ci_run_id"), "active-work.latest_promoted_repository_event.ci_run_id")
    for field in ("title", "merged_at", "qualification", "claim_boundary"):
        text(promoted.get(field), f"active-work.latest_promoted_repository_event.{field}")

    ownership = obj(document.get("work_ownership_resolution"), "active-work.work_ownership_resolution")
    if ownership.get("state_semantics") != "resolve_live_from_git_and_github":
        raise ValidationError("work_ownership_resolution.state_semantics is invalid")
    false_fields(ownership, ("persist_active_branch", "persist_active_pull_request", "persist_current_ci_status"), "active-work.work_ownership_resolution")
    text(ownership.get("rule"), "active-work.work_ownership_resolution.rule")

    capabilities = obj(document.get("repository_capabilities"), "active-work.repository_capabilities")
    true_capabilities = (
        "publication_plan_workflow_present_in_repository", "publication_readiness_workflow_present_in_repository",
        "publication_execution_workflow_present_in_repository", "collector_hosted_demo_api_workflow_present_in_repository",
        "collector_demo_api_typed_readiness_assessor_present", "collector_demo_api_fail_closed_what_if_classifier_present",
        "legacy_app_service_demo_workflow_retired",
    )
    for field in true_capabilities:
        if capabilities.get(field) is not True:
            raise ValidationError(f"active-work.repository_capabilities.{field} must be true")
    if capabilities.get("demo_backend_api_workflow_present_in_repository") is not False:
        raise ValidationError("active-work.repository_capabilities.demo_backend_api_workflow_present_in_repository must be false")
    if capabilities.get("state_semantics") != "repository_declaration_not_runtime_proof":
        raise ValidationError("repository_capabilities.state_semantics is invalid")
    text(capabilities.get("claim_boundary"), "active-work.repository_capabilities.claim_boundary")

    grants = items(document.get("bounded_authority_grants"), "active-work.bounded_authority_grants")
    if len(grants) != 1:
        raise ValidationError("active-work.bounded_authority_grants must contain exactly one grant")
    grant = obj(grants[0], "active-work.bounded_authority_grants[0]")
    for field in ("grant_id", "workflow_path", "operation", "authorized_by", "authorized_on", "authorization_source",
                  "protected_environment", "required_commit_semantics", "required_confirmation", "state_semantics", "claim_boundary"):
        text(grant.get(field), f"active-work.bounded_authority_grants[0].{field}")
    for field in ("active_workflow_authorized", "dispatch_authorized", "azure_authentication_authorized"):
        if grant.get(field) is not True:
            raise ValidationError(f"active-work.bounded_authority_grants[0].{field} must be true")
    false_fields(grant, ("azure_mutations_authorized",), "active-work.bounded_authority_grants[0]")
    if grant.get("state_semantics") != "bounded_exception_to_false_defaults":
        raise ValidationError("bounded grant state_semantics is invalid")
    texts(grant.get("permitted_azure_operations"), "active-work.bounded_authority_grants[0].permitted_azure_operations")

    authority = obj(document.get("authority_defaults"), "active-work.authority_defaults")
    false_fields(authority, ("workflow_dispatch_authorized", "azure_authentication_authorized", "azure_mutations_authorized", "guest_command_authorized"), "active-work.authority_defaults")
    text(authority.get("rule"), "active-work.authority_defaults.rule")

    deployment = obj(document.get("deployment_state"), "active-work.deployment_state")
    true_fields = (
        "demo_backend_api_dispatch_observed", "scoped_demo_what_if_observed", "azure_deployment_observed",
        "demo_backends_deployed", "collector_demo_api_dispatch_observed", "collector_vm_observed",
        "collector_vm_running_observed", "failed_app_service_attempt_partial_mutation_observed",
    )
    false_state_fields = (
        "rbac_mutation_observed", "demo_backend_listeners_verified", "demo_api_deployed", "demo_api_verified",
        "managed_identity_publication_observed", "blob_endpoint_verified", "browser_rendering_verified", "operationally_verified",
        "collector_demo_api_readiness_completed", "collector_demo_api_scoped_arm_what_if_observed",
        "collector_demo_api_public_ip_observed", "collector_demo_api_deployed", "collector_demo_api_tls_verified",
        "collector_demo_api_health_verified", "collector_demo_api_transactions_verified", "collector_demo_api_cors_verified",
        "collector_vm_public_ip_observed",
    )
    for field in true_fields:
        if deployment.get(field) is not True:
            raise ValidationError(f"active-work.deployment_state.{field} must be true")
    false_fields(deployment, false_state_fields, "active-work.deployment_state")
    if deployment.get("state_semantics") != "promoted_evidence_only":
        raise ValidationError("deployment_state.state_semantics is invalid")
    text(deployment.get("claim_boundary"), "active-work.deployment_state.claim_boundary")
    posint(deployment.get("collector_demo_api_last_observed_run_id"), "active-work.deployment_state.collector_demo_api_last_observed_run_id")
    text(deployment.get("collector_vm_private_ip_observed"), "active-work.deployment_state.collector_vm_private_ip_observed")
    text(deployment.get("collector_vm_size_observed"), "active-work.deployment_state.collector_vm_size_observed")
    current = nonneg(deployment.get("public_ip_quota_current_observed"), "active-work.deployment_state.public_ip_quota_current_observed")
    limit = nonneg(deployment.get("public_ip_quota_limit_observed"), "active-work.deployment_state.public_ip_quota_limit_observed")
    remaining = nonneg(deployment.get("public_ip_quota_remaining_observed"), "active-work.deployment_state.public_ip_quota_remaining_observed")
    if limit < current or remaining != limit - current:
        raise ValidationError("active-work.deployment_state public IP quota values are inconsistent")
    for field in ("public_ip_quota_observed_at", "orphan_application_insights_observed", "orphan_storage_account_status"):
        text(deployment.get(field), f"active-work.deployment_state.{field}")

    latest = obj(document.get("latest_promoted_evidence"), "active-work.latest_promoted_evidence")
    evidence(latest, "active-work.latest_promoted_evidence")
    workstreams = obj(document.get("promoted_evidence_by_workstream"), "active-work.promoted_evidence_by_workstream")
    evidence(obj(workstreams.get("report_publication"), "active-work.promoted_evidence_by_workstream.report_publication"), "active-work.promoted_evidence_by_workstream.report_publication")
    collector = obj(workstreams.get("collector_demo_api"), "active-work.promoted_evidence_by_workstream.collector_demo_api")
    evidence(collector, "active-work.promoted_evidence_by_workstream.collector_demo_api")
    if (collector.get("event_id"), collector.get("run_id")) != (latest.get("event_id"), latest.get("run_id")):
        raise ValidationError("latest_promoted_evidence must match collector_demo_api promoted evidence")

    resolution = obj(document.get("live_state_resolution"), "active-work.live_state_resolution")
    for field in ("repository", "pull_requests", "ci", "azure"):
        text(resolution.get(field), f"active-work.live_state_resolution.{field}")
    if resolution.get("canonical_distinction") != "latest_promoted_repository_event != current_repository_head":
        raise ValidationError("live_state_resolution.canonical_distinction is invalid")


def validate_repository_events(events: list[dict[str, Any]], active: dict[str, Any]) -> None:
    event_ids: set[str] = set()
    pull_requests: set[int] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for index, event in enumerate(events, 1):
        prefix = f"repository-events[{index}]"
        event_id = text(event.get("event_id"), f"{prefix}.event_id")
        if event_id in event_ids:
            raise ValidationError(f"Duplicate repository event_id: {event_id}")
        event_ids.add(event_id)
        by_id[event_id] = event
        if event.get("event_type") != "pull_request_merged":
            raise ValidationError(f"{prefix}.event_type must be pull_request_merged")
        text(event.get("repository"), f"{prefix}.repository")
        pr = posint(event.get("pull_request"), f"{prefix}.pull_request")
        if pr in pull_requests:
            raise ValidationError(f"Duplicate repository pull request: {pr}")
        pull_requests.add(pr)
        text(event.get("title"), f"{prefix}.title")
        sha(event.get("merge_commit"), f"{prefix}.merge_commit")
        if "source_head" in event:
            sha(event.get("source_head"), f"{prefix}.source_head")
        if "ci_run_id" in event:
            posint(event.get("ci_run_id"), f"{prefix}.ci_run_id")
        for field in ("qualification", "evidence", "claim_boundary"):
            text(event.get(field), f"{prefix}.{field}")
    for active_key, commit_key in (("last_substantive_baseline", "commit"), ("latest_promoted_repository_event", "merge_commit")):
        selected = active[active_key]
        event = by_id.get(selected["event_id"])
        if event is None or event["pull_request"] != selected["pull_request"] or event["merge_commit"] != selected[commit_key]:
            raise ValidationError(f"{active_key} does not match repository-events")


def validate_workstream_catalog(document: dict[str, Any]) -> int:
    if document.get("schema_version") != "project.workstream-catalog.v1":
        raise ValidationError("workstream-catalog.json schema is invalid")
    text(document.get("project"), "workstream-catalog.project")
    authority = obj(document.get("workspace_authority"), "workstream-catalog.workspace_authority")
    for field in ("canonical_conversation_workspace", "implementation_authority", "azure_authority", "conflict_rule"):
        text(authority.get(field), f"workstream-catalog.workspace_authority.{field}")
    workstreams = items(document.get("workstreams"), "workstream-catalog.workstreams")
    ids: set[str] = set()
    for index, raw in enumerate(workstreams):
        workstream = obj(raw, f"workstream-catalog.workstreams[{index}]")
        wid = text(workstream.get("workstream_id"), f"workstream-catalog.workstreams[{index}].workstream_id")
        for field in ("title", "purpose", "claim_boundary"):
            text(workstream.get(field), f"workstream-catalog.workstreams[{index}].{field}")
        paths = texts(workstream.get("primary_paths"), f"workstream-catalog.workstreams[{index}].primary_paths")
        if wid == "deployment-evidence-and-screenshots" and ".project/repository-events.jsonl" not in paths:
            raise ValidationError("deployment evidence workstream must include repository-events.jsonl")
        if wid in ids:
            raise ValidationError(f"Duplicate workstream_id: {wid}")
        ids.add(wid)
    if ids != CANONICAL_WORKSTREAM_IDS:
        raise ValidationError("workstream-catalog does not contain the six canonical workstreams")
    return len(workstreams)


def validate_environment_state(document: dict[str, Any]) -> int:
    if document.get("schema_version") != "project.environment-state.v1":
        raise ValidationError("environment-state.json schema is invalid")
    text(document.get("project"), "environment-state.project")
    text(document.get("updated_on"), "environment-state.updated_on")
    facts = items(document.get("facts"), "environment-state.facts")
    ids: set[str] = set()
    for index, raw in enumerate(facts):
        fact = obj(raw, f"environment-state.facts[{index}]")
        fid = text(fact.get("fact_id"), f"environment-state.facts[{index}].fact_id")
        for field in ("value", "status", "last_observed_on", "source"):
            text(fact.get(field), f"environment-state.facts[{index}].{field}")
        if "notes" in fact:
            text(fact.get("notes"), f"environment-state.facts[{index}].notes")
        if fid in ids:
            raise ValidationError(f"Duplicate environment fact_id: {fid}")
        ids.add(fid)
    return len(facts)


def validate_deployment_history(events: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    for index, event in enumerate(events, 1):
        prefix = f"deployment-history[{index}]"
        event_id = text(event.get("event_id"), f"{prefix}.event_id")
        for field in ("event_type", "component", "status", "evidence"):
            text(event.get(field), f"{prefix}.{field}")
        if event_id in ids:
            raise ValidationError(f"Duplicate deployment event_id: {event_id}")
        ids.add(event_id)
        for field in ("workflow_run_id", "run_attempt", "artifact_id"):
            if field in event:
                posint(event.get(field), f"{prefix}.{field}")
        for field in ("repository_commit", "reviewed_commit"):
            if field in event:
                sha(event.get(field), f"{prefix}.{field}")
        if "artifact_sha256" in event:
            digest(event.get("artifact_sha256"), f"{prefix}.artifact_sha256")
        for field in ("azure_mutations_authorized", "azure_mutations_performed"):
            if field in event:
                boolean(event.get(field), f"{prefix}.{field}")


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
