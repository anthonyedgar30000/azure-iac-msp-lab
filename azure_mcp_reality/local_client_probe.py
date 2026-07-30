from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import mcp.types as types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOLS = [
    "get_current_reality",
    "list_lab_profiles",
    "prepare_lab_request",
]

_TEST_PARAMETERS = {
    "dnsLabel": "st-demo-api-mcp-probe-001",
    "allowedOrigin": "https://probe.example.invalid",
    "backendTransactionUrl": "https://backend.example.invalid/api/demo/run",
    "adminSshPublicKey": (
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIProtocolProbeOnlyKey local-mcp-probe"
    ),
    "sourceRepository": "https://github.com/anthonyedgar30000/azure-iac-msp-lab.git",
    "sourceRef": "0123456789abcdef0123456789abcdef01234567",
    "installerUri": (
        "https://raw.githubusercontent.com/anthonyedgar30000/"
        "azure-iac-msp-lab/0123456789abcdef0123456789abcdef01234567/"
        "workloads/servicetracer-demo-api/scripts/install.sh"
    ),
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.stdout.strip()


def _server_environment() -> dict[str, str]:
    """Build a subprocess environment with Azure and model credentials removed."""

    denied_prefixes = (
        "AZURE_",
        "ARM_",
        "OPENAI_",
        "MSI_",
        "IDENTITY_",
    )
    denied_exact = {
        "API_KEY",
        "OPENAI_API_KEY",
        "AZURE_OPENAI_API_KEY",
    }
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in denied_exact and not key.startswith(denied_prefixes)
    }
    existing_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT) + (
        os.pathsep + existing_pythonpath if existing_pythonpath else ""
    )
    return environment


