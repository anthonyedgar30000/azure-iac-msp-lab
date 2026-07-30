# Local Lab Factory MCP smoke test

## Purpose

Prove that a real MCP client can start the repository server over local `stdio`, discover the admitted tool inventory, call only the two repository-only Lab Factory tools, and receive a deterministic prepare-only plan.

This runbook does not authenticate to Azure and does not call `get_current_reality`.

```text
local MCP implementation != local MCP client call verified
local MCP client call verified != ChatGPT connected
prepared request != ARM What-If
prepared request != deployment authorized
profile location allowlist != live Azure capacity
```

## Scope

The smoke test calls exactly:

```text
list_lab_profiles
prepare_lab_request
prepare_lab_request
```

The second `prepare_lab_request` call repeats the first request to prove deterministic output.

The client must not call:

```text
get_current_reality
```

## Dependencies

- Python 3.12
- `mcp[cli]==1.24.0` from `requirements/azure-mcp-reality-tool.txt`
- repository checkout at the exact source under review
- no Azure credential or OpenAI API key in the test environment

## Local execution

From the repository root:

```bash
python -m pip install -r requirements/azure-mcp-reality-tool.txt
python scripts/smoke_test_lab_factory_mcp_stdio.py \
  --output /tmp/lab-factory-mcp-local-smoke-receipt.json
```

The script starts this server subprocess:

```bash
python -m azure_mcp_reality.server --transport stdio
```

The server process receives a deliberately reduced environment. Azure and model credentials are not forwarded.

## Expected result

The command exits with status `0` and emits a JSON receipt containing:

```text
status: passed
transport: stdio
client_and_server_colocated: true
remote_endpoint_used: false
get_current_reality_called: false
model_call_performed: false
profile: servicetracer-demo-api@1.0.0
profile_release_state: candidate
next_gate: preflight_required
parameter_values_returned: false
azure_queries_performed: false
azure_mutations_performed: false
deployment_authorized: false
cleanup_authorized: false
```

The receipt includes the exact source SHA and deterministic plan digest. It does not include supplied parameter values.

## CI execution

`.github/workflows/lab-factory-mcp-local-smoke.yml` performs the same test on a GitHub-hosted runner. It checks out the exact pull-request source head rather than the synthetic merge ref, installs the pinned SDK, verifies that Azure and model credentials are absent, runs the smoke client, validates the receipt, and uploads the receipt as a bounded workflow artifact.

The workflow has:

```text
contents: read
id-token: none
workflow_dispatch: absent
Azure login: absent
```

## Failure handling

The test fails closed when:

- the MCP server cannot initialize;
- the tool inventory differs from the exact three-tool set;
- either Lab Factory tool returns an MCP error;
- the profile or version differs from the catalog expectation;
- a supplied parameter value is echoed;
- identical requests produce different plans;
- the plan claims an Azure query, mutation, deployment authorization, or cleanup authorization;
- the checked-out source differs from `EXPECTED_SOURCE_SHA`;
- the operation exceeds the bounded timeout.

Stop the local process and inspect stderr. No Azure rollback or cleanup is required because the test creates no Azure resources and performs no Azure query or mutation.

## Evidence boundary

A passing receipt establishes a local MCP protocol round trip for the two repository-only planning tools at one exact source revision.

It does not establish:

- a remote MCP endpoint;
- ChatGPT connectivity;
- Azure OpenAI MCP invocation;
- current Azure subscription, quota, SKU, policy, RBAC, or cost state;
- ARM What-If acceptance;
- deployment success;
- service validation;
- cleanup verification.
