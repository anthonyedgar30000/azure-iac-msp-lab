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
    "independent-demo-api-plan-30064289707-attempt-1",
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
    "independent-demo-api-plan-run-30064289707",
    "independent-demo-api-target-readiness",
    "independent-demo-api-target-resource-group-state",
    "independent-demo-api-provider-registration",
}
CANONICAL_WORKSTREAMS = {
    "architecture-and-design-decisions",
    "azure-resource-plan-and-iac",
    "deployment-evidence-and-screenshots",
    "cost-health-and-configuration-telemetry",
    "servicetracer-findings-and-reports",
    "portfolio-and-demo-narrative",
}
FALSE_OPERATIONAL_AUTHORITY_FIELDS = {
    "workflow_dispatch_authorized",
    "azure_authentication_authorized",
    "azure_mutations_authorized",
    "guest_command_authorized",
    "cleanup_authorized",
    "github_environment_mutation_authorized",
    "github_secret_mutation_authorized",
    "entra_identity_mutation_authorized",
    "azure_rbac_mutation_authorized",
}
TRUE_INDEPENDENT_FIELDS = {
    "repository_implemented",
    "planner_present",
    "planner_dispatched",
    "architecture_ratified",
    "target_subscription_selected",
    "github_environment_configured",
    "dependency_identity_configured",
    "target_identity_configured",
    "required_read_only_rbac_configured",
    "azure_authentication_succeeded",
    "dependency_endpoint_observed",
    "target_compute_provider_registered",
    "target_network_provider_registered",
}
FALSE_INDEPENDENT_FIELDS = {
    "requested_sku_unrestricted",
    "target_resource_group_observed",
    "arm_validation_performed",
    "what_if_performed",
    "plan_accepted",
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


def require_nonnegative_int(value: Any, field: str) -> int:
    require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{field} must be a nonnegative integer")
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
    for marker in (
        "readiness_rejected != workflow_mechanism_failed",
        "planner_dispatched != ARM_WhatIf_completed",
        "not_observed != false",
    ):
        require(marker in distinctions, f"canonical distinction is missing: {marker}")

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
    require(architecture.get("authorization_status") == "ratified_for_bounded_read_only_planning", "architecture ratification resolution is missing")
    require(architecture.get("state") == "architecture_ratified_readiness_rejected_before_arm_validation_and_what_if", "architecture state mismatch")
    require(architecture.get("repository_default_location") == "eastus", "authorized eastus run is not recorded")
    require(architecture.get("github_environment_name") == "azure-api-payg", "planner environment name mismatch")
    for field in (
        "application_architecture_merge",
        "application_architecture_source_head",
        "dual_subscription_source_head",
        "stack_merge_commit",
        "main_merge_commit",
        "evidence_merge_commit",
        "typed_readiness_source_head",
        "typed_readiness_merge_commit",
        "authorization_reconciliation_merge_commit",
    ):
        require_sha(architecture.get(field), f"active-work.architecture_baseline.{field}")
    for field in (
        "application_architecture_ci_run_id",
        "dual_subscription_ci_run_id",
        "stack_merge_ci_run_id",
        "typed_readiness_ci_run_id",
    ):
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
        "typed_target_readiness_assessor_present",
        "target_observation_failure_preserved",
    ):
        require(capabilities.get(field) is True, f"repository capability {field} must be true")
    require(capabilities.get("independent_demo_api_deploy_workflow_present") is False, "independent deploy workflow must remain absent")

    defaults = require_object(active.get("authority_defaults"), "active-work.authority_defaults")
    for field in FALSE_OPERATIONAL_AUTHORITY_FIELDS:
        require(defaults.get(field) is False, f"authority default {field} must be false")
    require(defaults.get("architecture_ratification_complete") is True, "architecture ratification must be recorded")
    require(defaults.get("consumed_planner_authorization_active") is False, "consumed authorization must not remain active")

    deployment = require_object(active.get("deployment_state"), "active-work.deployment_state")
    independent = require_object(deployment.get("independent_demo_api"), "active-work.deployment_state.independent_demo_api")
    for field in TRUE_INDEPENDENT_FIELDS:
        require(independent.get(field) is True, f"independent state {field} must be true")
    for field in FALSE_INDEPENDENT_FIELDS:
        require(independent.get(field) is False, f"independent state {field} must be false")
    require(independent.get("last_planner_run_id") == 30064289707, "independent planner run mismatch")
    require(independent.get("last_planner_run_attempt") == 1, "independent planner attempt mismatch")
    require_sha(independent.get("dispatch_sha"), "active-work.deployment_state.independent_demo_api.dispatch_sha")
    require(independent.get("requested_location") == "eastus", "requested location mismatch")
    require(independent.get("requested_vm_size") == "Standard_B2ats_v2", "requested VM size mismatch")
    require(independent.get("requested_sku_restriction_reason") == "NotAvailableForSubscription", "SKU restriction mismatch")
    require(independent.get("target_vm_family") == "standardBasv2Family", "VM family mismatch")
    for field, expected in (
        ("target_total_regional_vcpu_current", 0),
        ("target_total_regional_vcpu_limit", 10),
        ("target_vm_family_vcpu_current", 0),
        ("target_vm_family_vcpu_limit", 0),
        ("target_standard_ipv4_public_ip_current", 0),
        ("target_standard_ipv4_public_ip_limit", 20),
    ):
        require(require_nonnegative_int(independent.get(field), f"independent.{field}") == expected, f"independent {field} mismatch")
    require(independent.get("Azure_state") == "readiness_observed_target_inventory_not_observed_ARM_what_if_not_performed", "independent Azure state mismatch")
    require(deployment.get("operationally_verified") is False, "project must not claim operational verification")

    latest = require_object(active.get("latest_promoted_evidence"), "active-work.latest_promoted_evidence")
    require(latest.get("event_id") == "independent-demo-api-plan-30064289707-attempt-1", "latest evidence event mismatch")
    require(latest.get("run_id") == 30064289707, "latest evidence run mismatch")
    require(latest.get("run_attempt") == 1, "latest evidence attempt mismatch")
    require(latest.get("artifact_id") == 8585693830, "latest evidence artifact mismatch")
    require_digest(latest.get("artifact_sha256"), "active-work.latest_promoted_evidence.artifact_sha256")
    require(latest.get("azure_authentication_performed") is True, "latest evidence must record Azure authentication")
    for field in ("azure_mutations_authorized", "azure_mutations_performed", "arm_validation_performed", "what_if_performed", "deployment_authorized"):
        require(latest.get(field) is False, f"latest evidence field {field} must remain false")

    configuration = require_object(active.get("configuration_state"), "active-work.configuration_state")
    require(configuration.get("committed_live_report_url_present") is False, "unverified report URL must not be committed")
    require(configuration.get("committed_live_demo_api_url_present") is False, "unverified API URL must not be committed")

    gate = require_object(active.get("safe_next_gate"), "active-work.safe_next_gate")
    require(gate.get("operation") == "select_candidate_and_authorize_fresh_read_only_planner", "safe next gate mismatch")
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
    require(REQUIRED_FACTS.issubset(by_id), "environment-state is missing required facts")
    require(by_id["independent-demo-api-planning-authorization"]["status"] == "consumed_no_new_dispatch_authority", "planner authorization status mismatch")
    require(by_id["independent-demo-api-target-subscription"]["status"] == "selected_enabled_identity_redacted", "target subscription observation mismatch")
    require(by_id["independent-demo-api-default-location"]["status"] == "resolved_for_run_30064289707_new_run_requires_fresh_choice", "location resolution mismatch")
    require(by_id["independent-demo-api-plan-run-30064289707"]["status"] == "completed_readiness_rejected_safely", "planner run fact mismatch")
    require(by_id["independent-demo-api-target-resource-group-state"]["status"] == "not_observed", "target resource group must remain not_observed")
    return len(facts)


