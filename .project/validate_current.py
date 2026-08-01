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
    require(
        isinstance(value, str) and SHA.fullmatch(value) is not None,
        f'{field} must be a lowercase 40-character SHA',
    )


def require_digest(value, field: str) -> None:
    require(
        isinstance(value, str)
        and SHA256.fullmatch(value.removeprefix('sha256:')) is not None,
        f'{field} must be a SHA-256 digest',
    )


def write_log(message: str) -> None:
    try:
        TEST_LOG.write_text(message.rstrip() + '\n', encoding='utf-8')
    except OSError:
        pass


def validate_selector() -> tuple[dict, dict, dict, str]:
    selector = load_json(ROOT / 'CURRENT.json')
    require(
        selector.get('authoritative_current_reality')
        == '.project/current-reality-v7.json',
        'CURRENT must select current-reality-v7',
    )
    require(
        selector.get('authoritative_state_index')
        == '.project/state-index-v16.json',
        'CURRENT must select state-index-v16',
    )
    require(
        selector.get('authoritative_handoff')
        == '.project/handoffs/current-state-v6.md',
        'CURRENT must select current-state-v6',
    )
    for field in (
        'active_azure_ai_activation_authorization',
        'active_servicetracer_planning_authorization',
        'active_deployment_authorization',
        'active_servicetracer_external_validation_authorization',
        'active_cleanup_authorization',
    ):
        require(selector.get(field) is None, f'{field} must be null')

    reality = load_json(REPOSITORY_ROOT / selector['authoritative_current_reality'])
    index = load_json(REPOSITORY_ROOT / selector['authoritative_state_index'])
    handoff = (
        REPOSITORY_ROOT / selector['authoritative_handoff']
    ).read_text(encoding='utf-8')
    return selector, reality, index, handoff


