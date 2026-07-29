from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from openai_azure_provider.client import create_response
from openai_azure_provider.config import AzureOpenAISettings
from openai_azure_provider.invoke import build_execution_receipt


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / ".project/contracts/openai-azure-foundry-provider-v2.json"
RECONCILIATION = (
    ROOT
    / ".project"
    / "reconciliations"
    / "azure-ai-go-live-run6-terminal-and-runtime-wire-20260729.json"
)
PROFILE = ROOT / "config/azure-openai-runtime.dev.sh"
HANDOFF = ROOT / ".project/handoffs/azure-ai-verified-runtime-wire-20260729.md"
DOC = ROOT / "docs/architecture/openai-azure-foundry-provider.md"
STATE_INDEX = ROOT / ".project/state-index.json"


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        return {"id": "response-test", **kwargs}


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class AzureAiVerifiedRuntimeWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
        cls.profile = PROFILE.read_text(encoding="utf-8")
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.state_index = json.loads(STATE_INDEX.read_text(encoding="utf-8"))

    def test_verified_runtime_contract_preserves_exact_evidence_boundary(self) -> None:
        self.assertEqual(
            self.contract["status"],
            "verified_runtime_wired_repository_candidate",
        )
        runtime = self.contract["verified_runtime"]
        self.assertEqual(
            runtime["base_url"],
            "https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/",
        )
        self.assertEqual(runtime["deployment_name"], "gpt-5-mini")
        self.assertEqual(runtime["response_status"], "completed")
        self.assertEqual(runtime["expected_output"], "AZURE ENTRA CONNECTED")
        self.assertEqual(runtime["usage"]["total_tokens"], 40)
        self.assertFalse(runtime["api_key_required_for_verified_path"])
        self.assertFalse(runtime["azure_mcp_connected"])
        self.assertEqual(
            self.contract["unknown_or_not_established"]["region"],
            "not_freshly_observed_for_verified_endpoint",
        )
        self.assertFalse(self.contract["authority"]["azure_mutation_authorized"])
        self.assertFalse(self.contract["authority"]["rbac_mutation_authorized"])

    def test_profile_is_sourceable_non_secret_and_exact(self) -> None:
        self.assertIn(
            "AZURE_OPENAI_BASE_URL='https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/'",
            self.profile,
        )
        self.assertIn("AZURE_OPENAI_MODEL_DEPLOYMENT='gpt-5-mini'", self.profile)
        self.assertIn("AZURE_OPENAI_MAX_RETRIES='0'", self.profile)
        lowered = self.profile.lower()
        self.assertNotIn("api_key=", lowered)
        self.assertNotIn("access_token=", lowered)
        self.assertNotIn("client_secret=", lowered)
        self.assertNotIn("subscription_id=", lowered)
        self.assertNotIn("tenant_id=", lowered)

    def test_create_response_supports_verified_bounded_reasoning_shape(self) -> None:
        settings = AzureOpenAISettings.from_env(
            {
                "AZURE_OPENAI_BASE_URL": (
                    "https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/"
                ),
                "AZURE_OPENAI_MODEL_DEPLOYMENT": "gpt-5-mini",
            }
        )
        client = FakeClient()
        result = create_response(
            client,
            settings,
            " Reply with exactly: AZURE ENTRA CONNECTED ",
            max_output_tokens=128,
            reasoning_effort="minimal",
        )
        self.assertEqual(result["model"], "gpt-5-mini")
        self.assertEqual(result["max_output_tokens"], 128)
        self.assertEqual(result["reasoning"], {"effort": "minimal"})
        self.assertEqual(len(client.responses.calls), 1)
        with self.assertRaises(ValueError):
            create_response(
                client,
                settings,
                "hello",
                reasoning_effort="unbounded",
            )

    def test_execution_receipt_is_non_secret_and_separates_mcp(self) -> None:
        settings = AzureOpenAISettings.from_env(
            {
                "AZURE_OPENAI_BASE_URL": (
                    "https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/"
                ),
                "AZURE_OPENAI_MODEL_DEPLOYMENT": "gpt-5-mini",
            }
        )
        response = SimpleNamespace(
            status="completed",
            id="response-observed",
            model="gpt-5-mini",
            output_text="AZURE ENTRA CONNECTED",
            usage=SimpleNamespace(
                model_dump=lambda: {
                    "input_tokens": 16,
                    "output_tokens": 24,
                    "total_tokens": 40,
                }
            ),
        )
        receipt = build_execution_receipt(
            response,
            settings,
            latency_ms=2500,
            max_output_tokens=128,
            reasoning_effort="minimal",
            prompt_classification="bounded_non_sensitive_demo",
        )
        self.assertEqual(receipt["status"], "completed")
        self.assertEqual(receipt["output_text"], "AZURE ENTRA CONNECTED")
        self.assertEqual(receipt["usage"]["total_tokens"], 40)
        self.assertFalse(receipt["api_key_used"])
        self.assertFalse(receipt["mcp_connection_configured"])
        encoded = json.dumps(receipt).lower()
        self.assertNotIn("access_token", encoded)
        self.assertNotIn("client_secret", encoded)

    def test_run6_and_verified_runtime_are_not_collapsed(self) -> None:
        terminal = self.reconciliation["run6_terminal"]
        runtime = self.reconciliation["verified_runtime"]
        reconciliation = self.reconciliation["reconciliation"]
        self.assertEqual(terminal["failure_stage"], "pre_mutation_what_if")
        self.assertFalse(terminal["deployment_started"])
        self.assertFalse(terminal["model_request_performed"])
        self.assertEqual(runtime["deployment"], "gpt-5-mini")
        self.assertEqual(runtime["request_status"], "completed")
        self.assertFalse(reconciliation["run6_target_matches_verified_runtime"])
        self.assertFalse(
            reconciliation["verified_runtime_retroactively_makes_run6_successful"]
        )

    def test_state_and_documentation_point_to_verified_runtime_wiring(self) -> None:
        self.assertIsNone(self.state_index["active_azure_ai_activation_authorization"])
        self.assertEqual(
            self.state_index["azure_ai_provider_contract"],
            ".project/contracts/openai-azure-foundry-provider-v2.json",
        )
        self.assertEqual(
            self.state_index["azure_ai_runtime_profile"],
            "config/azure-openai-runtime.dev.sh",
        )
        self.assertEqual(
            self.state_index["azure_ai_verified_deployment"],
            "gpt-5-mini",
        )
        self.assertFalse(self.state_index["azure_ai_mcp_connected"])
        self.assertIn("python -m openai_azure_provider.invoke", self.handoff)
        self.assertIn("AZURE ENTRA CONNECTED", self.handoff)
        self.assertIn("gpt-5-mini", self.doc)


if __name__ == "__main__":
    unittest.main()
