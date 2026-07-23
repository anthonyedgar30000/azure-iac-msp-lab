from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

CONTROL_MESSAGES = {
    "proceed",
    "fix",
    "sync_with_reality",
    "restrategize",
    "verify",
    "rollback",
    "escalate",
    "complete",
}

TERMINAL_PHASES = {"completed", "escalated"}

STALE_OR_UNCERTAIN_BLOCKERS = {
    "public_ip_quota_not_observable",
    "collector_private_ip_drift",
    "collector_vm_not_succeeded",
    "collector_vm_power_state_unexpected",
    "collector_nic_primary_configuration_ambiguous",
    "collector_module_parameters_missing",
}
STRATEGY_BLOCKERS = {
    "public_ip_quota_insufficient",
}
BOUNDARY_BLOCKERS = {
    "resource_group_read_only_lock_present",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _require_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid JSON {path}: {exc}") from exc


def new_state(
    *,
    objective: str,
    success_criteria: list[str],
    authorized_scope: list[str],
    retry_budget: int,
    strategy: str,
    reality_watermark: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not objective.strip():
        raise ValueError("objective must not be empty")
    if not success_criteria or not all(isinstance(item, str) and item.strip() for item in success_criteria):
        raise ValueError("success_criteria must contain at least one non-empty string")
    if not authorized_scope or not all(isinstance(item, str) and item.strip() for item in authorized_scope):
        raise ValueError("authorized_scope must contain at least one non-empty string")
    if isinstance(retry_budget, bool) or not isinstance(retry_budget, int) or retry_budget < 0:
        raise ValueError("retry_budget must be a non-negative integer")
    if not strategy.strip():
        raise ValueError("strategy must not be empty")

    return {
        "schema_version": "servicetracer.governed-persistence-state.v1",
        "objective": objective,
        "success_criteria": list(success_criteria),
        "authorized_scope": list(authorized_scope),
        "strategy": strategy,
        "strategy_revision": 0,
        "phase": "planned",
        "attempt_number": 0,
        "retry_budget": retry_budget,
        "observed_result": None,
        "failure_class": None,
        "evidence": [],
        "reality_watermark": reality_watermark or {},
        "success_criteria_verified": False,
        "rollback_authorized": False,
        "next_control_message": "proceed",
        "authority": {
            "scope_expansion_authorized": False,
            "objective_change_authorized": False,
            "azure_mutation_authorized": False,
            "automatic_execution_authorized": False,
        },
        "history": [],
        "updated_at": _utc_now(),
    }


def apply_control_message(
    state: dict[str, Any],
    message: str,
    *,
    observation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if message not in CONTROL_MESSAGES:
        raise ValueError(f"unsupported control message: {message}")

    current = deepcopy(state)
    phase = str(current.get("phase") or "")
    if phase in TERMINAL_PHASES:
        raise ValueError(f"cannot apply {message} to terminal phase {phase}")

    observation = observation or {}
    evidence = observation.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("observation.evidence must be an array")

    before_scope = deepcopy(current.get("authorized_scope"))
    before_objective = current.get("objective")
    before_authority = deepcopy(current.get("authority"))
    attempt_number = current.get("attempt_number")
    retry_budget = current.get("retry_budget")
    if isinstance(attempt_number, bool) or not isinstance(attempt_number, int) or attempt_number < 0:
        raise ValueError("state.attempt_number must be a non-negative integer")
    if isinstance(retry_budget, bool) or not isinstance(retry_budget, int) or retry_budget < 0:
        raise ValueError("state.retry_budget must be a non-negative integer")

    failure_class = observation.get("failure_class")
    observed_result = observation.get("observed_result")
    verified = observation.get("success_criteria_verified", False)
    _require_bool(verified, "observation.success_criteria_verified")

    next_message: str | None
    if message == "proceed":
        if phase not in {"planned", "awaiting_human", "blocked"}:
            raise ValueError(f"proceed is not valid from phase {phase}")
        current["phase"] = "acting"
        current["attempt_number"] = attempt_number + 1
        next_message = "verify"
    elif message == "fix":
        if failure_class != "recoverable_failure":
            raise ValueError("fix requires failure_class=recoverable_failure")
        if attempt_number >= retry_budget + 1:
            raise ValueError("retry budget exhausted")
        current["phase"] = "acting"
        current["attempt_number"] = attempt_number + 1
        next_message = "verify"
    elif message == "sync_with_reality":
        current["phase"] = "synchronizing"
        watermark = observation.get("reality_watermark")
        if not isinstance(watermark, dict) or not watermark:
            raise ValueError("sync_with_reality requires a non-empty reality_watermark")
        current["reality_watermark"] = watermark
        next_message = "restrategize" if failure_class == "strategy_failure" else "verify"
    elif message == "restrategize":
        strategy = observation.get("strategy")
        if not isinstance(strategy, str) or not strategy.strip():
            raise ValueError("restrategize requires a replacement strategy")
        current["phase"] = "planned"
        current["strategy"] = strategy
        current["strategy_revision"] = int(current.get("strategy_revision", 0)) + 1
        next_message = "proceed"
    elif message == "verify":
        current["phase"] = "verifying"
        current["success_criteria_verified"] = verified
        next_message = "complete" if verified else "fix"
    elif message == "rollback":
        if current.get("rollback_authorized") is not True:
            raise ValueError("rollback is not authorized")
        current["phase"] = "rolling_back"
        next_message = "verify"
    elif message == "escalate":
        current["phase"] = "escalated"
        next_message = None
    else:
        if verified is not True and current.get("success_criteria_verified") is not True:
            raise ValueError("complete requires verified success criteria")
        current["phase"] = "completed"
        current["success_criteria_verified"] = True
        next_message = None

    current["observed_result"] = observed_result
    current["failure_class"] = failure_class
    current["evidence"] = [*current.get("evidence", []), *evidence]
    current["next_control_message"] = next_message
    current["updated_at"] = _utc_now()
    current.setdefault("history", []).append(
        {
            "control_message": message,
            "phase_before": phase,
            "phase_after": current["phase"],
            "attempt_number": current["attempt_number"],
            "observed_result": observed_result,
            "failure_class": failure_class,
            "evidence": evidence,
            "recorded_at": current["updated_at"],
        }
    )

    if current.get("authorized_scope") != before_scope:
        raise ValueError("control message attempted to expand or alter authorized scope")
    if current.get("objective") != before_objective:
        raise ValueError("control message attempted to change the objective")
    if current.get("authority") != before_authority:
        raise ValueError("control message attempted to grant new authority")

    return current


def _artifact_json(artifact_dir: Path, name: str) -> dict[str, Any] | None:
    path = artifact_dir / name
    if not path.exists():
        return None
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Artifact {path} must contain a JSON object")
    return payload


def _retry_exhausted(attempt_number: int, retry_budget: int) -> bool:
    return attempt_number > retry_budget


def evaluate_collector_demo_api(
    *,
    operation: str,
    workflow_conclusion: str,
    attempt_number: int,
    retry_budget: int,
    artifact_dir: Path,
) -> dict[str, Any]:
    if operation not in {"what-if", "deploy", "verify"}:
        raise ValueError("operation must be what-if, deploy, or verify")
    if workflow_conclusion not in {"success", "failure", "cancelled", "timed_out"}:
        raise ValueError("unsupported workflow conclusion")
    if isinstance(attempt_number, bool) or not isinstance(attempt_number, int) or attempt_number < 1:
        raise ValueError("attempt_number must be a positive integer")
    if isinstance(retry_budget, bool) or not isinstance(retry_budget, int) or retry_budget < 0:
        raise ValueError("retry_budget must be a non-negative integer")

    request = _artifact_json(artifact_dir, "request.json")
    readiness = _artifact_json(artifact_dir, "readiness-assessment.json")
    what_if = _artifact_json(artifact_dir, "what-if-assessment.json")
    deployment = _artifact_json(artifact_dir, "deployment-result.json")
    verification = _artifact_json(artifact_dir, "verification.json")
    observed_files = sorted(path.name for path in artifact_dir.glob("*.json")) if artifact_dir.exists() else []
    retries_exhausted = _retry_exhausted(attempt_number, retry_budget)

    reasons: list[str] = []
    next_message = "escalate"
    next_operation: str | None = None
    human_gate: str | None = None
    terminal = False
    success_verified = False
    failure_class: str | None = None

    if verification and all(
        verification.get(field) is True
        for field in (
            "tls_verified",
            "health_verified",
            "twenty_correlated_transactions_verified",
            "cors_verified",
            "service_validated",
        )
    ):
        next_message = "complete"
        terminal = True
        success_verified = True
        reasons.append("all collector demo API success criteria are verified")
    elif workflow_conclusion in {"cancelled", "timed_out"}:
        reasons.append(f"workflow ended as {workflow_conclusion}; no blind retry is authorized")
        failure_class = "boundary_reached"
    elif request is None:
        reasons.append("bounded request evidence is missing, so scope and authority were not proven")
        failure_class = "authority_or_scope_unproven"
    elif readiness and readiness.get("blockers"):
        blockers = {str(item) for item in readiness.get("blockers", [])}
        if blockers & BOUNDARY_BLOCKERS:
            next_message = "escalate"
            failure_class = "boundary_reached"
            reasons.append("a governance or Azure boundary blocks continuation")
        elif blockers & STRATEGY_BLOCKERS:
            next_message = "restrategize"
            failure_class = "strategy_failure"
            reasons.append("the current Azure strategy cannot satisfy readiness")
        elif blockers and all(
            any(blocker == known or blocker.startswith(known + ":") for known in STALE_OR_UNCERTAIN_BLOCKERS)
            for blocker in blockers
        ):
            next_message = "sync_with_reality" if not retries_exhausted else "escalate"
            failure_class = "stale_or_uncertain_state"
            reasons.append("readiness failed on stale, incomplete, or conflicting Azure evidence")
        else:
            next_message = "escalate"
            failure_class = "unclassified_failure"
            reasons.append("readiness blockers are not safely classified for autonomous recovery")
    elif deployment is not None and verification is None:
        if retries_exhausted:
            next_message = "escalate"
            failure_class = "retry_budget_exhausted"
            reasons.append("deployment evidence exists but service verification is absent and the retry budget is exhausted")
        else:
            next_message = "verify"
            next_operation = "verify"
            human_gate = "explicit_verify_dispatch"
            failure_class = "verification_not_observed"
            reasons.append("deployment evidence exists, but current service success criteria are not verified")
    elif what_if and what_if.get("status") == "accepted_isolated_collector_api_changes":
        next_message = "proceed"
        next_operation = "deploy"
        human_gate = "explicit_deploy_authorization"
        reasons.append("scoped ARM What-If passed; deployment remains a separate human-authorized operation")
    elif workflow_conclusion == "failure":
        if retries_exhausted:
            next_message = "escalate"
            failure_class = "retry_budget_exhausted"
            reasons.append("the workflow failed and the retry budget is exhausted")
        elif readiness is None:
            next_message = "sync_with_reality"
            next_operation = operation
            human_gate = "explicit_workflow_dispatch"
            failure_class = "stale_or_uncertain_state"
            reasons.append("the workflow failed before a readiness conclusion was recorded")
        elif operation in {"deploy", "verify"}:
            next_message = "fix"
            next_operation = "verify" if deployment is not None else operation
            human_gate = "explicit_workflow_dispatch"
            failure_class = "recoverable_failure"
            reasons.append("the bounded operation failed after readiness; diagnose and correct within the existing scope")
        else:
            next_message = "restrategize"
            next_operation = "what-if"
            human_gate = "explicit_workflow_dispatch"
            failure_class = "strategy_failure"
            reasons.append("planning failed after readiness without an accepted scoped What-If")
    else:
        failure_class = "evidence_insufficient"
        reasons.append("workflow outcome and artifacts do not prove a safe next action")

    return {
        "schema_version": "servicetracer.governed-persistence-transition.v1",
        "objective": "deploy and verify the bounded collector-hosted demo API",
        "operation": operation,
        "workflow_conclusion": workflow_conclusion,
        "attempt_number": attempt_number,
        "retry_budget": retry_budget,
        "retries_exhausted": retries_exhausted,
        "observed_artifacts": observed_files,
        "next_control_message": next_message,
        "recommended_next_operation": next_operation,
        "human_gate_required": human_gate,
        "failure_class": failure_class,
        "reasons": reasons,
        "terminal": terminal,
        "success_criteria_verified": success_verified,
        "authority_effects": {
            "objective_changed": False,
            "scope_expanded": False,
            "azure_mutation_authorized": False,
            "workflow_dispatch_authorized": False,
            "automatic_execution_authorized": False,
        },
        "claim_boundary": (
            "This controller recommends a bounded control message from recorded evidence. "
            "It does not dispatch a workflow, authenticate to Azure, mutate Azure, expand scope, "
            "change the objective, or satisfy a human authorization gate."
        ),
        "generated_at": _utc_now(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Governed Persistence Loop controller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("new-state", help="Create a bounded persistence state document")
    create.add_argument("--objective", required=True)
    create.add_argument("--success-criterion", action="append", required=True)
    create.add_argument("--authorized-scope", action="append", required=True)
    create.add_argument("--retry-budget", type=int, required=True)
    create.add_argument("--strategy", required=True)
    create.add_argument("--output", required=True)

    transition = subparsers.add_parser("transition", help="Apply one typed control message")
    transition.add_argument("--state", required=True)
    transition.add_argument("--message", choices=sorted(CONTROL_MESSAGES), required=True)
    transition.add_argument("--observation")
    transition.add_argument("--output", required=True)

    evaluate = subparsers.add_parser(
        "evaluate-collector-demo-api",
        help="Recommend the next bounded control message from workflow evidence",
    )
    evaluate.add_argument("--operation", choices=("what-if", "deploy", "verify"), required=True)
    evaluate.add_argument(
        "--workflow-conclusion",
        choices=("success", "failure", "cancelled", "timed_out"),
        required=True,
    )
    evaluate.add_argument("--attempt-number", type=int, required=True)
    evaluate.add_argument("--retry-budget", type=int, required=True)
    evaluate.add_argument("--artifact-dir", required=True)
    evaluate.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "new-state":
        result = new_state(
            objective=args.objective,
            success_criteria=args.success_criterion,
            authorized_scope=args.authorized_scope,
            retry_budget=args.retry_budget,
            strategy=args.strategy,
        )
    elif args.command == "transition":
        state = _load_json(Path(args.state))
        if not isinstance(state, dict):
            raise SystemExit("State document must be a JSON object")
        observation: dict[str, Any] | None = None
        if args.observation:
            loaded = _load_json(Path(args.observation))
            if not isinstance(loaded, dict):
                raise SystemExit("Observation document must be a JSON object")
            observation = loaded
        result = apply_control_message(state, args.message, observation=observation)
    else:
        result = evaluate_collector_demo_api(
            operation=args.operation,
            workflow_conclusion=args.workflow_conclusion,
            attempt_number=args.attempt_number,
            retry_budget=args.retry_budget,
            artifact_dir=Path(args.artifact_dir),
        )

    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