def validate_current_state(
    selector: dict,
    reality: dict,
    index: dict,
    handoff: str,
) -> None:
    require(
        reality.get('schema_version') == 'project.current-reality.v12',
        'current reality schema mismatch',
    )
    require(
        index.get('schema_version') == 'project.state-index.v16',
        'state index schema mismatch',
    )
    require(
        index.get('authoritative_current_reality')
        == selector['authoritative_current_reality'],
        'state index reality pointer mismatch',
    )
    require(
        index.get('authoritative_handoff')
        == selector['authoritative_handoff'],
        'state index handoff pointer mismatch',
    )

    repo = reality.get('repository_state', {})
    require_sha(repo.get('observed_main'), 'repository_state.observed_main')
    require(
        repo.get('observed_main')
        == 'e67869e98d8c26c6525fa25e08cae1af6f5be73d',
        'repository watermark mismatch',
    )
    require(repo.get('latest_merged_pull_request') == 263, 'latest merged PR must be 263')
    require(
        repo.get('latest_merged_pull_request_source_head')
        == '83b68d4836b36ffd0db3254121eb4fe3b8ce3e80',
        'latest merged PR source head mismatch',
    )
    require(repo.get('open_pull_requests_observed') == [], 'sync must begin with no observed open PRs')
    require(repo.get('source_pr_head_ci_observed') is True, 'PR-head CI must be observed')
    require(repo.get('merge_commit_ci_observed') is False, 'merge-commit CI must remain unobserved')

    service = reality.get('domain_state', {}).get('servicetracer_demo_api', {})
    expected_true = (
        'planner_workflow_present',
        'deployment_workflow_present',
        'plan_accepted',
        'deployment_succeeded',
        'vm_running',
        'vm_extension_succeeded',
        'local_process_health_verified',
        'public_fqdn_https_health_verified_from_vm_guest',
        'azure_runtime_identity_verified',
        'runtime_identity_resource_group_matches',
        'runtime_identity_vm_matches',
        'runtime_identity_location_matches',
        'runtime_identity_source_ref_matches',
        'github_pages_publication_verified',
        'external_browser_path_verified',
        'browser_tls_verified',
        'cors_verified',
        'cors_allowed_origin_verified',
        'cors_disallowed_origin_fail_closed_verified',
        'transaction_post_verified',
        'transaction_request_correlation_verified',
        'external_validation_authority_consumed',
        'frontend_guarded_inconclusive_output_verified',
        'potential_api_evidence_boundary_defect',
        'unidentified_browser_console_404_observed',
    )
    for field in expected_true:
        require(service.get(field) is True, f'servicetracer_demo_api.{field} must be true')

    expected_false = (
        'repository_head_matches_deployed_source_ref',
        'external_validation_retry_authorized',
        'downstream_transaction_success_verified',
        'stable_backend_localization_verified',
        'exact_root_cause_claimed',
        'cleanup_verified',
    )
    for field in expected_false:
        require(service.get(field) is False, f'servicetracer_demo_api.{field} must be false')

    require(service.get('planning_run_id') == 30660575435, 'planning run mismatch')
    require(service.get('deployment_run_id') == 30661015789, 'deployment run mismatch')
    require(service.get('external_validation_run_id') == 30693434244, 'external validation run mismatch')
    require(service.get('external_validation_artifact_id') == 8816461373, 'external artifact mismatch')
    require_sha(service.get('deployed_source_ref'), 'servicetracer_demo_api.deployed_source_ref')
    require(service.get('bounded_sample_attempts') == 20, 'bounded sample count mismatch')
    require(service.get('bounded_sample_successes') == 0, 'bounded sample success count mismatch')
    require(service.get('bounded_sample_failures') == 20, 'bounded sample failure count mismatch')
    require(service.get('bounded_sample_transport_errors') == 0, 'bounded sample transport count mismatch')
    require(
        service.get('bounded_sample_backend_counts') == {'VPN-01': 0, 'VPN-02': 20},
        'bounded backend counts mismatch',
    )
    require(
        service.get('bounded_sample_failure_boundary_counts') == {'radius_response': 20},
        'bounded failure-boundary counts mismatch',
    )
    require(
        service.get('potential_api_evidence_boundary_defect_status') == 'unresolved',
        'API evidence-boundary defect must remain unresolved',
    )
    require(service.get('raw_api_inconclusive_boundary') == 'VPN-02', 'raw API boundary mismatch')
    require(
        service.get('undeployed_repository_commits')
        == [
            'b5bfd616d2f3faab5f692301c4b71c46a6f9557f',
            '2ad9557e21cddeed6fc9437c8f20c32b387bf2a2',
        ],
        'undeployed commit set mismatch',
    )
    require(
        all(value is None for value in index.get('active_authorizations', {}).values()),
        'no operational authority may remain active',
    )

    for marker in (
        'HTTP_200_API_response != downstream_transaction_success',
        'all_observed_transactions_on_VPN-02 != stable_backend_localization',
        'potential API evidence-boundary defect',
        'external validation retry authorized: false',
        'actual month-to-date Azure cost',
    ):
        require(marker in handoff, f'handoff is missing marker: {marker}')


