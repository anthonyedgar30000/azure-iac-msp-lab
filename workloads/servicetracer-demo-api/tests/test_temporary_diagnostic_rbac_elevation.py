from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNBOOK = ROOT / "docs/runbooks/temporary-diagnostic-rbac-elevation.md"
TEMPLATE = ROOT / ".project/templates/temporary-diagnostic-rbac-elevation-request.example.json"
RECONCILIATION = ROOT / ".project/reconciliations/temporary-diagnostic-rbac-elevation-process-20260725.json"
ACTIVE_AUTHORIZATION = ROOT / ".project/authorizations/temporary-diagnostic-rbac-elevation-20260725.json"
ACTIVE_WORKFLOW = ROOT / ".github/workflows/temporary-diagnostic-rbac-elevation.yml"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_request_template_is_inert() -> None:
    request = load_json(TEMPLATE)
    assert request["schema_version"] == "project.azure-temporary-diagnostic-elevation-request.v1"
    assert request["status"] == "template_only"
    assert request["authorized"] is False
    assert request["authorization_source"].startswith("No operational authorization")


def test_request_uses_named_human_contributor_at_exact_resource_group() -> None:
    request = load_json(TEMPLATE)
    assert request["principal"]["type"] == "human_user"
    assert request["principal"]["named_identity_required"] is True
    assert request["principal"]["service_principal_allowed"] is False
    assert request["principal"]["managed_identity_allowed"] is False
    assert request["role"]["name"] == "Contributor"
    assert request["role"]["owner_allowed"] is False
    assert request["role"]["user_access_administrator_allowed"] is False
    assert request["scope"]["resource_group"] == "rg-st-demo-api-dev-westus2"
    assert request["scope"]["scope_must_equal_exact_resource_group"] is True
    assert request["scope"]["subscription_scope_allowed"] is False
    assert request["scope"]["management_group_scope_allowed"] is False
    assert request["scope"]["tenant_scope_allowed"] is False


def test_request_enforces_short_pim_activation_controls() -> None:
    request = load_json(TEMPLATE)
    activation = request["activation"]
    assert activation["mechanism"] == "Microsoft Entra Privileged Identity Management"
    assert activation["maximum_duration_minutes"] == 60
    assert activation["require_mfa"] is True
    assert activation["require_approval"] is True
    assert activation["require_business_justification"] is True
    assert activation["require_ticket_reference"] is True
    assert activation["manual_deactivation_required"] is True
    assert activation["fresh_authentication_after_activation_required"] is True
    assert activation["fresh_authentication_after_deactivation_required"] is True


def test_request_allows_only_one_exact_diagnostic_attempt() -> None:
    request = load_json(TEMPLATE)
    diagnostic = request["diagnostic_test"]
    assert diagnostic["max_attempts"] == 1
    assert diagnostic["automatic_retry_authorized"] is False
    assert diagnostic["unrelated_resource_exploration_authorized"] is False
    assert diagnostic["mutation_authorized"] is False
    assert diagnostic["exact_command_workflow_or_api_digest"] == "REQUIRED"


def test_all_operational_authority_is_false_in_template() -> None:
    request = load_json(TEMPLATE)
    assert request["authority"]
    assert all(value is False for value in request["authority"].values())


def test_runbook_preserves_diagnostic_and_durable_permission_boundary() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert "temporary_broad_access_succeeds != broad_access_required_permanently" in runbook
    assert "RBAC_assignment != effective_least_privilege" in runbook
    assert "Contributor" in runbook
    assert "Owner" in runbook
    assert "one hour" in runbook
    assert "one exact diagnostic test" in runbook
    assert "Do not substitute a normal standing role assignment" in runbook
    assert "A mutating test requires separate mutation authority" in runbook
    assert "deactivation_requested != access_terminated" in runbook


def test_reconciliation_keeps_current_durable_repair_unchanged() -> None:
    reconciliation = load_json(RECONCILIATION)
    assert reconciliation["repository_observation"]["observed_main_head"] == "d548d116cf3cfa8f7927ac2ab65403ba34626aa3"
    assert reconciliation["repository_observation"]["latest_reviewed_source_ci_conclusion"] == "success"
    assert reconciliation["decision"]["durable_permission_design_changed"] is False
    assert reconciliation["decision"]["diagnostic_role"] == "Contributor"
    assert reconciliation["decision"]["maximum_activation_minutes"] == 60
    assert reconciliation["decision"]["maximum_test_attempts"] == 1
    assert reconciliation["decision"]["owner_role_allowed"] is False
    assert reconciliation["decision"]["standing_contributor_fallback_allowed"] is False


def test_increment_adds_no_operational_authorization_or_workflow() -> None:
    assert not ACTIVE_AUTHORIZATION.exists()
    assert not ACTIVE_WORKFLOW.exists()
