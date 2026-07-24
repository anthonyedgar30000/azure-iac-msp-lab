#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / ".project"
EVIDENCE_PATH = PROJECT / "evidence" / "servicetracer-demo-api-live-verification-30086152352.json"
HANDOFF_PATH = PROJECT / "handoffs" / "servicetracer-demo-api-live-current-state.md"
HISTORY_PATH = PROJECT / "deployment-history.jsonl"
ACTIVE_PATH = PROJECT / "active-work.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "servicetracer-demo-api-live-verify.yml"

SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
EVENT_ID = "independent-demo-api-live-verification-30086152352-attempt-1"


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain an object")
    return value


def load_history(path: Path) -> dict[str, dict[str, Any]]:
    events: dict[str, dict[str, Any]] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        event = json.loads(line)
        require(isinstance(event, dict), f"deployment history line {number} must be an object")
        event_id = event.get("event_id")
        require(isinstance(event_id, str) and event_id, f"deployment history line {number} lacks event_id")
        require(event_id not in events, f"duplicate deployment event: {event_id}")
        events[event_id] = event
    return events


def require_sha(value: Any, field: str) -> str:
    require(isinstance(value, str) and bool(SHA.fullmatch(value)), f"{field} must be a 40-character SHA")
    return value


def require_digest(value: Any, field: str) -> str:
    require(isinstance(value, str) and bool(DIGEST.fullmatch(value.removeprefix("sha256:"))), f"{field} must be SHA-256")
    return value


