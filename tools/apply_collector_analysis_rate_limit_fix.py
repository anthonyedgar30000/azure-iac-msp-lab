from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    content = target.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, observed {count}")
    target.write_text(content.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    installer_old = """    location /api/ {
        limit_req zone=servicetracer_demo_api burst=2 nodelay;
        proxy_pass http://127.0.0.1:${LOCAL_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \\$host;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout ${PROXY_READ_TIMEOUT_SECONDS}s;
        client_max_body_size 4k;
    }
"""
    installer_new = """    # Health and provenance polling are deliberately outside the analysis limiter.
    # A healthy endpoint does not prove that a live analysis request completed.
    location = /api/health {
        proxy_pass http://127.0.0.1:${LOCAL_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \\$host;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 10s;
    }

    # Browser execution requires a CORS preflight and a POST. Keep rate limiting
    # on the expensive analysis path while reserving enough burst for that pair.
    location = /api/demo/run {
        limit_req zone=servicetracer_demo_api burst=4 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:${LOCAL_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \\$host;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout ${PROXY_READ_TIMEOUT_SECONDS}s;
        client_max_body_size 4k;
    }

    location /api/ {
        return 404;
    }
"""
    replace_once(
        "infra/scripts/install_collector_demo_api.sh",
        installer_old,
        installer_new,
    )

    replace_once(
        "docs/live-monitor.js",
        "apiReady ? 'Healthy API response' : 'Health contract rejected'",
        "apiReady ? 'Health endpoint reachable' : 'Health contract rejected'",
    )
    replace_once(
        "docs/live-monitor.js",
        "setMonitorState('Frontend ↔ governed collector API live', 'healthy');",
        "setMonitorState('Collector health and Azure identity verified', 'healthy');",
    )
    replace_once(
        "infra/tests/test_frontend_azure_provenance_monitor.py",
        '        self.assertIn("Frontend ↔ governed collector API live", source)',
        '        self.assertIn("Collector health and Azure identity verified", source)',
    )

    replace_once(
        "docs/app.js",
        """      elements.reportSourceName.textContent = 'Controlled demo fixture — API unavailable';
      elements.reportSourceDetail.textContent = 'The live Azure API failed; using the controlled fixture.';""",
        """      elements.reportSourceName.textContent = 'Controlled demo fixture — live analysis unavailable';
      elements.reportSourceDetail.textContent = 'Collector health was verified, but the live analysis request did not complete; using the controlled fixture.';""",
    )
    replace_once(
        "docs/app.js",
        """        elements.reportSourceName.textContent = 'Controlled demo fixture — API unavailable';
        elements.reportSourceDetail.textContent = 'The configured API did not pass its health contract; no live transactions will run.';""",
        """        elements.reportSourceName.textContent = 'Controlled demo fixture — API health unavailable';
        elements.reportSourceDetail.textContent = 'The configured API did not pass its health contract; no live transactions will run.';""",
    )

    test_source = '''from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "infra" / "scripts" / "install_collector_demo_api.sh"
APP = ROOT / "docs" / "app.js"
MONITOR = ROOT / "docs" / "live-monitor.js"


class CollectorAnalysisRateLimitFixTests(unittest.TestCase):
    def test_health_polling_is_outside_analysis_rate_limiter(self) -> None:
        source = INSTALLER.read_text(encoding="utf-8")
        health = source.split("location = /api/health {", 1)[1].split(
            "location = /api/demo/run {", 1
        )[0]
        analysis = source.split("location = /api/demo/run {", 1)[1].split(
            "location /api/ {", 1
        )[0]
        self.assertNotIn("limit_req", health)
        self.assertIn("proxy_read_timeout 10s", health)
        self.assertIn(
            "limit_req zone=servicetracer_demo_api burst=4 nodelay",
            analysis,
        )
        self.assertIn("limit_req_status 429", analysis)
        self.assertIn("client_max_body_size 4k", analysis)
        self.assertNotIn("location /api/ {\n        limit_req", source)

    def test_unknown_api_paths_fail_closed(self) -> None:
        source = INSTALLER.read_text(encoding="utf-8")
        fallback = source.split("location /api/ {", 1)[1].split(
            "location / {", 1
        )[0]
        self.assertIn("return 404", fallback)

    def test_frontend_copy_separates_health_from_analysis(self) -> None:
        app = APP.read_text(encoding="utf-8")
        monitor = MONITOR.read_text(encoding="utf-8")
        self.assertIn("Controlled demo fixture — live analysis unavailable", app)
        self.assertIn("Controlled demo fixture — API health unavailable", app)
        self.assertIn(
            "Collector health was verified, but the live analysis request did not complete",
            app,
        )
        self.assertNotIn("Controlled demo fixture — API unavailable", app)
        self.assertIn("Health endpoint reachable", monitor)
        self.assertIn("Collector health and Azure identity verified", monitor)
        self.assertNotIn("Frontend ↔ governed collector API live", monitor)


if __name__ == "__main__":
    unittest.main()
'''
    test_path = ROOT / "infra/tests/test_collector_analysis_rate_limit_fix.py"
    test_path.write_text(test_source, encoding="utf-8")

    request = {
        "schema_version": "project.collector-analysis-rate-limit-fix.v1",
        "request_id": "collector-analysis-rate-limit-fix-20260727",
        "tracking_issue": 171,
        "status": "authorized_repository_repair",
        "authorized_by": "user instruction: Proceed",
        "recorded_on": "2026-07-27",
        "repository": {
            "name": "anthonyedgar30000/azure-iac-msp-lab",
            "base_branch": "main",
            "base_commit": "9e87a930f262a5af2ee16a05a4fa5ef4bf7f3d25",
            "working_branch": "fix/collector-analysis-rate-limit",
            "open_pull_requests_observed_before_change": 0,
            "local_working_tree": "not_observed_connector_backed_repository_changes",
        },
        "observed_browser_boundary": {
            "collector_health_and_identity_verified": True,
            "frontend_request_id_created": True,
            "accepted_correlation_proof": False,
            "fixture_fallback_used": True,
            "exact_http_failure_status": "not_observed",
        },
        "operational_authority": {
            "merge_after_exact_head_ci": True,
            "one_deployment_attempt": True,
            "one_browser_api_verification": True,
            "automatic_retry": False,
            "rollback": False,
            "scope_expansion": False,
        },
        "azure_scope": {
            "resource_group": "rg-servicetracer-dev-westus2",
            "location": "westus2",
            "collector_vm": "vm-stcollector-mst-dev",
            "collector_endpoint": "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run",
            "frontend_origin": "https://anthonyedgar30000.github.io",
            "new_resources_expected": 0,
            "quota_delta_expected": 0,
            "recurring_cost_delta_CAD_expected": 0,
        },
        "claim_boundaries": [
            "health_endpoint_reachable != live_analysis_completed",
            "repository_fix != deployed_fix",
            "deployment_succeeded != browser_path_verified",
            "failed_attempt != renewed_authority",
        ],
    }
    request_path = (
        ROOT
        / ".project/change-requests/collector-analysis-rate-limit-fix-20260727.json"
    )
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