def validate_external_evidence() -> None:
    evidence = load_json(
        ROOT / 'evidence' / 'servicetracer-external-path-run-30693434244.json'
    )
    require(
        evidence.get('schema_version')
        == 'project.servicetracer-external-path-evidence.v1',
        'external evidence schema mismatch',
    )
    source = evidence.get('source', {})
    require(source.get('pull_request') == 263, 'external evidence PR mismatch')
    require(source.get('workflow_run_id') == 30693434244, 'external evidence run mismatch')
    require(source.get('workflow_run_attempt') == 1, 'external evidence attempt mismatch')
    require(source.get('workflow_conclusion') == 'success', 'external evidence must be successful')
    require_sha(source.get('authorized_pr_head_sha'), 'external evidence PR head')
    require_sha(source.get('successful_workflow_checkout_sha'), 'external evidence checkout SHA')
    require_sha(source.get('merged_main_sha'), 'external evidence merged main SHA')

    artifact = evidence.get('artifact', {})
    require(artifact.get('artifact_id') == 8816461373, 'external artifact ID mismatch')
    require_digest(artifact.get('digest'), 'external artifact digest')
    require(artifact.get('internal_manifest_verified') is True, 'external artifact manifest must be verified')
    require(artifact.get('internal_manifest_entries') == 17, 'external artifact manifest count mismatch')
    for name, digest in artifact.get('selected_file_sha256', {}).items():
        require_digest(digest, f'external artifact file {name}')

    frontend = evidence.get('frontend_observation', {})
    require(frontend.get('github_pages_publication_verified') is True, 'GitHub Pages is not verified')
    require(frontend.get('hosted_chrome_render_verified') is True, 'browser render is not verified')
    require(frontend.get('fixture_fallback_used') is False, 'fixture fallback must not be used')
    require(frontend.get('rendered_suspect') == 'Not established', 'frontend invented a suspect')
    require(frontend.get('technician_workflow_hidden') is True, 'frontend exposed an unsupported workflow')

    contract = evidence.get('api_contract_observation', {})
    require(contract.get('health_http_status') == 200, 'health status mismatch')
    require(contract.get('allowed_origin_preflight_http_status') == 204, 'preflight status mismatch')
    require(contract.get('transaction_http_status') == 200, 'POST status mismatch')
    require(contract.get('request_header_and_body_ids_matched') is True, 'request IDs did not match')
    require(contract.get('azure_host', {}).get('verified') is True, 'browser Azure identity is not verified')
    require_sha(contract.get('azure_host', {}).get('source_ref'), 'browser runtime source ref')
    denied = contract.get('disallowed_origin', {})
    require(denied.get('http_status') == 403, 'denied-origin status mismatch')
    require(denied.get('error') == 'origin_not_allowed', 'denied-origin error mismatch')
    require(denied.get('fail_closed_verified') is True, 'denied-origin fail-closed proof missing')

    sample = evidence.get('bounded_transaction_sample', {})
    require(sample.get('attempts') == 20, 'external sample attempts mismatch')
    require(sample.get('successful_transactions') == 0, 'external sample successes mismatch')
    require(sample.get('failed_transactions') == 20, 'external sample failures mismatch')
    require(sample.get('transport_errors') == 0, 'external sample transport errors mismatch')
    require(sample.get('backend_counts') == {'VPN-01': 0, 'VPN-02': 20}, 'external backend counts mismatch')
    require(sample.get('failure_boundary_counts') == {'radius_response': 20}, 'external failure boundary mismatch')
    require(sample.get('stable_backend_localization') is False, 'stable localization must remain false')
    require(sample.get('exact_root_cause_claimed') is False, 'exact root cause must remain false')
    require(sample.get('downstream_transaction_success_verified') is False, 'downstream success must remain false')

    assessment = evidence.get('evidence_boundary_assessment', {})
    require(
        assessment.get('status') == 'potential_api_evidence_boundary_defect_unresolved',
        'API evidence-boundary status mismatch',
    )
    require(assessment.get('raw_api_service_tracer_stops_at') == 'VPN-02', 'raw API stop boundary mismatch')
    require(assessment.get('raw_api_stable_localization') is False, 'raw API localization must be inconclusive')
    require(assessment.get('frontend_guard_prevented_unsupported_localization') is True, 'frontend guard proof missing')


