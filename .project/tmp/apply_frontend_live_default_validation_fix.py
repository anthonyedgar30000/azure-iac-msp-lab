from __future__ import annotations

from pathlib import Path
import re


VALIDATOR = Path('.project/validate.py')
COLLECTOR_TEST = Path('infra/tests/test_collector_demo_api.py')


def replace_once(source: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one replacement, got {count}')
    return updated


def patch_validator() -> None:
    source = VALIDATOR.read_text(encoding='utf-8')
    if 'LIVE_COLLECTOR_API =' not in source:
        source = source.replace(
            'SHA256 = re.compile(r"^[0-9a-f]{64}$")\n',
            'SHA256 = re.compile(r"^[0-9a-f]{64}$")\n'
            'LIVE_COLLECTOR_API = "https://st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com/api/demo/run"\n'
            'COLLECTOR_DEPLOYMENT_EVIDENCE = ROOT / "reconciliations" / "collector-demo-api-deployment-run18-20260726.json"\n',
            1,
        )

    replacement = '''def validate_frontend_configuration() -> None:
    source = load_json(REPOSITORY_ROOT / "docs" / "report-source.json")
    require(source.get("schema_version") == "servicetracer.report-source.v1", "report-source schema is invalid")
    require(source.get("live_report_url") == "", "unverified report URL must remain blank")
    require(source.get("live_demo_api_url") == LIVE_COLLECTOR_API, "live demo API must match the exact deployed collector endpoint")
    require(source.get("candidate_demo_api_url") == LIVE_COLLECTOR_API, "candidate API must remain aligned with the live endpoint")
    require(source.get("fallback_report_url") == "technician-handoff-report.json", "fixture fallback changed unexpectedly")
    require(source.get("activation_status") == "live_default_pending_github_pages_verification", "frontend activation status is invalid")
    require(
        source.get("evidence_anchor") == ".project/reconciliations/collector-demo-api-deployment-run18-20260726.json",
        "frontend evidence anchor is invalid",
    )
    require("does not by itself prove" in require_text(source.get("claim_boundary"), "report-source.claim_boundary"), "frontend claim boundary is incomplete")

    evidence = load_json(COLLECTOR_DEPLOYMENT_EVIDENCE)
    require(evidence.get("schema_version") == "project.collector-demo-api-deployment-evidence.v1", "collector deployment evidence schema is invalid")
    deployment_source = require_object(evidence.get("source"), "collector-deployment.source")
    require(deployment_source.get("reviewed_commit") == "98b092201053fd3592be157a24de6e623e6b74a6", "collector deployment source mismatch")
    require(deployment_source.get("workflow_run_id") == 30196388398, "collector deployment run mismatch")
    require(deployment_source.get("workflow_run_number") == 18, "collector deployment run number mismatch")
    require(deployment_source.get("operation") == "deploy", "collector deployment operation mismatch")

    artifact = require_object(evidence.get("artifact"), "collector-deployment.artifact")
    require(artifact.get("artifact_id") == 8630260279, "collector deployment artifact mismatch")
    require_digest(artifact.get("sha256"), "collector-deployment.artifact.sha256")
    require(artifact.get("manifest_payloads_verified") == 48, "collector deployment manifest count mismatch")
    require(artifact.get("manifest_payload_failures") == 0, "collector deployment manifest contains failures")

    deployment = require_object(evidence.get("deployment"), "collector-deployment.deployment")
    require(deployment.get("parent_deployment") == "Succeeded", "collector parent deployment did not succeed")
    require(deployment.get("nested_deployment") == "Succeeded", "collector nested deployment did not succeed")
    extension = require_object(deployment.get("collector_vm_extension"), "collector-deployment.extension")
    require(extension.get("provisioning_state") == "Succeeded", "collector extension did not converge")
    require(extension.get("force_update_tag") == deployment_source.get("reviewed_commit"), "collector extension source binding mismatch")
    pool = require_object(deployment.get("backend_pool"), "collector-deployment.backend_pool")
    require(pool.get("provisioning_state") == "Succeeded", "collector backend pool did not converge")
    require(pool.get("address_count") == 1, "collector backend pool must contain exactly one address")
    require(pool.get("address_name") == "collector", "collector backend address name mismatch")
    require(pool.get("private_ip") == "10.20.40.10", "collector backend private IP mismatch")

    runtime = require_object(evidence.get("runtime_evidence"), "collector-deployment.runtime")
    require(runtime.get("health_status") == "healthy", "collector API health is not established")
    require(runtime.get("backend_target_configured") is True, "collector API backend target is not configured")
    require(runtime.get("transaction_request_http_status") == 200, "collector API transaction request did not return HTTP 200")
    require(runtime.get("transaction_count") == 20, "collector API evidence must contain exactly 20 transactions")
    require(runtime.get("exact_root_cause_claimed") is False, "collector API evidence claimed unsupported root cause")
    require(runtime.get("cors_preflight_status") == 204, "collector API CORS preflight failed")
    require(runtime.get("cors_allow_origin") == "https://anthonyedgar30000.github.io", "collector API CORS origin mismatch")
    require(runtime.get("cors_allows_post") is True, "collector API CORS does not allow POST")

    conclusion = require_object(evidence.get("workflow_conclusion"), "collector-deployment.workflow_conclusion")
    require(conclusion.get("classification") == "verifier_false_negative_after_successful_deployment_and_runtime_requests", "collector workflow failure classification mismatch")
    require(conclusion.get("deployment_failed") is False, "collector evidence incorrectly marks deployment failed")
    require(conclusion.get("service_failed") is False, "collector evidence incorrectly marks service failed")

    authority = require_object(evidence.get("authority"), "collector-deployment.authority")
    require(authority.get("one_shot_deployment_authority_consumed") is True, "deployment authority consumption is not recorded")
    require(authority.get("retry_authorized") is False, "deployment retry must remain unauthorized")
    require(authority.get("additional_azure_mutation_authorized") is False, "additional Azure mutation must remain unauthorized")


'''
    source = replace_once(
        source,
        r'def validate_frontend_configuration\(\) -> None:\n.*?\n\ndef validate_planner_contract\(\) -> None:',
        replacement + 'def validate_planner_contract() -> None:',
        'frontend validator',
    )
    VALIDATOR.write_text(source, encoding='utf-8')


def patch_collector_test() -> None:
    source = COLLECTOR_TEST.read_text(encoding='utf-8')
    replacement = '''    def test_source_configuration_activates_exact_verified_collector_endpoint(self):
        config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
        expected = "https://st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com/api/demo/run"
        self.assertEqual(config["live_report_url"], "")
        self.assertEqual(config["live_demo_api_url"], expected)
        self.assertEqual(config["candidate_demo_api_url"], expected)
        self.assertEqual(config["fallback_report_url"], "technician-handoff-report.json")
        self.assertEqual(
            config["activation_status"],
            "live_default_pending_github_pages_verification",
        )
        self.assertEqual(
            config["evidence_anchor"],
            ".project/reconciliations/collector-demo-api-deployment-run18-20260726.json",
        )
        self.assertIn("does not by itself prove", config["claim_boundary"])

'''
    source = replace_once(
        source,
        r'    def test_source_configuration_withholds_unverified_endpoint\(self\):\n.*?\n(?=    def |\nif __name__)',
        replacement,
        'collector source configuration test',
    )
    COLLECTOR_TEST.write_text(source, encoding='utf-8')


if __name__ == '__main__':
    patch_validator()
    patch_collector_test()
