from __future__ import annotations

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
        self.assertNotIn("location /api/ {
        limit_req", source)

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