def validate_authority_and_reconciliation() -> None:
    authority_record = load_json(
        ROOT / 'authorizations' / 'servicetracer-external-validation-20260801.json'
    )
    authorization = authority_record.get('authorization', {})
    require(authorization.get('status') == 'consumed_success', 'external authority status mismatch')
    require(authorization.get('active_for_one_attempt') is False, 'external authority must be inactive')
    require(authorization.get('attempt_consumed') is True, 'external authority must be consumed')
    require(authorization.get('retry_authorized') is False, 'external retry must not be authorized')
    require(authorization.get('manual_dispatch_authorized') is False, 'manual dispatch must not be authorized')

    recon = load_json(
        ROOT / 'reconciliations' / 'servicetracer-external-evidence-sync-20260801.json'
    )
    promoted = recon.get('promoted_evidence', {})
    require(promoted.get('workflow_run_id') == 30693434244, 'reconciliation run mismatch')
    require(promoted.get('artifact_id') == 8816461373, 'reconciliation artifact mismatch')
    require_digest(promoted.get('artifact_digest'), 'reconciliation artifact digest')
    require(promoted.get('authorization_status') == 'consumed_success', 'reconciliation authority mismatch')

    reconciliation_authority = recon.get('authority', {})
    for field in (
        'workflow_dispatch_or_rerun_by_this_sync',
        'external_live_post_by_this_sync',
        'azure_authentication_or_query_by_this_sync',
        'arm_what_if_by_this_sync',
        'guest_command_by_this_sync',
        'azure_mutation_by_this_sync',
        'rbac_mutation',
        'deployment',
        'repair',
        'redeployment',
        'rollback',
        'cleanup',
    ):
        require(
            reconciliation_authority.get(field) is False,
            f'reconciliation authority field {field} must be false',
        )


def validate_prior_evidence_and_workflows() -> None:
    plan = load_json(
        ROOT / 'evidence' / 'servicetracer-demo-api-plan-run-30660575435.json'
    )
    deploy = load_json(
        ROOT / 'evidence' / 'servicetracer-demo-api-deployment-run-30661015789.json'
    )
    require(plan.get('source', {}).get('workflow_run_id') == 30660575435, 'plan evidence run mismatch')
    require(plan.get('what_if', {}).get('status') == 'accepted_independent_workload_create_plan', 'plan What-If mismatch')
    require(deploy.get('source', {}).get('workflow_run_id') == 30661015789, 'deployment evidence run mismatch')
    require(deploy.get('deployment', {}).get('provisioning_state') == 'Succeeded', 'deployment did not succeed')

    external_workflow = (
        REPOSITORY_ROOT / '.github/workflows/servicetracer-demo-api-live-verify.yml'
    ).read_text(encoding='utf-8')
    require('\n  workflow_dispatch:\n' not in external_workflow, 'external workflow must not allow manual dispatch')
    require(
        'ref: ${{ github.event.pull_request.head.sha }}' in external_workflow,
        'external workflow must check out the exact PR head',
    )
    require('Evaluate one-shot authority' in external_workflow, 'external workflow lacks authority gate')
    require(
        "if: steps.authority.outputs.authorized == 'true'" in external_workflow,
        'external workflow network steps are not authority-gated',
    )
    for forbidden in (
        'azure/login',
        'az login',
        'az deployment',
        'az vm run-command',
        'az role assignment',
    ):
        require(forbidden not in external_workflow, f'external workflow contains forbidden operation: {forbidden}')

    source = load_json(REPOSITORY_ROOT / 'docs/report-source.json')
    expected = 'https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/demo/run'
    require(source.get('live_demo_api_url') == expected, 'frontend live API URL mismatch')
    require(
        source.get('activation_status')
        == 'independent_demo_api_live_default_pending_github_pages_verification',
        'frontend repository activation label changed without a publication change',
    )
    require(
        source.get('evidence_anchor')
        == '.project/evidence/servicetracer-demo-api-deployment-run-30661015789.json',
        'frontend repository evidence anchor changed without a publication change',
    )


def main() -> int:
    stage = 'startup'
    try:
        stage = 'selector'
        selector, reality, index, handoff = validate_selector()
        stage = 'current-state'
        validate_current_state(selector, reality, index, handoff)
        stage = 'external-evidence'
        validate_external_evidence()
        stage = 'authority-and-reconciliation'
        validate_authority_and_reconciliation()
        stage = 'prior-evidence-and-workflows'
        validate_prior_evidence_and_workflows()
    except (ValidationError, OSError) as exc:
        message = f'workflow-observability validation failed at {stage}: {exc}'
        print(message, file=sys.stderr)
        write_log(message)
        return 1

    message = (
        'workflow-observability validation passed: canonical deployment, consumed '
        'external browser evidence, authority, uncertainty, and next-gate boundaries '
        'are consistent'
    )
    print(message)
    write_log(message)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
