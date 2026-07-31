from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parent
TEST_LOG = Path('/tmp/tests.log')
SHA = re.compile(r'^[0-9a-f]{40}$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ValidationError(f'missing required file: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(value, dict), f'{path} must contain a JSON object')
    return value


def require_sha(value, field: str) -> None:
    require(isinstance(value, str) and SHA.fullmatch(value) is not None, f'{field} must be a lowercase 40-character SHA')


def require_digest(value, field: str) -> None:
    require(isinstance(value, str) and SHA256.fullmatch(value.removeprefix('sha256:')) is not None, f'{field} must be a SHA-256 digest')


def write_log(message: str) -> None:
    try:
        TEST_LOG.write_text(message.rstrip() + '\n', encoding='utf-8')
    except OSError:
        pass


def validate_selector() -> tuple[dict, dict, dict, str]:
    selector = load_json(ROOT / 'CURRENT.json')
    require(selector.get('authoritative_current_reality') == '.project/current-reality-v6.json', 'CURRENT must select current-reality-v6')
    require(selector.get('authoritative_state_index') == '.project/state-index-v15.json', 'CURRENT must select state-index-v15')
    require(selector.get('authoritative_handoff') == '.project/handoffs/current-state-v5.md', 'CURRENT must select current-state-v5')
    for field in ('active_azure_ai_activation_authorization', 'active_servicetracer_planning_authorization', 'active_deployment_authorization', 'active_cleanup_authorization'):
        require(selector.get(field) is None, f'{field} must be null')
    reality = load_json(REPOSITORY_ROOT / selector['authoritative_current_reality'])
    index = load_json(REPOSITORY_ROOT / selector['authoritative_state_index'])
    handoff = (REPOSITORY_ROOT / selector['authoritative_handoff']).read_text(encoding='utf-8')
    return selector, reality, index, handoff


def validate_current_state(selector: dict, reality: dict, index: dict, handoff: str) -> None:
    require(reality.get('schema_version') == 'project.current-reality.v11', 'current reality schema mismatch')
    require(index.get('schema_version') == 'project.state-index.v15', 'state index schema mismatch')
    require(index.get('authoritative_current_reality') == selector['authoritative_current_reality'], 'state index reality pointer mismatch')
    require(index.get('authoritative_handoff') == selector['authoritative_handoff'], 'state index handoff pointer mismatch')
    repo = reality.get('repository_state', {})
    require_sha(repo.get('observed_main'), 'repository_state.observed_main')
    require(repo.get('latest_merged_pull_request') == 260, 'latest merged PR must be 260')
    require(repo.get('open_pull_requests_observed') == [], 'sync must begin with no observed open PRs')
    service = reality.get('domain_state', {}).get('servicetracer_demo_api', {})
    expected_true = (
        'planner_workflow_present', 'deployment_workflow_present', 'plan_accepted',
        'deployment_succeeded', 'vm_running', 'vm_extension_succeeded',
        'local_process_health_verified', 'public_fqdn_https_health_verified_from_vm_guest',
        'azure_runtime_identity_verified', 'runtime_identity_resource_group_matches',
        'runtime_identity_vm_matches', 'runtime_identity_location_matches',
        'runtime_identity_source_ref_matches',
    )
    for field in expected_true:
        require(service.get(field) is True, f'servicetracer_demo_api.{field} must be true')
    for field in ('external_browser_path_verified', 'github_pages_publication_verified', 'cors_verified', 'transaction_post_verified', 'downstream_transaction_success_verified', 'cleanup_verified'):
        require(service.get(field) is False, f'servicetracer_demo_api.{field} must remain false')
    require(service.get('planning_run_id') == 30660575435, 'planning run mismatch')
    require(service.get('deployment_run_id') == 30661015789, 'deployment run mismatch')
    require_sha(service.get('deployed_source_ref'), 'servicetracer_demo_api.deployed_source_ref')
    require(all(value is None for value in index.get('active_authorizations', {}).values()), 'no operational authority may remain active')
    for marker in ('deployment_succeeded != service_validated', 'public_FQDN_from_VM_guest != external_browser_path', 'active cleanup authority: none', 'actual month-to-date cost'):
        require(marker in handoff, f'handoff is missing marker: {marker}')


