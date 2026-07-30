from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parent
LEGACY_PATH = ROOT / "validate.py"


def _load_legacy_validator():
    spec = importlib.util.spec_from_file_location("project_legacy_validator", LEGACY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load legacy project validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _validate_single_subscription_planner(legacy) -> None:
    workflow = (
        REPOSITORY_ROOT
        / ".github"
        / "workflows"
        / "servicetracer-demo-api-subproject-plan.yml"
    ).read_text(encoding="utf-8")
    assessor = (
        REPOSITORY_ROOT
        / "workloads"
        / "servicetracer-demo-api"
        / "scripts"
        / "assess_target_readiness.py"
    ).read_text(encoding="utf-8")
    runbook = (
        REPOSITORY_ROOT
        / "docs"
        / "runbooks"
        / "servicetracer-demo-api-student-subscription-boundary.md"
    ).read_text(encoding="utf-8")

    legacy.require("environment: azure-lab" in workflow, "planner must use azure-lab")
    legacy.require(
        workflow.count("uses: azure/login@v2") == 1,
        "planner must use exactly one Azure login",
    )
    legacy.require(
        'subscription_boundary:"single_subscription"' in workflow,
        "planner must record the single-subscription boundary",
    )
    for marker in ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID"):
        legacy.require(marker in workflow, f"planner is missing {marker}")
    for marker in (
        "AZURE_DEPENDENCY_CLIENT_ID",
        "AZURE_TARGET_CLIENT_ID",
        "AZURE_DEPENDENCY_SUBSCRIPTION_ID",
        "AZURE_TARGET_SUBSCRIPTION_ID",
        "environment: azure-api-payg",
    ):
        legacy.require(marker not in workflow, f"planner retains obsolete marker: {marker}")
    legacy.require(
        workflow.count("--validation-level ProviderNoRbac") == 2,
        "planner must use ProviderNoRbac twice",
    )
    legacy.require(
        "credential_creation_authorized:false" in workflow,
        "planner must record credential creation as unauthorized",
    )
    legacy.require("ssh-keygen" not in workflow, "planner must not generate a credential")
    legacy.require("az deployment sub create" not in workflow, "planner must not deploy")
    legacy.require("az role assignment create" not in workflow, "planner must not mutate RBAC")
    for marker in (
        "assess_target_readiness.py",
        "target-readiness-assessment.json",
        "ResourceGroupNotFound",
        'status:"observation_failed"',
        'status:"not_observed"',
    ):
        legacy.require(marker in workflow, f"planner is missing typed observation marker: {marker}")
    legacy.require("ready_for_arm_what_if" in assessor, "readiness assessor must emit ready status")
    legacy.require(
        "target_resource_group_observation_failed" in assessor,
        "readiness assessor must block failed target observation",
    )
    legacy.require(
        "does not create GitHub environments" in runbook,
        "runbook must preserve environment setup boundary",
    )
    legacy.require(
        "does not create Azure role assignments" in runbook,
        "runbook must preserve RBAC boundary",
    )


def main() -> int:
    legacy = _load_legacy_validator()
    legacy.validate_planner_contract = lambda: _validate_single_subscription_planner(legacy)
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
