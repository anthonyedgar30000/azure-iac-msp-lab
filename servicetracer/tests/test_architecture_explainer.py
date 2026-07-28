from __future__ import annotations

from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPOSITORY_ROOT / "docs"


class ServiceTracerArchitectureExplainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = (DOCS_ROOT / "index.html").read_text(encoding="utf-8")
        cls.styles = (DOCS_ROOT / "architecture.css").read_text(encoding="utf-8")

    def test_architecture_explainer_assets_are_linked(self) -> None:
        self.assertTrue((DOCS_ROOT / "architecture.css").is_file())
        self.assertIn('href="architecture.css"', self.index)
        self.assertIn('id="architecture-explainer"', self.index)
        self.assertIn('id="architecture-title"', self.index)
        self.assertIn("How ServiceTracer works", self.index)

    def test_golden_path_components_are_explicit(self) -> None:
        for expected in (
            "GitHub Pages frontend",
            "pip-st-demo-api-mst-dev",
            "lb-st-demo-api-mst-dev",
            "vm-stcollector-mst-dev · 10.20.40.10",
            "Nginx reverse proxy",
            "Python API · 127.0.0.1:8090",
            "lb-remote-access-mst-dev",
            "vm-vpn01-mst-dev",
            "vm-vpn02-mst-dev",
        ):
            self.assertIn(expected, self.index)

    def test_security_and_truth_boundaries_are_visible(self) -> None:
        for expected in (
            "Private application security boundary",
            "Mediated access only",
            "The collector has no directly attached public IP",
            "load_balancer_probe_healthy != complete_transaction_healthy",
            "resource_deployed != service_validated",
            "API_reachable != backend_dependency_healthy",
            "finding_localized != exact_root_cause_proven",
            "it does not manufacture runtime proof",
        ):
            self.assertIn(expected, self.index)

    def test_explainer_is_responsive_and_accessible(self) -> None:
        self.assertIn('aria-label="ServiceTracer request path', self.index)
        self.assertIn('aria-labelledby="architecture-title"', self.index)
        self.assertIn("@media (max-width: 980px)", self.styles)
        self.assertIn("@media (max-width: 760px)", self.styles)
        self.assertIn("grid-template-columns: 1fr", self.styles)


if __name__ == "__main__":
    unittest.main()