def validate_evidence() -> None:
    plan = load_json(ROOT / 'evidence' / 'servicetracer-demo-api-plan-run-30660575435.json')
    deploy = load_json(ROOT / 'evidence' / 'servicetracer-demo-api-deployment-run-30661015789.json')
    recon = load_json(ROOT / 'reconciliations' / 'servicetracer-plan-deploy-runtime-sync-20260731.json')
    require(plan.get('source', {}).get('workflow_run_id') == 30660575435, 'plan evidence run mismatch')
    require(plan.get('source', {}).get('conclusion') == 'success', 'plan evidence must be successful')
    require_digest(plan.get('artifact', {}).get('sha256'), 'plan artifact sha256')
    require(plan.get('what_if', {}).get('status') == 'accepted_independent_workload_create_plan', 'plan What-If was not accepted')
    require(deploy.get('source', {}).get('workflow_run_id') == 30661015789, 'deployment evidence run mismatch')
    require(deploy.get('source', {}).get('conclusion') == 'success', 'deployment workflow must be successful')
    require_digest(deploy.get('artifact', {}).get('sha256'), 'deployment artifact sha256')
    require(deploy.get('artifact', {}).get('internal_manifest_verified') is True, 'deployment artifact manifest must be verified')
    require(deploy.get('artifact', {}).get('internal_manifest_entries') == 45, 'deployment artifact manifest count mismatch')
    require(deploy.get('deployment', {}).get('provisioning_state') == 'Succeeded', 'Azure deployment did not succeed')
    runtime = deploy.get('runtime_evidence', {})
    require(runtime.get('local_process_health', {}).get('status') == 'healthy', 'local health is not established')
    public = runtime.get('public_fqdn_health_from_vm_guest', {})
    require(public.get('status') == 'healthy', 'public FQDN health is not established')
    require(public.get('azure_host', {}).get('verified') is True, 'Azure runtime identity is not verified')
    require_sha(public.get('azure_host', {}).get('source_ref'), 'runtime source_ref')
    require(runtime.get('external_browser_path_verified') is False, 'browser path must remain unverified')
    require(runtime.get('transaction_post_verified') is False, 'POST transaction must remain unverified')
    authority = recon.get('authority', {})
    for field in ('workflow_dispatch_or_rerun_by_this_sync', 'azure_authentication_or_query_by_this_sync', 'guest_command_by_this_sync', 'arm_what_if_by_this_sync', 'azure_mutation_by_this_sync', 'deployment', 'cleanup', 'rollback'):
        require(authority.get(field) is False, f'reconciliation authority field {field} must be false')


def validate_workflows_and_frontend() -> None:
    planner = (REPOSITORY_ROOT / '.github/workflows/servicetracer-demo-api-subproject-plan.yml').read_text(encoding='utf-8')
    deployer = (REPOSITORY_ROOT / '.github/workflows/servicetracer-demo-api-subproject-deploy.yml').read_text(encoding='utf-8')
    source = load_json(REPOSITORY_ROOT / 'docs/report-source.json')
    require('environment: azure-lab' in planner, 'planner must use azure-lab')
    require(planner.count('uses: azure/login@v2') == 1, 'planner must use one Azure login')
    require('az deployment sub create' not in planner, 'planner must remain non-deploying')
    require(deployer.count('az deployment sub create') == 1, 'deployment workflow must contain exactly one deployment command')
    for forbidden in ('az group delete', 'az resource delete', 'az vm run-command', 'az role assignment create'):
        require(forbidden not in deployer, f'deployment workflow contains forbidden command: {forbidden}')
    expected = 'https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/demo/run'
    require(source.get('live_demo_api_url') == expected, 'frontend live API URL mismatch')
    require(source.get('candidate_demo_api_url') == expected, 'frontend candidate API URL mismatch')
    require(source.get('activation_status') == 'independent_demo_api_live_default_pending_github_pages_verification', 'frontend activation status mismatch')
    require(source.get('evidence_anchor') == '.project/evidence/servicetracer-demo-api-deployment-run-30661015789.json', 'frontend evidence anchor mismatch')


def main() -> int:
    stage = 'startup'
    try:
        stage = 'selector'
        selector, reality, index, handoff = validate_selector()
        stage = 'current-state'
        validate_current_state(selector, reality, index, handoff)
        stage = 'evidence'
        validate_evidence()
        stage = 'workflows-and-frontend'
        validate_workflows_and_frontend()
    except (ValidationError, OSError) as exc:
        message = f'workflow-observability validation failed at {stage}: {exc}'
        print(message, file=sys.stderr)
        write_log(message)
        return 1
    message = 'workflow-observability validation passed: canonical plan, deployment, runtime health, authority, and frontend boundaries are consistent'
    print(message)
    write_log(message)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