def _structured_content(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured

    for block in getattr(result, "content", []):
        if isinstance(block, types.TextContent):
            try:
                parsed = json.loads(block.text)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    raise RuntimeError("MCP tool response did not contain structured JSON content")


def _require_false(mapping: dict[str, Any], *keys: str) -> None:
    for key in keys:
        if mapping.get(key) is not False:
            raise RuntimeError(f"expected {key}=false")


def _validate_profile_list(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "lab-factory.profile-list.v1":
        raise RuntimeError("unexpected profile-list schema")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or [item.get("id") for item in profiles] != [
        "servicetracer-demo-api"
    ]:
        raise RuntimeError("unexpected profile inventory")
    execution = payload.get("execution")
    if not isinstance(execution, dict):
        raise RuntimeError("profile-list execution boundary is missing")
    _require_false(
        execution,
        "azure_queries_performed",
        "azure_mutations_performed",
        "deployment_authorized",
        "cleanup_authorized",
    )


def _validate_prepared_plan(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "lab-factory.plan.v1":
        raise RuntimeError("unexpected prepared-plan schema")
    request = payload.get("request")
    deployment = payload.get("deployment")
    gates = payload.get("gates")
    execution = payload.get("execution")
    if not all(isinstance(item, dict) for item in (request, deployment, gates, execution)):
        raise RuntimeError("prepared-plan boundary objects are missing")
    if request != {
        "request_id": "local-mcp-probe-001",
        "profile_id": "servicetracer-demo-api",
        "profile_version": "1.0.0",
        "environment": "test",
        "location": "westus2",
        "ttl_hours": 6,
    }:
        raise RuntimeError("prepared request differs from the exact probe scope")
    if deployment.get("operation") != "prepare_only":
        raise RuntimeError("prepared request widened beyond prepare_only")
    if deployment.get("resource_group") != "rg-st-demo-api-test-westus2":
        raise RuntimeError("unexpected resource-group plan")
    if deployment.get("missing_required_parameters") != []:
        raise RuntimeError("prepared request is missing required parameters")
    if gates.get("ready_for_preflight") is not True:
        raise RuntimeError("prepared request did not reach the preflight gate")
    if gates.get("what_if_required") is not True:
        raise RuntimeError("ARM What-If gate was not preserved")
    if gates.get("explicit_deployment_authorization_required") is not True:
        raise RuntimeError("explicit deployment-authorization gate was not preserved")
    if payload.get("next_gate") != "preflight_required":
        raise RuntimeError("unexpected next gate")
    plan_digest = payload.get("plan_digest")
    if not isinstance(plan_digest, str) or not plan_digest.startswith("sha256:"):
        raise RuntimeError("prepared plan digest is missing")
    _require_false(
        execution,
        "azure_queries_performed",
        "azure_mutations_performed",
        "deployment_authorized",
        "cleanup_authorized",
    )
    serialized = _canonical_json(payload)
    for value in _TEST_PARAMETERS.values():
        if value in serialized:
            raise RuntimeError("prepared plan echoed a supplied parameter value")


async def run_probe() -> dict[str, Any]:
    repository_head = _git("rev-parse", "HEAD")
    working_tree_clean = _git("status", "--porcelain=v1", "--untracked-files=normal") == ""
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "azure_mcp_reality.server", "--transport", "stdio"],
        env=_server_environment(),
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            tool_names = sorted(tool.name for tool in listed.tools)
            if tool_names != sorted(EXPECTED_TOOLS):
                raise RuntimeError(f"unexpected MCP tool inventory: {tool_names}")

            profile_result = await session.call_tool("list_lab_profiles", arguments={})
            if profile_result.is_error:
                raise RuntimeError("list_lab_profiles returned an MCP tool error")
            profile_payload = _structured_content(profile_result)
            _validate_profile_list(profile_payload)

            prepare_result = await session.call_tool(
                "prepare_lab_request",
                arguments={
                    "profile_id": "servicetracer-demo-api",
                    "environment": "test",
                    "location": "westus2",
                    "ttl_hours": 6,
                    "version": "1.0.0",
                    "request_id": "local-mcp-probe-001",
                    "parameters": dict(_TEST_PARAMETERS),
                },
            )
            if prepare_result.is_error:
                raise RuntimeError("prepare_lab_request returned an MCP tool error")
            prepare_payload = _structured_content(prepare_result)
            _validate_prepared_plan(prepare_payload)

    initialized_payload = initialized.model_dump(by_alias=True, exclude_none=True)
    server_info = initialized_payload.get("serverInfo", {})
    receipt: dict[str, Any] = {
        "schema_version": "azure-mcp.local-client-probe.v1",
        "repository": {
            "head": repository_head,
            "working_tree_clean": working_tree_clean,
        },
        "transport": {
            "type": "stdio_subprocess",
            "server_module": "azure_mcp_reality.server",
            "network_listener_created": False,
            "remote_endpoint_used": False,
        },
        "protocol": {
            "initialized": True,
            "protocol_version": initialized_payload.get("protocolVersion"),
            "server_name": server_info.get("name"),
            "server_version": server_info.get("version"),
        },
        "tool_inventory": tool_names,
        "calls": {
            "list_lab_profiles": {
                "is_error": False,
                "schema_version": profile_payload["schema_version"],
                "profile_ids": [item["id"] for item in profile_payload["profiles"]],
                "release_states": [
                    item["release_state"] for item in profile_payload["profiles"]
                ],
                "execution": profile_payload["execution"],
            },
            "prepare_lab_request": {
                "is_error": False,
                "schema_version": prepare_payload["schema_version"],
                "request": prepare_payload["request"],
                "operation": prepare_payload["deployment"]["operation"],
                "resource_group": prepare_payload["deployment"]["resource_group"],
                "missing_required_parameters": prepare_payload["deployment"][
                    "missing_required_parameters"
                ],
                "ready_for_preflight": prepare_payload["gates"]["ready_for_preflight"],
                "what_if_required": prepare_payload["gates"]["what_if_required"],
                "explicit_deployment_authorization_required": prepare_payload["gates"][
                    "explicit_deployment_authorization_required"
                ],
                "next_gate": prepare_payload["next_gate"],
                "plan_digest": prepare_payload["plan_digest"],
                "execution": prepare_payload["execution"],
            },
        },
        "negative_evidence": {
            "get_current_reality_called": False,
            "azure_credentials_forwarded_to_server": False,
            "azure_authentication_performed": False,
            "azure_queries_performed": False,
            "azure_mutations_performed": False,
            "arm_what_if_performed": False,
            "deployment_authorized": False,
            "deployment_performed": False,
            "model_call_performed": False,
            "remote_mcp_endpoint_deployed": False,
            "chatgpt_connection_configured": False,
            "cleanup_authorized": False,
            "cleanup_performed": False,
        },
        "claim_boundaries": [
            "local_MCP_protocol_call_verified != ChatGPT_connected",
            "profile_listed != released_lab",
            "prepared_request != ARM_WhatIf",
            "prepared_request != deployment_authorized",
            "allowed_location != live_capacity_available",
            "parameter_values_transmitted_to_tool != parameter_values_returned",
        ],
    }
    receipt["receipt_digest"] = _digest(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Connect to the local MCP server over stdio and call only the repository-only "
            "Lab Factory list and prepare tools."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the sanitized JSON receipt to this path instead of stdout.",
    )
    args = parser.parse_args()

    try:
        receipt = asyncio.run(run_probe())
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": "azure-mcp.local-client-probe-error.v1",
                    "status": "failed",
                    "error": str(exc),
                    "azure_mutations_performed": False,
                    "deployment_performed": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
