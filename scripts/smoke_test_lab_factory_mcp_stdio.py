#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


EXPECTED_TOOLS = {
    "get_current_reality",
    "list_lab_profiles",
    "prepare_lab_request",
}
CALLED_TOOLS = ["list_lab_profiles", "prepare_lab_request", "prepare_lab_request"]
PROFILE_ID = "servicetracer-demo-api"
PROFILE_VERSION = "1.0.0"
REQUEST_ID = "lab-mcp-smoke-001"
SYNTHETIC_PARAMETERS = {
    "dnsLabel": "st-mcp-smoke-001",
    "allowedOrigin": "https://smoke.example.invalid",
    "backendTransactionUrl": "https://backend.example.invalid/transaction",
    "adminSshPublicKey": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAISmokeOnlyKey mcp-smoke",
    "sourceRepository": "https://github.com/anthonyedgar30000/azure-iac-msp-lab.git",
    "sourceRef": "0123456789abcdef0123456789abcdef01234567",
    "installerUri": (
        "https://raw.githubusercontent.com/anthonyedgar30000/azure-iac-msp-lab/"
        "0123456789abcdef0123456789abcdef01234567/"
        "workloads/servicetracer-demo-api/scripts/install.sh"
    ),
}


class SmokeTestError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def _repository_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    _require((root / "azure_mcp_reality/server.py").is_file(), "MCP server is missing")
    _require((root / "lab_factory/catalog.json").is_file(), "Lab Factory catalog is missing")
    return root


def _source_sha(root: Path) -> str:
    expected = os.environ.get("EXPECTED_SOURCE_SHA", "").strip()
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip()
    if expected:
        _require(actual == expected, "checked-out source does not match EXPECTED_SOURCE_SHA")
    return actual


def _safe_server_environment(root: Path) -> dict[str, str]:
    allowed = {
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "PYTHONIOENCODING",
        "PYTHONUNBUFFERED",
        "SYSTEMROOT",
        "TMP",
        "TEMP",
        "TMPDIR",
    }
    environment = {key: value for key, value in os.environ.items() if key in allowed}
    inherited_pythonpath = os.environ.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = (
        str(root)
        if not inherited_pythonpath
        else str(root) + os.pathsep + inherited_pythonpath
    )
    environment["PYTHONUNBUFFERED"] = "1"
    return environment


