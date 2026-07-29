from __future__ import annotations

import json
from pathlib import Path
import unittest

from openai_azure_provider.client import build_client, create_response
from openai_azure_provider.config import (
    AzureOpenAISettings,
    ConfigurationError,
    DEFAULT_TOKEN_SCOPE,
)
from openai_azure_provider.plan import build_connection_plan


ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = ROOT / "requirements/openai-azure-provider.txt"
CONTRACT = (
    ROOT
    / ".project"
    / "contracts"
    / "openai-azure-foundry-provider-v1.json"
)


def valid_env() -> dict[str, str]:
    return {
        "AZURE_OPENAI_BASE_URL": (
            "https://example-resource.openai.azure.com/openai/v1/"
        ),
        "AZURE_OPENAI_MODEL_DEPLOYMENT": "gpt-demo",
    }


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        return {"id": "response-test", **kwargs}


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class AzureOpenAIProviderTests(unittest.TestCase):
    def test_valid_settings_are_normalized_and_fail_closed(self) -> None:
        settings = AzureOpenAISettings.from_env(valid_env())

        self.assertEqual(
            settings.base_url,
            "https://example-resource.openai.azure.com/openai/v1/",
        )
        self.assertEqual(settings.deployment, "gpt-demo")
        self.assertEqual(settings.token_scope, DEFAULT_TOKEN_SCOPE)
        self.assertEqual(settings.timeout_seconds, 30)
        self.assertEqual(settings.max_retries, 0)

    def test_services_ai_hostname_is_supported(self) -> None:
        environ = valid_env()
        environ["AZURE_OPENAI_BASE_URL"] = (
            "https://example-resource.services.ai.azure.com/openai/v1"
        )

        settings = AzureOpenAISettings.from_env(environ)

        self.assertEqual(
            settings.base_url,
            "https://example-resource.services.ai.azure.com/openai/v1/",
        )

    def test_unapproved_endpoint_shapes_are_rejected(self) -> None:
        invalid_urls = (
            "http://example-resource.openai.azure.com/openai/v1/",
            "https://example.invalid/openai/v1/",
            "https://user@example-resource.openai.azure.com/openai/v1/",
            "https://example-resource.openai.azure.com:8443/openai/v1/",
            "https://example-resource.openai.azure.com/openai/v1/?x=1",
            "https://example-resource.openai.azure.com/openai/v2/",
        )
        for invalid_url in invalid_urls:
            with self.subTest(invalid_url=invalid_url):
                environ = valid_env()
                environ["AZURE_OPENAI_BASE_URL"] = invalid_url
                with self.assertRaises(ConfigurationError):
                    AzureOpenAISettings.from_env(environ)

    def test_api_key_and_token_scope_override_are_rejected(self) -> None:
        api_key_env = valid_env()
        api_key_env["AZURE_OPENAI_API_KEY"] = "not-a-real-secret"
        with self.assertRaises(ConfigurationError):
            AzureOpenAISettings.from_env(api_key_env)

        scope_env = valid_env()
        scope_env["AZURE_OPENAI_TOKEN_SCOPE"] = "https://graph.microsoft.com/.default"
        with self.assertRaises(ConfigurationError):
            AzureOpenAISettings.from_env(scope_env)

    def test_retry_and_timeout_bounds_are_enforced(self) -> None:
        for key, value in (
            ("AZURE_OPENAI_MAX_RETRIES", "3"),
            ("AZURE_OPENAI_MAX_RETRIES", "-1"),
            ("AZURE_OPENAI_TIMEOUT_SECONDS", "0"),
            ("AZURE_OPENAI_TIMEOUT_SECONDS", "121"),
            ("AZURE_OPENAI_TIMEOUT_SECONDS", "not-an-int"),
        ):
            with self.subTest(key=key, value=value):
                environ = valid_env()
                environ[key] = value
                with self.assertRaises(ConfigurationError):
                    AzureOpenAISettings.from_env(environ)

    def test_client_construction_uses_entra_provider_without_network(self) -> None:
        settings = AzureOpenAISettings.from_env(valid_env())
        captured: dict[str, object] = {}
        fake_credential = object()

        def credential_factory(**kwargs: object) -> object:
            captured["credential_kwargs"] = kwargs
            return fake_credential

        def token_provider_factory(
            credential: object,
            scope: str,
        ):
            captured["credential"] = credential
            captured["scope"] = scope

            def token_provider() -> str:
                raise AssertionError("token provider must not be called during construction")

            return token_provider

        def client_factory(**kwargs: object) -> dict[str, object]:
            captured["client_kwargs"] = kwargs
            return {"constructed": True}

        client = build_client(
            settings,
            credential_factory=credential_factory,
            token_provider_factory=token_provider_factory,
            client_factory=client_factory,
        )

        self.assertEqual(client, {"constructed": True})
        self.assertEqual(
            captured["credential_kwargs"],
            {"exclude_interactive_browser_credential": True},
        )
        self.assertIs(captured["credential"], fake_credential)
        self.assertEqual(captured["scope"], DEFAULT_TOKEN_SCOPE)
        client_kwargs = captured["client_kwargs"]
        self.assertEqual(client_kwargs["base_url"], settings.base_url)
        self.assertEqual(client_kwargs["timeout"], 30)
        self.assertEqual(client_kwargs["max_retries"], 0)
        self.assertTrue(callable(client_kwargs["api_key"]))

    def test_response_execution_is_explicit_and_bounded(self) -> None:
        settings = AzureOpenAISettings.from_env(valid_env())
        client = FakeClient()

        result = create_response(
            client,
            settings,
            "  explain the observed drift  ",
            max_output_tokens=256,
        )

        self.assertEqual(result["model"], "gpt-demo")
        self.assertEqual(result["input"], "explain the observed drift")
        self.assertEqual(result["max_output_tokens"], 256)
        self.assertEqual(len(client.responses.calls), 1)

        with self.assertRaises(ValueError):
            create_response(client, settings, " ")
        with self.assertRaises(ValueError):
            create_response(client, settings, "hello", max_output_tokens=5000)

    def test_plan_is_non_secret_and_does_not_claim_execution(self) -> None:
        settings = AzureOpenAISettings.from_env(valid_env())
        plan = build_connection_plan(settings)
        encoded = json.dumps(plan).lower()

        self.assertFalse(plan["client_constructed"])
        self.assertFalse(plan["azure_authentication_performed"])
        self.assertFalse(plan["model_request_performed"])
        self.assertFalse(plan["mcp_connection_configured"])
        self.assertNotIn("api_key", encoded)
        self.assertNotIn("access_token", encoded)
        self.assertNotIn("client_secret", encoded)

    def test_contract_and_dependencies_preserve_repository_only_boundary(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        requirements = REQUIREMENTS.read_text(encoding="utf-8")

        self.assertEqual(
            contract["status"],
            "repository_only_provider_scaffold_candidate",
        )
        self.assertFalse(contract["execution"]["azure_authentication_performed"])
        self.assertFalse(contract["execution"]["model_request_performed"])
        self.assertFalse(contract["execution"]["mcp_connection_configured"])
        self.assertFalse(contract["authority"]["pull_request_merge_authorized"])
        self.assertFalse(contract["authority"]["azure_mutation_authorized"])
        self.assertFalse(contract["authority"]["openai_or_azure_model_call_authorized"])
        self.assertIn("openai==2.46.0", requirements)
        self.assertIn("azure-identity==1.25.3", requirements)


if __name__ == "__main__":
    unittest.main()
