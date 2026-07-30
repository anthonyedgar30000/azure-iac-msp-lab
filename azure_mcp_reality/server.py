from __future__ import annotations

import argparse
from typing import Any, Callable

from .azure_cli_compat import active_subscription_runner
from .config import RealitySettings
from .lab_factory_tools import (
    list_lab_profiles_payload,
    prepare_lab_request_payload,
)
from .observer import observe_current_reality


RealityToolHandler = Callable[[], dict[str, Any]]
ProfileListHandler = Callable[[], dict[str, Any]]
PrepareLabHandler = Callable[..., dict[str, Any]]


def _default_reality_tool_handler() -> dict[str, Any]:
    settings = RealitySettings.from_env()
    return observe_current_reality(
        settings,
        runner=active_subscription_runner,
    )


def build_server(
    *,
    tool_handler: RealityToolHandler | None = None,
    list_lab_profiles_handler: ProfileListHandler | None = None,
    prepare_lab_request_handler: PrepareLabHandler | None = None,
):
    """Build the local-only MCP server without starting network transport."""

    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

    reality_handler = tool_handler or _default_reality_tool_handler
    profile_handler = list_lab_profiles_handler or list_lab_profiles_payload
    prepare_handler = prepare_lab_request_handler or prepare_lab_request_payload
    server = FastMCP(
        name="Azure IaC MSP Lab Assistant",
        instructions=(
            "This server exposes one bounded Azure reality observer and two "
            "repository-only Azure Lab Factory planning tools. All tools are read-only. "
            "A prepared plan is not ARM What-If, deployment authority, service validation, "
            "or cleanup proof."
        ),
        stateless_http=True,
        json_response=True,
        host="127.0.0.1",
        port=8000,
        streamable_http_path="/mcp",
    )

    @server.tool(
        name="get_current_reality",
        title="Get current Azure lab reality",
        description=(
            "Observe one explicitly configured Azure subscription and resource group "
            "plus the exact local repository state. Performs fixed read-only Azure CLI "
            "and Git commands, returns sanitized structured evidence, and performs no mutation."
        ),
        annotations=ToolAnnotations(
            title="Get current Azure lab reality",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def get_current_reality() -> dict[str, Any]:
        return reality_handler()

    @server.tool(
        name="list_lab_profiles",
        title="List bounded Azure lab profiles",
        description=(
            "List versioned lab profiles from the repository catalog. Performs no Azure "
            "authentication, query, model call, deployment, or file write."
        ),
        annotations=ToolAnnotations(
            title="List bounded Azure lab profiles",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def list_lab_profiles() -> dict[str, Any]:
        return profile_handler()

    @server.tool(
        name="prepare_lab_request",
        title="Prepare an Azure lab request",
        description=(
            "Validate a request against one fixed catalog profile and return a deterministic "
            "prepare-only plan. Parameter values are validated but are not echoed. This tool "
            "does not query Azure, run ARM What-If, deploy resources, or authorize cleanup."
        ),
        annotations=ToolAnnotations(
            title="Prepare an Azure lab request",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def prepare_lab_request(
        profile_id: str,
        environment: str = "dev",
        location: str | None = None,
        ttl_hours: int | None = None,
        version: str | None = None,
        request_id: str | None = None,
        parameters: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return prepare_handler(
            profile_id=profile_id,
            environment=environment,
            location=location,
            ttl_hours=ttl_hours,
            version=version,
            request_id=request_id,
            parameters=parameters,
        )

    return server


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
    )
    args = parser.parse_args()

    server = build_server()
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