def _structured_payload(result: Any) -> dict[str, Any]:
    if bool(getattr(result, "isError", False)) or bool(getattr(result, "is_error", False)):
        messages = [
            block.text
            for block in getattr(result, "content", [])
            if isinstance(block, types.TextContent)
        ]
        raise SmokeTestError("MCP tool returned an error: " + " | ".join(messages))

    structured = getattr(result, "structuredContent", None)
    if structured is None:
        structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        if set(structured) == {"result"} and isinstance(structured["result"], dict):
            return structured["result"]
        return structured

    for block in getattr(result, "content", []):
        if not isinstance(block, types.TextContent):
            continue
        try:
            parsed = json.loads(block.text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise SmokeTestError("MCP tool did not return a structured JSON object")


def _assert_profile_list(payload: dict[str, Any]) -> None:
    _require(payload.get("schema_version") == "lab-factory.profile-list.v2", "profile-list schema mismatch")
    profiles = payload.get("profiles")
    _require(isinstance(profiles, list) and len(profiles) == 1, "unexpected profile inventory")
    profile = profiles[0]
    _require(profile.get("id") == PROFILE_ID, "profile id mismatch")
    _require(profile.get("version") == PROFILE_VERSION, "profile version mismatch")
    _require(profile.get("release_state") == "candidate", "profile release state mismatch")
    _require(profile.get("allowed_locations") == ["westus2"], "location allowlist mismatch")
    planner = profile.get("planner", {})
    _require(
        planner.get("workflow_path") == ".github/workflows/servicetracer-demo-api-subproject-plan.yml",
        "canonical planner workflow mismatch",
    )
    _require(planner.get("trigger") == "workflow_dispatch", "planner trigger mismatch")
    _require(planner.get("github_environment") == "azure-api-payg", "planner environment mismatch")
    _require(planner.get("subscription_boundary") == "dual_subscription", "subscription boundary mismatch")
    _require(planner.get("provider_validation_level") == "ProviderNoRbac", "provider validation mismatch")
    _require(planner.get("deployment_command_available") is False, "planner exposes deployment")
    _require(planner.get("live_dispatch_authorized") is False, "profile list granted dispatch")
    digest = planner.get("workflow_sha256")
    _require(isinstance(digest, str) and digest.startswith("sha256:") and len(digest) == 71, "workflow digest invalid")
    execution = payload.get("execution", {})
    _require(execution.get("azure_queries_performed") is False, "profile listing queried Azure")
    _require(execution.get("azure_mutations_performed") is False, "profile listing mutated Azure")
    _require(execution.get("workflow_dispatch_performed") is False, "profile listing dispatched workflow")


def _assert_prepared_plan(payload: dict[str, Any]) -> None:
    _require(payload.get("schema_version") == "lab-factory.plan.v1", "plan schema mismatch")
    request = payload.get("request", {})
    _require(request.get("request_id") == REQUEST_ID, "request id mismatch")
    _require(request.get("profile_id") == PROFILE_ID, "prepared profile mismatch")
    _require(request.get("profile_version") == PROFILE_VERSION, "prepared version mismatch")
    _require(request.get("location") == "westus2", "prepared location mismatch")
    _require(request.get("ttl_hours") == 8, "prepared TTL mismatch")
    _require(payload.get("next_gate") == "planner_dispatch_review_required", "unexpected next gate")
    deployment = payload.get("deployment", {})
    _require(deployment.get("operation") == "prepare_only", "operation is not prepare_only")
    _require(deployment.get("missing_required_parameters") == [], "required parameters remain missing")
    gates = payload.get("gates", {})
    _require(gates.get("ready_for_preflight") is True, "plan is not ready for bounded preflight")
    _require(gates.get("explicit_deployment_authorization_required") is True, "deployment authorization gate missing")
    planner = payload.get("planner", {})
    _require(planner.get("operation") == "prepare_only", "planner operation is not prepare_only")
    _require(
        planner.get("workflow_path") == ".github/workflows/servicetracer-demo-api-subproject-plan.yml",
        "planner workflow mismatch",
    )
    _require(planner.get("github_environment") == "azure-api-payg", "planner environment mismatch")
    _require(planner.get("subscription_boundary") == "dual_subscription", "planner subscription boundary mismatch")
    _require(planner.get("dependency_subscription_access") == "read_only", "dependency access mismatch")
    _require(planner.get("target_subscription_access") == "planning_only", "target access mismatch")
    _require(planner.get("provider_validation_level") == "ProviderNoRbac", "planner validation mismatch")
    _require(planner.get("arm_validation_required") is True, "ARM validation gate missing")
    _require(planner.get("arm_what_if_required") is True, "ARM What-If gate missing")
    _require(planner.get("deployment_command_available") is False, "planner exposes deployment command")
    _require(planner.get("ready_for_dispatch_review") is True, "planner is not ready for dispatch review")
    _require(planner.get("live_dispatch_authorized") is False, "planner granted live dispatch")
    _require(planner.get("parameter_values_returned") is False, "planner returned parameter values")
    _require(planner.get("confirmation_value_returned") is False, "planner returned confirmation value")
    execution = payload.get("execution", {})
    _require(execution.get("azure_queries_performed") is False, "prepare tool queried Azure")
    _require(execution.get("azure_mutations_performed") is False, "prepare tool mutated Azure")
    _require(execution.get("workflow_dispatch_performed") is False, "prepare tool dispatched workflow")
    _require(execution.get("deployment_authorized") is False, "prepare tool granted deployment authority")
    _require(execution.get("cleanup_authorized") is False, "prepare tool granted cleanup authority")
    serialized = json.dumps(payload, sort_keys=True)
    for value in SYNTHETIC_PARAMETERS.values():
        _require(value not in serialized, "a supplied parameter value was returned")
    digest = payload.get("plan_digest")
    _require(isinstance(digest, str) and digest.startswith("sha256:") and len(digest) == 71, "plan digest invalid")


async def _run_smoke(root: Path) -> dict[str, Any]:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "azure_mcp_reality.server", "--transport", "stdio"],
        env=_safe_server_environment(root),
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed_tools = await session.list_tools()
            tool_names = {tool.name for tool in listed_tools.tools}
            _require(tool_names == EXPECTED_TOOLS, "unexpected MCP tool inventory")

            profiles_result = await session.call_tool("list_lab_profiles", arguments={})
            profiles = _structured_payload(profiles_result)
            _assert_profile_list(profiles)

            arguments = {
                "profile_id": PROFILE_ID,
                "version": PROFILE_VERSION,
                "environment": "dev",
                "location": "westus2",
                "ttl_hours": 8,
                "request_id": REQUEST_ID,
                "parameters": SYNTHETIC_PARAMETERS,
            }
            first_result = await session.call_tool("prepare_lab_request", arguments=arguments)
            second_result = await session.call_tool("prepare_lab_request", arguments=arguments)
            first = _structured_payload(first_result)
            second = _structured_payload(second_result)
            _assert_prepared_plan(first)
            _assert_prepared_plan(second)
            _require(first == second, "identical MCP requests produced different plans")

    return {
        "tool_inventory": sorted(tool_names),
        "called_tools": CALLED_TOOLS,
        "profile": f"{PROFILE_ID}@{PROFILE_VERSION}",
        "profile_release_state": profiles["profiles"][0]["release_state"],
        "request_id": REQUEST_ID,
        "plan_digest": first["plan_digest"],
        "next_gate": first["next_gate"],
        "planner_workflow": first["planner"]["workflow_path"],
        "planner_subscription_boundary": first["planner"]["subscription_boundary"],
        "planner_dispatch_authorized": False,
        "parameter_values_returned": False,
        "azure_queries_performed": False,
        "azure_mutations_performed": False,
        "deployment_authorized": False,
        "cleanup_authorized": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bounded local stdio MCP Lab Factory smoke test.")
    parser.add_argument("--output", type=Path, help="Optional JSON receipt path.")
    parser.add_argument("--timeout-seconds", type=int, default=45)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = _repository_root()
    try:
        result = asyncio.run(asyncio.wait_for(_run_smoke(root), timeout=args.timeout_seconds))
        receipt = {
            "schema_version": "lab-factory.mcp-local-smoke-receipt.v2",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_sha": _source_sha(root),
            "transport": "stdio",
            "client_and_server_colocated": True,
            "remote_endpoint_used": False,
            "model_call_performed": False,
            "get_current_reality_called": False,
            "azure_environment_forwarded_to_server": False,
            **result,
            "status": "passed",
        }
    except (SmokeTestError, asyncio.TimeoutError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Lab Factory local MCP smoke test failed: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
