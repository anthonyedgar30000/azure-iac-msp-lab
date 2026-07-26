from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "collector-provenance-preflight.yml"
SUMMARIZER = ROOT / "infra" / "scripts" / "summarize_cost_management_query.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CollectorProvenancePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summarizer = load_module(SUMMARIZER, "cost_summarizer")

    def test_script_compiles(self):
        py_compile.compile(str(SUMMARIZER), doraise=True)

    def test_workflow_is_exact_source_bound_and_read_only(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("reviewed_commit", workflow)
        self.assertIn("COLLECTOR-PROVENANCE-PREFLIGHT:", workflow)
        self.assertIn("azure_queries_authorized:true", workflow)
        self.assertIn("azure_mutations_authorized:false", workflow)
        self.assertIn("deployment_authorized:false", workflow)
        self.assertIn("az account show", workflow)
        self.assertIn("az network list-usages", workflow)
        self.assertIn("az vm list-usage", workflow)
        self.assertIn("az lock list", workflow)
        self.assertIn("Microsoft.CostManagement/query?api-version=2023-11-01", workflow)
        self.assertIn("--result-format FullResourcePayloads", workflow)
        self.assertIn("assert_collector_demo_api_what_if.py", workflow)
        self.assertIn("summarize_cost_management_query.py", workflow)
        self.assertNotIn("az deployment group create", workflow)
        self.assertNotIn("inputs.operation", workflow)
        self.assertNotIn("transaction replay", workflow.lower())

    def test_workflow_does_not_persist_raw_subscription_or_tenant_ids(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("subscription-id.sha256", workflow)
        self.assertIn("tenant-id.sha256", workflow)
        self.assertIn("raw_identifiers_persisted:false", workflow)
        self.assertNotIn("subscriptionId:id", workflow)
        self.assertNotIn("tenantId:tenantId", workflow)

    def test_summarizer_records_observed_cost_and_currency(self):
        payload = {
            "properties": {
                "columns": [
                    {"name": "PreTaxCost", "type": "Number"},
                    {"name": "Currency", "type": "String"},
                ],
                "rows": [[0.5, "CAD"], [0.25, "CAD"]],
            }
        }

        result = self.summarizer.summarize(payload, scope="resource_group")

        self.assertEqual(result["observation_status"], "observed")
        self.assertEqual(result["amount"], 0.75)
        self.assertEqual(result["currency"], "CAD")
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(
            result["boundary"],
            "observed_month_to_date_cost != remaining_credit",
        )

    def test_summarizer_preserves_failed_query_as_not_observed(self):
        result = self.summarizer.summarize(
            None,
            scope="subscription",
            unavailable_reason="cost_management_query_failed_or_not_authorized",
        )

        self.assertEqual(result["observation_status"], "not_observed")
        self.assertIsNone(result["amount"])
        self.assertIsNone(result["currency"])
        self.assertEqual(result["boundary"], "not_observed != zero_cost")

    def test_summarizer_does_not_collapse_empty_rows_to_zero(self):
        payload = {
            "properties": {
                "columns": [
                    {"name": "PreTaxCost", "type": "Number"},
                    {"name": "Currency", "type": "String"},
                ],
                "rows": [],
            }
        }

        result = self.summarizer.summarize(payload, scope="subscription")

        self.assertEqual(result["observation_status"], "not_observed")
        self.assertEqual(result["reason"], "cost_management_returned_no_rows")
        self.assertIsNone(result["amount"])

    def test_credit_balance_is_explicitly_separate_from_cost(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("month_to_date_cost != remaining_credit", workflow)
        self.assertIn(
            "remaining_credit_requires_a_separate_supported_sponsorship_or_billing_scope",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
