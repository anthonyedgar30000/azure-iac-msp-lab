from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .config import AzureOpenAISettings


def build_client(
    settings: AzureOpenAISettings,
    *,
    credential: Any | None = None,
    credential_factory: Callable[..., Any] | None = None,
    token_provider_factory: Callable[[Any, str], Callable[[], str]] | None = None,
    client_factory: Callable[..., Any] | None = None,
) -> Any:
    """Construct an OpenAI SDK client for an Azure v1 endpoint.

    Construction is intentionally separate from execution. This function does not
    request a token or call a model by itself.
    """

    if credential_factory is None or token_provider_factory is None:
        from azure.identity import (  # type: ignore[import-not-found]
            DefaultAzureCredential,
            get_bearer_token_provider,
        )

        credential_factory = credential_factory or DefaultAzureCredential
        token_provider_factory = (
            token_provider_factory or get_bearer_token_provider
        )

    if client_factory is None:
        from openai import OpenAI  # type: ignore[import-not-found]

        client_factory = OpenAI

    active_credential = credential
    if active_credential is None:
        active_credential = credential_factory(
            exclude_interactive_browser_credential=True
        )

    token_provider = token_provider_factory(
        active_credential,
        settings.token_scope,
    )

    return client_factory(
        base_url=settings.base_url,
        api_key=token_provider,
        timeout=settings.timeout_seconds,
        max_retries=settings.max_retries,
    )


def create_response(
    client: Any,
    settings: AzureOpenAISettings,
    input_text: str,
    *,
    max_output_tokens: int = 600,
) -> Any:
    """Execute one explicit Responses API call through a supplied client."""

    prompt = input_text.strip()
    if not prompt:
        raise ValueError("input_text must not be empty")
    if not 1 <= max_output_tokens <= 4096:
        raise ValueError("max_output_tokens must be between 1 and 4096")

    return client.responses.create(
        model=settings.deployment,
        input=prompt,
        max_output_tokens=max_output_tokens,
    )