def validate_deployment_history() -> int:
    events = load_jsonl(ROOT / "deployment-history.jsonl", "deployment-history")
    ids: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for index, event in enumerate(events, 1):
        prefix = f"deployment-history[{index}]"
        event_id = require_text(event.get("event_id"), f"{prefix}.event_id")
        require(event_id not in ids, f"duplicate deployment event_id: {event_id}")
        ids.add(event_id)
        by_id[event_id] = event
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
    plan = by_id["independent-demo-api-plan-30064289707-attempt-1"]
    require(plan.get("workflow_run_id") == 30064289707, "independent planner history run mismatch")
    require(plan.get("artifact_id") == 8585693830, "independent planner history artifact mismatch")
    require(plan.get("azure_authentication_performed") is True, "independent planner must record authentication")
    for field in ("azure_mutations_authorized", "azure_mutations_performed", "arm_validation_performed", "what_if_performed", "deployment_authorized"):
        require(plan.get(field) is False, f"independent planner history {field} must remain false")
    require(plan.get("target_resource_group_state") == "not_observed", "target resource group history must remain not_observed")
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
    assessor = (REPOSITORY_ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "assess_target_readiness.py").read_text(encoding="utf-8")
    runbook = (REPOSITORY_ROOT / "docs" / "runbooks" / "servicetracer-demo-api-payg-subscription-boundary.md").read_text(encoding="utf-8")
    require("environment: azure-api-payg" in workflow, "planner must use azure-api-payg")
    require(workflow.count("uses: azure/login@v2") == 2, "planner must retain two Azure logins")
    require(workflow.count("--validation-level ProviderNoRbac") == 2, "planner must use ProviderNoRbac twice")
    require("credential_creation_authorized:false" in workflow, "planner must record credential creation as unauthorized")
    require("ssh-keygen" not in workflow, "planner must not generate a credential")
    require("az deployment sub create" not in workflow, "planner must not deploy")
    require("az role assignment create" not in workflow, "planner must not mutate RBAC")
    for marker in (
        "assess_target_readiness.py",
        "target-readiness-assessment.json",
        "ResourceGroupNotFound",
        'status:"observation_failed"',
        'status:"not_observed"',
    ):
        require(marker in workflow, f"planner is missing typed observation marker: {marker}")
    require("ready_for_arm_what_if" in assessor, "readiness assessor must emit ready status")
    require("target_resource_group_observation_failed" in assessor, "readiness assessor must block failed target observation")
    require("does not create GitHub environments" in runbook, "runbook must preserve environment setup boundary")
    require("does not create Azure role assignments" in runbook, "runbook must preserve RBAC boundary")


def validate_documents() -> None:
    handoff = (ROOT / "handoffs" / "current-state.md").read_text(encoding="utf-8")
    implementation = (REPOSITORY_ROOT / "docs" / "implementation-status.md").read_text(encoding="utf-8")
    overview = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    helix = load_json(REPOSITORY_ROOT / ".helix" / "repository-context.json")
    for marker in (
        "92b0c3b1064158684a4b280348c77eeedba6dfc3",
        "30064289707",
        "8585693830",
        "7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22",
        "NotAvailableForSubscription",
        "standardBasv2Family",
        "not_observed != false",
        "PR #73",
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
