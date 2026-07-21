from __future__ import annotations

import json
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = REPOSITORY_ROOT / "docs"


class ServiceTracerVisualDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = (DEMO_ROOT / "index.html").read_text(encoding="utf-8")
        cls.styles = (DEMO_ROOT / "styles.css").read_text(encoding="utf-8")
        cls.javascript = (DEMO_ROOT / "app.js").read_text(encoding="utf-8")
        cls.report_text = (DEMO_ROOT / "technician-handoff-report.json").read_text(
            encoding="utf-8"
        )
        cls.report = json.loads(cls.report_text)
        cls.source_config = json.loads(
            (DEMO_ROOT / "report-source.json").read_text(encoding="utf-8")
        )

    def test_static_demo_files_exist(self) -> None:
        for filename in (
            "index.html",
            "styles.css",
            "app.js",
            "report-source.json",
            "technician-handoff-report.json",
        ):
            self.assertTrue((DEMO_ROOT / filename).is_file(), filename)

    def test_demo_preserves_bounded_investigation_contract(self) -> None:
        self.assertEqual(
            self.report["load_balancer"]["status"],
            "healthy_under_configured_probe",
        )
        self.assertEqual(
            self.report["localization"]["suspect_backend"],
            "VPN-02",
        )
        self.assertEqual(
            self.report["localization"]["healthy_comparison_backend"],
            "VPN-01",
        )
        self.assertEqual(
            self.report["investigation_boundary"]["service_tracer_stops_at"],
            "VPN-02",
        )
        self.assertFalse(
            self.report["investigation_boundary"]["exact_root_cause_claimed"]
        )
        self.assertEqual(
            self.report["root_cause"]["status"],
            "not_determined_by_servicetracer",
        )

    def test_visual_report_does_not_expose_deeper_diagnosis(self) -> None:
        rendered = self.report_text.lower()
        self.assertNotIn("radius_response", rendered)
        self.assertNotIn("shared secret", rendered)
        self.assertNotIn("root cause is", rendered)

    def test_demo_contains_the_manual_technician_sequence(self) -> None:
        step_ids = [step["step_id"] for step in self.report["technician_workflow"]]
        self.assertEqual(
            step_ids,
            [
                "temporary-user-reroute",
                "manual-backend-troubleshooting",
                "controlled-test-user-validation",
                "original-user-return",
            ],
        )

    def test_page_has_operator_controls_and_report_provenance(self) -> None:
        for expected in (
            'id="run-analysis"',
            'id="reset-demo"',
            'id="incident-chip"',
            'id="report-source-name"',
            'id="report-source-detail"',
            'aria-live="polite"',
            'id="workflow-list"',
            'src="app.js"',
            'href="styles.css"',
        ):
            self.assertIn(expected, self.index)

    def test_javascript_supports_live_report_and_bounded_fallback(self) -> None:
        self.assertEqual(
            self.source_config["schema_version"],
            "servicetracer.report-source.v1",
        )
        self.assertEqual(self.source_config["live_report_url"], "")
        self.assertEqual(
            self.source_config["fallback_report_url"],
            "technician-handoff-report.json",
        )
        for expected in (
            "servicetracer.public-report.v1",
            "report-source.json",
            "live_report_url",
            "fallback_report_url",
            "exact_root_cause_claimed !== false",
            "Live report is stale",
            "new URLSearchParams(window.location.search).get('report')",
        ):
            self.assertIn(expected, self.javascript)
        self.assertIn("ServiceTracer", self.index)
        self.assertIn("prefers-reduced-motion", self.styles)


if __name__ == "__main__":
    unittest.main()