def main() -> int:
    evidence = load_json(EVIDENCE_PATH)
    active = load_json(ACTIVE_PATH)
    history = load_history(HISTORY_PATH)
    handoff = HANDOFF_PATH.read_text(encoding="utf-8")
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    require(
        evidence.get("schema_version") == "project.servicetracer-demo-api-live-verification.v1",
        "live evidence schema mismatch",
    )

    repository = evidence["repository_evidence"]
    require(repository["pull_request"] == 80, "PR anchor mismatch")
    require_sha(repository["base_main"], "repository.base_main")
    require_sha(repository["source_head"], "repository.source_head")
    require_sha(repository["tested_pull_request_merge_sha"], "repository.tested_pull_request_merge_sha")
    require_sha(repository["final_merge_commit"], "repository.final_merge_commit")
    require(repository["source_head"] == "9212437bf2155434c035b50a8d32b39fcc046182", "source head mismatch")
    require(repository["final_merge_commit"] == "76279db80458b098b063e428bc7dabf9c1f9edce", "final merge mismatch")
    comparison = repository["tested_tree_vs_final_merge"]
    require(comparison["changed_file_count"] == 0, "tested and final merge trees differ")
    require(comparison["file_content_difference_observed"] is False, "file difference was incorrectly promoted")
    require(repository["final_merge_commit_ci_observed"] is False, "final merge CI was incorrectly claimed")
    runs = {item["run_id"]: item["conclusion"] for item in repository["exact_source_head_ci"]}
    require(runs == {30086152352: "success", 30086152445: "success"}, "exact source-head CI mismatch")

    artifact = evidence["artifact"]
    require(artifact["workflow_run_id"] == 30086152352, "artifact run mismatch")
    require(artifact["run_attempt"] == 1, "artifact attempt mismatch")
    require(artifact["artifact_id"] == 8593782051, "artifact ID mismatch")
    require_digest(artifact["artifact_sha256"], "artifact.artifact_sha256")
    require(
        artifact["artifact_sha256"] == "2bd876dfd7e707994218ea347887816df03cff03ba5cb45b60e96cf082c83ad7",
        "artifact digest mismatch",
    )
    require(artifact["expired_when_promoted"] is False, "artifact was incorrectly marked expired")
    require(len(artifact["manifest_entries"]) == 9, "manifest entry count mismatch")
    for name, digest in artifact["manifest_entries"].items():
        require(isinstance(name, str) and name, "manifest filename is invalid")
        require_digest(digest, f"manifest.{name}")

    runtime = evidence["public_runtime_observation"]
    require(runtime["base_url"] == "https://st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com", "base URL mismatch")
    require(runtime["allowed_origin"] == "https://anthonyedgar30000.github.io", "allowed origin mismatch")
    require(runtime["public_endpoint_reachable"] is True, "public endpoint was not promoted")
    require(runtime["tls_verified"] is True, "TLS was not promoted")
    require(runtime["health"] == {
        "http_status": 200,
        "schema_version": "servicetracer.demo-api-health.v1",
        "status": "healthy",
        "backend_target_configured": True,
        "hosting_model": "dedicated_vm_subproject",
    }, "health contract mismatch")
    require(runtime["cors"]["preflight_http_status"] == 204, "CORS status mismatch")
    require(runtime["cors"]["allow_origin_exact_match"] is True, "CORS origin mismatch")
    require(runtime["cors"]["allow_methods"] == ["POST", "OPTIONS"], "CORS methods mismatch")

    transaction = runtime["transaction_protocol"]
    require(transaction["request_http_status"] == 200, "transaction HTTP status mismatch")
    require(transaction["attempts"] == 2, "attempt count mismatch")
    require(transaction["successful_attempts"] == 0, "successful attempts were incorrectly promoted")
    require(transaction["failed_attempts"] == 2, "failed attempt count mismatch")
    require(transaction["observed_backends"] == ["VPN-02"], "observed backend mismatch")
    require(transaction["backend_attempt_counts"] == {"VPN-01": 0, "VPN-02": 2}, "backend attempt counts mismatch")
    require(transaction["backend_http_statuses"] == [503, 503], "backend HTTP statuses mismatch")
    require(transaction["failure_boundaries"] == ["radius_response", "radius_response"], "failure boundaries mismatch")
    require(transaction["probe_gap_detected"] is True, "probe gap was lost")
    require(transaction["exact_root_cause_claimed"] is False, "root cause was overclaimed")
    require(transaction["backend_specific_localization_stable"] is False, "backend localization was overclaimed")

    typed = evidence["typed_verification"]
    for field in ("public_api_operationally_verified", "health_contract_verified", "cors_verified", "transaction_protocol_verified"):
        require(typed[field] is True, f"typed verification {field} must be true")
    for field in ("backend_transaction_success_verified", "full_workload_operationally_verified", "frontend_integration_verified"):
        require(typed[field] is False, f"typed verification {field} must be false")

    control = evidence["azure_control_plane_provenance"]
    for field, value in control.items():
        if field == "state":
            require(value == "not_observed", "control-plane state must be not_observed")
        else:
            require(value is False, f"control-plane field {field} must remain false")

    authority = evidence["mutation_and_authority"]
    require(authority["repository_evidence_promotion_authorized"] is True, "repository promotion authority missing")
    require(authority["pull_request_creation_authorized"] is True, "PR authority missing")
    for field in (
        "verification_azure_mutations_performed",
        "pull_request_merge_authorized",
        "azure_authentication_authorized",
        "azure_mutations_authorized",
        "deployment_authorized",
        "cleanup_authorized",
    ):
        require(authority[field] is False, f"authority field {field} must remain false")

    integration = evidence["shared_state_integration"]
    require(integration["active_work_modified"] is False, "active-work must remain isolated")
    require(integration["environment_state_modified"] is False, "environment state must remain isolated")
    require(integration["primary_handoff_modified"] is False, "primary handoff must remain isolated")
    require(integration["deployment_history_appended"] is True, "deployment history must be appended")

    event = history.get(EVENT_ID)
    require(event is not None, "deployment history lacks live verification event")
    require(event["workflow_run_id"] == 30086152352, "history run mismatch")
    require(event["artifact_id"] == 8593782051, "history artifact mismatch")
    require_digest(event["artifact_sha256"], "history artifact digest")
    require(event["public_endpoint_reachable"] is True, "history lost endpoint observation")
    require(event["transaction_protocol_verified"] is True, "history lost transaction verification")
    require(event["backend_transaction_success_verified"] is False, "history overclaimed backend success")
    require(event["deployment_provenance_state"] == "not_observed", "history overclaimed deployment provenance")
    require(event["azure_authentication_performed"] is False, "history incorrectly claims Azure login")
    require(event["azure_mutations_performed"] is False, "history incorrectly claims Azure mutation")

    independent = active["deployment_state"]["independent_demo_api"]
    for field in ("deployed", "tls_verified", "health_verified", "transactions_verified", "cors_verified", "frontend_live_verified"):
        require(independent[field] is False, f"shared planner state {field} was overwritten")
    require(active["deployment_state"]["operationally_verified"] is False, "shared state overclaimed full operation")

    for marker in (
        "30086152352",
        "8593782051",
        "2bd876dfd7e707994218ea347887816df03cff03ba5cb45b60e96cf082c83ad7",
        "public_API_operationally_verified = true",
        "backend_transaction_success_verified = false",
        "full_workload_operationally_verified = false",
        "hosting subscription = not_observed",
        "not_observed != absent",
    ):
        require(marker in handoff, f"dedicated handoff lacks marker: {marker}")

    require("uses: azure/login" not in workflow, "live verification workflow must not log into Azure")
    require("\naz " not in workflow, "live verification workflow must not invoke Azure CLI")
    require("azd " not in workflow, "live verification workflow must not invoke azd")
    require("permissions:\n  contents: read" in workflow, "live verification workflow permissions widened")

    print("ServiceTracer demo API live-evidence promotion validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
