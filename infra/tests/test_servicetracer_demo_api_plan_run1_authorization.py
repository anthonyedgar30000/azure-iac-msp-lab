import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / ".project/deployment-requests/servicetracer-demo-api-plan-run1.json"
WORKFLOW = ROOT / ".github/workflows/servicetracer-demo-api-subproject-plan.yml"


def load_request():
    return json.loads(REQUEST.read_text(encoding="utf-8"))


def test_exact_repository_and_workflow_boundary():
    request = load_request()
    boundary = request["repository_boundary"]
    assert boundary["base_branch"] == "main"
    assert boundary["base_commit"] == "1eca6b55e93d7276ada5fb06ffd8707d3895936a"
    assert boundary["latest_merged_pull_request"] == 230
    assert boundary["workflow"] == ".github/workflows/servicetracer-demo-api-subproject-plan.yml"
    assert WORKFLOW.exists()


def test_exact_planning_inputs_and_confirmation():
    request = load_request()
    inputs = request["inputs"]
    assert inputs == {
        "environment": "dev",
        "location": "westus2",
        "prefix": "mst",
        "dependency_resource_group": "rg-servicetracer-dev-westus2",
        "dns_label": "st-demo-api-vm-aeg30000",
        "allowed_origin": "https://anthonyedgar30000.github.io",
        "vm_size": "Standard_F1als_v7",
        "maximum_monthly_cost_cad": "25.00",
    }
    assert request["dispatch"]["confirmation"] == (
        "PLAN-DEMO-API-SUBPROJECT:dev:st-demo-api-vm-aeg30000"
    )


def test_one_attempt_planning_only_authority():
    request = load_request()
    scope = request["scope"]
    assert request["attempt_limit"] == 1
    assert request["dispatch"]["authorized"] is True
    assert request["dispatch"]["performed"] is False
    assert request["dispatch"]["rerun_authorized"] is False
    assert scope["arm_validation_authorized"] is True
    assert scope["arm_what_if_authorized"] is True
    assert scope["azure_resource_mutation_authorized"] is False
    assert scope["deployment_authorized"] is False
    assert scope["rbac_mutation_authorized"] is False
    assert scope["provider_registration_authorized"] is False
    assert scope["cleanup_authorized"] is False
    assert scope["rollback_authorized"] is False


def test_workflow_remains_planning_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "environment: azure-api-payg" in text
    assert "ProviderNoRbac" in text
    assert "az deployment sub validate" in text
    assert "az deployment sub what-if" in text
    assert "az deployment sub create" not in text
    assert "deployment_authorized:false" in text


def test_cost_ceiling_is_not_spend_authority():
    cost = load_request()["cost"]
    assert cost["planning_ceiling_cad"] == "25.00"
    assert cost["ceiling_is_spend_authority"] is False
    assert cost["actual_cost_freshly_observed"] is False
    assert cost["quota_freshly_observed"] is False
