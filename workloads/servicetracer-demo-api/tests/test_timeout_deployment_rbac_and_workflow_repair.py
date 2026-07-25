from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PARSER = ROOT / "workloads/servicetracer-demo-api/scripts/assert_effective_arm_permissions.py"
AUTHORIZED = ROOT / "workloads/servicetracer-demo-api/tests/fixtures/effective-arm-permissions-authorized.json"
MISSING = ROOT / "workloads/servicetracer-demo-api/tests/fixtures/effective-arm-permissions-missing-deployment-write.json"
RBAC = ROOT / "infra/rbac/servicetracer-demo-api-deployment-submitter-rbac.bicep"
BOOTSTRAP = ROOT / "scripts/bootstrap_servicetracer_deployment_submitter_rbac.sh"
WORKFLOW = ROOT / ".github/workflows/servicetracer-demo-api-timeout-fix-deploy-after-deployment-submitter-rbac.yml"
FUTURE_AUTHORIZATION = ROOT / ".project/authorizations/servicetracer-demo-api-timeout-fix-deployment-after-deployment-submitter-rbac-20260725.json"

REQUIRED = [
    "Microsoft.Resources/deployments/write",
    "Microsoft.Compute/virtualMachines/extensions/write",
]


def run_parser(path: Path) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(PARSER), str(path)]
    for action in REQUIRED:
        command.extend(["--require", action])
    return subprocess.run(command, check=False, capture_output=True, text=True)


def test_effective_permissions_fixture_accepts_both_required_actions() -> None:
    result = run_parser(AUTHORIZED)
    assert result.returncode == 0
    assert "required ARM permissions verified" in result.stdout


def test_effective_permissions_fixture_rejects_missing_deployment_write() -> None:
    result = run_parser(MISSING)
    assert result.returncode == 1
    assert "Microsoft.Resources/deployments/write" in result.stderr


def test_not_actions_override_matching_actions() -> None:
    document = json.loads(AUTHORIZED.read_text(encoding="utf-8"))
    document["value"][0]["actions"] = ["Microsoft.Resources/*"]
    document["value"][0]["notActions"] = ["Microsoft.Resources/deployments/write"]
    temporary = AUTHORIZED.with_name("effective-arm-permissions-temporary.json")
    temporary.write_text(json.dumps(document), encoding="utf-8")
    try:
        result = run_parser(temporary)
        assert result.returncode == 1
    finally:
        temporary.unlink(missing_ok=True)


def test_custom_role_is_narrow_and_resource_group_scoped() -> None:
    template = RBAC.read_text(encoding="utf-8")
    assert "Microsoft.Resources/deployments/write" in template
    assert "Microsoft.Resources/*" not in template
    assert "Microsoft.Compute/virtualMachines/extensions/write" not in template
    assert "scope: targetResourceGroup" in template
    assert "assignableScopes" in template


def test_bootstrap_defaults_to_plan_only() -> None:
    script = BOOTSTRAP.read_text(encoding="utf-8")
    assert "apply=false" in script
    assert "--apply" in script
    assert "rbac_mutation_performed:false" in script
    assert "az deployment sub what-if" in script


def test_new_workflow_reobserves_permissions_before_deployment() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Microsoft.Authorization/permissions?api-version=2022-04-01" in workflow
    assert "assert_effective_arm_permissions.py" in workflow
    assert "--require Microsoft.Resources/deployments/write" in workflow
    assert "--require Microsoft.Compute/virtualMachines/extensions/write" in workflow
    assert workflow.index("assert_effective_arm_permissions.py") < workflow.index("az deployment group create")


def test_new_workflow_uses_truthful_rollback_semantics() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "rollback_required" in workflow
    assert "rollback_attempted" in workflow
    assert "rollback_submission_accepted" in workflow
    assert "rollback_verified" in workflow
    assert "attempted_tag_observed" in workflow
    assert "rollback_performed:true" not in workflow


def test_new_workflow_is_inert_until_separate_authorization() -> None:
    assert not FUTURE_AUTHORIZATION.exists()
