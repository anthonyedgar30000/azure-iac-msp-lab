import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class FrontendStatusChipTests(unittest.TestCase):
    def test_incident_chip_supports_explicit_healthy_state(self) -> None:
        app = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "docs" / "styles.css").read_text(encoding="utf-8")

        self.assertIn(
            "const INCIDENT_STATES = new Set(['neutral', 'healthy', 'warning']);",
            app,
        )
        self.assertIn("function setIncidentState(text, stateName = 'neutral')", app)
        self.assertNotIn("function setIncidentState(text, warning = false)", app)
        self.assertIn(
            "const resolvedState = INCIDENT_STATES.has(stateName) ? stateName : 'neutral';",
            app,
        )
        self.assertIn(
            "elements.incidentChip.classList.remove('status-neutral', 'status-healthy', 'status-warning');",
            app,
        )
        self.assertIn("elements.incidentChip.classList.add(`status-${resolvedState}`);", app)
        self.assertIn(".status-healthy {", styles)
        self.assertIn("background: var(--healthy-soft);", styles)
        self.assertIn("color: var(--healthy);", styles)

    def test_verified_ready_paths_render_healthy_not_neutral(self) -> None:
        app = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

        self.assertIn("setIncidentState('Live lab API ready', 'healthy');", app)
        self.assertIn("setIncidentState('Live Azure evidence captured', 'healthy');", app)
        self.assertIn("setIncidentState('Service verified', 'healthy');", app)
        self.assertIn("setIncidentState('Live report is stale', 'warning');", app)
        self.assertIn("setIncidentState('Report unavailable', 'warning');", app)


if __name__ == "__main__":
    unittest.main()
