from __future__ import annotations

import argparse
import json
import time
from typing import Any, Sequence
from urllib.parse import urlparse

from .client import build_client, create_response
from .config import AzureOpenAISettings


def _value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _jsonable(model_dump())
    return str(value)


def extract_output_text(response: Any) -> str:
    direct = _value(response, "output_text")
    if isinstance(direct, str):
        return direct

    text_parts: list[str] = []
    for item in _value(response, "output", []) or []:
        for content in _value(item, "content", []) or []:
            if _value(content, "type") == "output_text":
                text = _value(content, "text")
                if isinstance(text, str):
                    text_parts.append(text)
    return "".join(text_parts)


def build_execution_receipt(
    response: Any,
    settings: AzureOpenAISettings,
    *,
    latency_ms: int,
    max_output_tokens: int,
    reasoning_effort: str | None,
    prompt_classification: str,
) -> dict[str, Any]:
    parsed = urlparse(settings.base_url)
    return {
        "schema_version": "openai-azure-provider.execution-receipt.v1",
        "status": _value(response, "status", "completed"),
        "provider": "azure_openai_v1",
        "authentication": "microsoft_entra_token_provider",
        "endpoint": {
            "host": parsed.hostname,
            "path": parsed.path,
        },
        "deployment": settings.deployment,
        "response_id": _value(response, "id"),
        "model": _value(response, "model"),
        "output_text": extract_output_text(response),
        "usage": _jsonable(_value(response, "usage")),
        "latency_ms": latency_ms,
        "max_output_tokens": max_output_tokens,
        "reasoning_effort": reasoning_effort,
        "prompt_classification": prompt_classification,
        "api_key_used": False,
        "mcp_connection_configured": False,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Make one explicit Entra-authenticated Azure OpenAI Responses call."
    )
    parser.add_argument("--input", required=True, help="Bounded prompt text.")
    parser.add_argument("--max-output-tokens", type=int, default=128)
    parser.add_argument(
        "--reasoning-effort",
        choices=("minimal", "low", "medium", "high"),
        default="minimal",
    )
    parser.add_argument(
        "--prompt-classification",
        default="bounded_non_sensitive_demo",
    )
    parser.add_argument(
        "--expect-exact",
        help="Return exit code 2 unless output_text exactly matches this value.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = AzureOpenAISettings.from_env()
    client = build_client(settings)

    started = time.perf_counter()
    response = create_response(
        client,
        settings,
        args.input,
        max_output_tokens=args.max_output_tokens,
        reasoning_effort=args.reasoning_effort,
    )
    latency_ms = max(0, round((time.perf_counter() - started) * 1000))
    receipt = build_execution_receipt(
        response,
        settings,
        latency_ms=latency_ms,
        max_output_tokens=args.max_output_tokens,
        reasoning_effort=args.reasoning_effort,
        prompt_classification=args.prompt_classification,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))

    if args.expect_exact is not None and receipt["output_text"] != args.expect_exact:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
