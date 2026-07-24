from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parent
TEST_LOG = Path("/tmp/tests.log")
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
    "collector-demo-api-deploy-30050103888",
    "collector-demo-api-what-if-30053018998",
}
REQUIRED_FACTS = {
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
    "independent-demo-api-repository-architecture",
    "independent-demo-api-vm-size",
    "independent-demo-api-Azure-state",
    "independent-demo-api-public-ip-headroom",
    "independent-demo-api-dual-subscription-plan",
    "independent-demo-api-planning-authorization",
    "independent-demo-api-target-subscription",
    "independent-demo-api-github-environment",
    "independent-demo-api-oidc-identities-rbac",
    "independent-demo-api-default-location",
}
CANONICAL_WORKSTREAMS = {
    "architecture-and-design-decisions",
    "azure-resource-plan-and-iac",
    "deployment-evidence-and-screenshots",
    "cost-health-and-configuration-telemetry",
    "servicetracer-findings-and-reports",
    "portfolio-and-demo-narrative",
}
FALSE_AUTHORITY_FIELDS = {
    "workflow_dispatch_authorized",
    "azure_authentication_authorized",
    "azure_mutations_authorized",
    "guest_command_authorized",
    "cleanup_authorized",
    "github_environment_mutation_authorized",
    "github_secret_mutation_authorized",
    "entra_identity_mutation_authorized",
    "azure_rbac_mutation_authorized",
    "architecture_ratification_complete",
}
FALSE_INDEPENDENT_STATE_FIELDS = {
    "planner_dispatched",
    "architecture_ratified",
    "target_subscription_selected",
    "github_environment_configured",
    "dependency_identity_configured",
    "target_identity_configured",
    "required_rbac_configured",
    "target_resource_group_observed",
    "deployed",
    "tls_verified",
    "health_verified",
    "transactions_verified",
    "cors_verified",
    "frontend_live_verified",
}


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_text(value: Any, field: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{field} must be a non-empty string")
    return value.strip()


def require_sha(value: Any, field: str) -> str:
    result = require_text(value, field)
    require(bool(SHA.fullmatch(result)), f"{field} must be a lowercase 40-character SHA")
    return result


def require_digest(value: Any, field: str) -> str:
    result = require_text(value, field).removeprefix("sha256:")
    require(bool(SHA256.fullmatch(result)), f"{field} must be a lowercase SHA-256 digest")
    return result


def require_positive_int(value: Any, field: str) -> int:
    require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{field} must be a positive integer")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def require_list(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    require(isinstance(value, list), f"{field} must be an array")
    require(allow_empty or bool(value), f"{field} must not be empty")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    return require_object(value, str(path))


def load_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {path}") from exc
    require(bool(lines), f"{label} must not be empty")
    result: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        try:
            result.append(require_object(json.loads(line), f"{label}[{number}]"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSONL at {path}:{number}: {exc}") from exc
    return result


def reject_live_keys(value: Any, path: str = "active-work") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(key not in FORBIDDEN_LIVE_KEYS, f"{path}.{key} persists live GitHub state")
            reject_live_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_live_keys(child, f"{path}[{index}]")


def validate_repository_events() -> dict[str, dict[str, Any]]:
    events = load_jsonl(ROOT / "repository-events.jsonl", "repository-events")
    by_id: dict[str, dict[str, Any]] = {}
    pull_requests: set[int] = set()
    for index, event in enumerate(events, 1):
        prefix = f"repository-events[{index}]"
        event_id = require_text(event.get("event_id"), f"{prefix}.event_id")
        require(event_id not in by_id, f"duplicate repository event_id: {event_id}")
        require(event.get("event_type") == "pull_request_merged", f"{prefix}.event_type must be pull_request_merged")
        pr = require_positive_int(event.get("pull_request"), f"{prefix}.pull_request")
        require(pr not in pull_requests, f"duplicate repository pull request: {pr}")
        pull_requests.add(pr)
        require_text(event.get("repository"), f"{prefix}.repository")
        require_text(event.get("title"), f"{prefix}.title")
        require_sha(event.get("source_head"), f"{prefix}.source_head")
        require_sha(event.get("merge_commit"), f"{prefix}.merge_commit")
        for field in ("qualification", "evidence", "claim_boundary"):
            require_text(event.get(field), f"{prefix}.{field}")
        if "ci_run_id" in event:
            require_positive_int(event.get("ci_run_id"), f"{prefix}.ci_run_id")
        by_id[event_id] = event
    require(REQUIRED_REPOSITORY_EVENTS.issubset(by_id), "repository event log is missing required historical events")
    return by_id


def validate_active_work(repository_events: dict[str, dict[str, Any]]) -> None:
    active = load_json(ROOT / "active-work.json")
    require(active.get("schema_version") == "project.active-work.v3", "active-work schema is invalid")
    require_text(active.get("project"), "active-work.project")
    require_text(active.get("updated_on"), "active-work.updated_on")
    reject_live_keys(active)

    model = require_object(active.get("state_model"), "active-work.state_model")
    require(model.get("durable_event_log") == ".project/repository-events.jsonl", "active-work durable event log is invalid")
    require(model.get("live_repository_state_policy") == "query_live_github_never_persist_as_current_truth", "active-work live-state policy is invalid")
    require(set(require_list(model.get("forbidden_live_fields"), "active-work.state_model.forbidden_live_fields")) == FORBIDDEN_LIVE_KEYS, "active-work forbidden live fields differ from validator")
    distinctions = set(require_list(model.get("canonical_distinctions"), "active-work.state_model.canonical_distinctions"))
    require("merged_state != authorized_state_transition" in distinctions, "merge-versus-authority distinction is missing")

    for key, commit_field in (("last_substantive_baseline", "commit"), ("latest_promoted_repository_event", "merge_commit")):
        selected = require_object(active.get(key), f"active-work.{key}")
        event_id = require_text(selected.get("event_id"), f"active-work.{key}.event_id")
        require(event_id in repository_events, f"active-work.{key} references an unknown event")
        event = repository_events[event_id]
        require(event["pull_request"] == require_positive_int(selected.get("pull_request"), f"active-work.{key}.pull_request"), f"active-work.{key} pull request mismatch")
        require(event["merge_commit"] == require_sha(selected.get(commit_field), f"active-work.{key}.{commit_field}"), f"active-work.{key} commit mismatch")

    architecture = require_object(active.get("architecture_baseline"), "active-work.architecture_baseline")
    require(architecture.get("strategy") == "independent_servicetracer_demo_api_subproject", "active strategy is invalid")
    require(architecture.get("planning_boundary") == "dual_subscription_repository_design", "dual-subscription boundary is missing")
    require(architecture.get("authorization_status") == "human_ratification_required", "architecture must remain at human ratification")
    require(architecture.get("repository_default_location") == "eastus", "merged eastus default is not recorded")
    require(architecture.get("initial_requested_location") == "westus2", "original westus2 request is not recorded")
    require(architecture.get("github_environment_name") == "azure-api-payg", "planner environment name mismatch")
    for field in (
        "application_architecture_merge",
        "application_architecture_source_head",
        "dual_subscription_source_head",
        "stack_merge_commit",
        "main_merge_commit",
        "evidence_merge_commit",
    ):
        require_sha(architecture.get(field), f"active-work.architecture_baseline.{field}")
    for field in ("application_architecture_ci_run_id", "dual_subscription_ci_run_id", "stack_merge_ci_run_id"):
        require_positive_int(architecture.get(field), f"active-work.architecture_baseline.{field}")

    capabilities = require_object(active.get("repository_capabilities"), "active-work.repository_capabilities")
    for field in (
        "independent_demo_api_subproject_present",
        "independent_demo_api_read_only_planner_present",
        "independent_demo_api_fail_closed_what_if_classifier_present",
        "independent_demo_api_bicep_root_present",
        "dual_subscription_planning_contract_present",
        "provider_no_rbac_validation_present",
        "planner_credential_generation_absent",
    ):
        require(capabilities.get(field) is True, f"repository capability {field} must be true")
    require(capabilities.get("independent_demo_api_deploy_workflow_present") is False, "independent deploy workflow must remain absent")
    require(capabilities.get("demo_backend_api_workflow_present_in_repository") is False, "legacy demo workflow must remain retired")

    grants = require_list(active.get("bounded_authority_grants"), "active-work.bounded_authority_grants")
    require(len(grants) == 1, "exactly one durable bounded grant is expected")
    grant = require_object(grants[0], "active-work.bounded_authority_grants[0]")
    require(grant.get("operation") == "read_only_azure_planning", "durable grant operation is invalid")
    require(grant.get("azure_mutations_authorized") is False, "durable grant must not authorize Azure mutation")
    require("does not authorize the independent demo API planner" in require_text(grant.get("claim_boundary"), "active-work.bounded_authority_grants[0].claim_boundary"), "publication grant must explicitly exclude the independent planner")

    defaults = require_object(active.get("authority_defaults"), "active-work.authority_defaults")
    for field in FALSE_AUTHORITY_FIELDS:
        require(defaults.get(field) is False, f"authority default {field} must be false")

    deployment = require_object(active.get("deployment_state"), "active-work.deployment_state")
    collector = require_object(deployment.get("collector_hosted_demo_api"), "active-work.deployment_state.collector_hosted_demo_api")
    require(collector.get("last_observed_run_id") == 30053018998, "latest authenticated collector evidence must be run 30053018998")
    require(collector.get("latest_read_only_what_if_rejected") is True, "latest collector What-If rejection is not recorded")
    require(collector.get("deployment_succeeded") is False, "collector deployment must not be promoted to success")
    for field in ("deployed", "tls_verified", "health_verified", "transactions_verified", "cors_verified", "frontend_live_verified"):
        require(collector.get(field) is False, f"collector state {field} must remain false")

    independent = require_object(deployment.get("independent_demo_api"), "active-work.deployment_state.independent_demo_api")
    require(independent.get("repository_implemented") is True, "independent implementation must remain recorded")
    require(independent.get("planner_present") is True, "independent planner must remain recorded")
    for field in FALSE_INDEPENDENT_STATE_FIELDS:
        require(independent.get(field) is False, f"independent state {field} must remain false")
    require(independent.get("Azure_state") == "not_observed", "independent Azure state must remain not_observed")
    require(deployment.get("operationally_verified") is False, "project must not claim operational verification")

    latest = require_object(active.get("latest_promoted_evidence"), "active-work.latest_promoted_evidence")
    require(latest.get("event_id") == "collector-demo-api-what-if-30053018998", "latest evidence event mismatch")
    require(latest.get("run_id") == 30053018998, "latest evidence run mismatch")
    require_digest(latest.get("artifact_sha256"), "active-work.latest_promoted_evidence.artifact_sha256")
    require(latest.get("azure_mutations_authorized") is False, "latest read-only evidence must not authorize mutation")
    require(latest.get("azure_mutations_performed") is False, "latest read-only evidence must record zero mutation")
    require(latest.get("deployment_authorized") is False, "latest evidence must not authorize deployment")

    configuration = require_object(active.get("configuration_state"), "active-work.configuration_state")
    require(configuration.get("committed_live_report_url_present") is False, "unverified report URL must not be committed")
    require(configuration.get("committed_live_demo_api_url_present") is False, "unverified API URL must not be committed")

    gate = require_object(active.get("safe_next_gate"), "active-work.safe_next_gate")
    require(gate.get("operation") == "ratify_or_reject_dual_subscription_planner_architecture", "safe next gate must remain architecture ratification")
    for field in ("workflow_dispatch_authorized", "Azure_authentication_authorized", "Azure_mutations_authorized", "deployment_authorized", "cleanup_authorized"):
        require(gate.get(field) is False, f"safe-next-gate field {field} must be false")


def validate_environment_state() -> int:
    document = load_json(ROOT / "environment-state.json")
    require(document.get("schema_version") == "project.environment-state.v1", "environment-state schema is invalid")
    facts = require_list(document.get("facts"), "environment-state.facts")
    by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(facts):
        fact = require_object(raw, f"environment-state.facts[{index}]")
        fact_id = require_text(fact.get("fact_id"), f"environment-state.facts[{index}].fact_id")
        require(fact_id not in by_id, f"duplicate environment fact_id: {fact_id}")
        for field in ("value", "status", "last_observed_on", "source", "notes"):
            require_text(fact.get(field), f"environment-state.facts[{index}].{field}")
        by_id[fact_id] = fact
    require(REQUIRED_FACTS.issubset(by_id), "environment-state is missing required independent-planner facts")
    require(by_id["independent-demo-api-planning-authorization"]["status"] == "human_ratification_required_fail_closed", "planning authorization must remain fail closed")
    require(by_id["independent-demo-api-target-subscription"]["status"] == "not_observed_and_not_authorized", "target subscription must remain unselected")
    require(by_id["independent-demo-api-default-location"]["status"] == "repository_configuration_conflict_human_resolution_required", "location conflict must remain explicit")
    return len(facts)


def validate_deployment_history() -> int:
    events = load_jsonl(ROOT / "deployment-history.jsonl", "deployment-history")
    ids: set[str] = set()
    for index, event in enumerate(events, 1):
        prefix = f"deployment-history[{index}]"
        event_id = require_text(event.get("event_id"), f"{prefix}.event_id")
        require(event_id not in ids, f"duplicate deployment event_id: {event_id}")
        ids.add(event_id)
        for field in ("event_type", "component", "status", "evidence", "notes"):
            require_text(event.get(field), f"{prefix}.{field}")
        for field in ("workflow_run_id", "run_attempt", "artifact_id"):
            if field in event:
                require_positive_int(event.get(field), f"{prefix}.{field}")
        if "repository_commit" in event:
            require_sha(event.get("repository_commit"), f"{prefix}.repository_commit")
        if "artifact_sha256" in event:
            require_digest(event.get("artifact_sha256"), f"{prefix}.artifact_sha256")
    require(REQUIRED_DEPLOYMENT_EVENTS.issubset(ids), "deployment history is missing required Azure evidence events")
    return len(events)


def validate_workstreams() -> int:
    document = load_json(ROOT / "workstream-catalog.json")
    require(document.get("schema_version") == "project.workstream-catalog.v1", "workstream catalog schema is invalid")
    workstreams = require_list(document.get("workstreams"), "workstream-catalog.workstreams")
    ids = {
        require_text(require_object(item, "workstream").get("workstream_id"), "workstream.workstream_id")
        for item in workstreams
    }
    require(ids == CANONICAL_WORKSTREAMS, "workstream catalog must contain exactly the six canonical workstreams")
    return len(workstreams)


def validate_frontend_configuration() -> None:
    source = load_json(REPOSITORY_ROOT / "docs" / "report-source.json")
    require(source.get("schema_version") == "servicetracer.report-source.v1", "report-source schema is invalid")
    require(source.get("live_report_url") == "", "unverified report URL must remain blank")
    require(source.get("live_demo_api_url") == "", "unverified demo API URL must remain blank")
    require_text(source.get("fallback_report_url"), "report-source.fallback_report_url")


def validate_planner_contract() -> None:
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-plan.yml").read_text(encoding="utf-8")
    runbook = (REPOSITORY_ROOT / "docs" / "runbooks" / "servicetracer-demo-api-payg-subscription-boundary.md").read_text(encoding="utf-8")
    require("environment: azure-api-payg" in workflow, "planner must use azure-api-payg")
    require(workflow.count("uses: azure/login@v2") == 2, "planner must retain two distinct Azure logins")
    require(workflow.count("--validation-level ProviderNoRbac") == 2, "planner must use ProviderNoRbac twice")
    require("credential_creation_authorized:false" in workflow, "planner must record credential creation as unauthorized")
    require("ssh-keygen" not in workflow, "planner must not generate a credential")
    require("az deployment sub create" not in workflow, "planner must not deploy")
    require("az role assignment create" not in workflow, "planner must not mutate RBAC")
    require("does not create GitHub environments" in runbook, "runbook must preserve the environment-setup boundary")
    require("does not create Azure role assignments" in runbook, "runbook must preserve the RBAC boundary")


def validate_documents() -> None:
    handoff = (ROOT / "handoffs" / "current-state.md").read_text(encoding="utf-8")
    implementation = (REPOSITORY_ROOT / "docs" / "implementation-status.md").read_text(encoding="utf-8")
    overview = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    helix = load_json(REPOSITORY_ROOT / ".helix" / "repository-context.json")
    for marker in (
        "323b3892c6efd598231037f23281d49608ceb570",
        "PR #71",
        "dd9b33b6d849b0e3635b148159d7f484744ee77a",
        "dual-subscription",
        "Human ratification",
        "30053018998",
        "azure-api-payg",
        "eastus",
        "westus2",
    ):
        require(marker in handoff, f"current handoff is missing marker: {marker}")
    require("independent" in implementation.lower(), "implementation status must describe the independent architecture")
    require("PR #41 is a draft" not in implementation, "implementation status retains superseded PR #41 state")
    require("empty VPN backend pool" not in overview, "README retains a superseded empty-backend claim")
    require(helix.get("classified_on") == "2026-07-23", ".helix classification changed unexpectedly")


def write_log(message: str) -> None:
    try:
        TEST_LOG.write_text(message.rstrip() + "\n", encoding="utf-8")
    except OSError:
        pass


def main() -> int:
    stage = "startup"
    try:
        stage = "repository-events"
        repository_events = validate_repository_events()
        stage = "active-work"
        validate_active_work(repository_events)
        stage = "environment-state"
        fact_count = validate_environment_state()
        stage = "deployment-history"
        deployment_count = validate_deployment_history()
        stage = "workstream-catalog"
        workstream_count = validate_workstreams()
        stage = "frontend-configuration"
        validate_frontend_configuration()
        stage = "planner-contract"
        validate_planner_contract()
        stage = "current-documents"
        validate_documents()
        stage = "required-documents"
        for path in (ROOT / "README.md", ROOT / "decisions.md", ROOT / "handoffs" / "current-state.md"):
            require(path.is_file() and bool(path.read_text(encoding="utf-8").strip()), f"missing or empty required document: {path}")
    except (ValidationError, OSError) as exc:
        message = f"workflow-observability validation failed at {stage}: {exc}"
        print(message, file=sys.stderr)
        write_log(message)
        return 1

    message = (
        "workflow-observability validation passed: "
        f"{len(repository_events)} repository event(s), "
        f"{workstream_count} canonical workstream(s), "
        f"{fact_count} environment fact(s), "
        f"{deployment_count} deployment event(s)"
    )
    print(message)
    write_log(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
