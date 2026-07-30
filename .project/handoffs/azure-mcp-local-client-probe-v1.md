# Azure MCP local Lab Factory client probe v1

## Objective

Verify the actual MCP protocol path for the two merged repository-only Lab Factory tools:

```text
MCP stdio client
  -> local azure_mcp_reality.server subprocess
  -> list_lab_profiles
  -> prepare_lab_request
  -> sanitized digest-bearing receipt
```

This increment does not call `get_current_reality`, authenticate to Azure, query Azure, run ARM What-If, deploy, assign RBAC, call a model, expose a remote MCP endpoint, connect ChatGPT, or execute cleanup.

## Starting boundary

```text
repository: anthonyedgar30000/azure-iac-msp-lab
base main: 8926a5b48db9bb7cb08523d337e43d20ba7ed69d
latest merged PR: #220
open PRs before branch: none
branch: agent/verify-local-mcp-lab-factory-client-v1
```

PR #218 already merged the three-tool local MCP server. PR #220 records:

```text
get_current_reality: implemented / separately authorized Azure observer
list_lab_profiles: implemented / repository-only
prepare_lab_request: implemented / repository-only
Lab Factory live MCP client call observed: false
remote MCP endpoint deployed: false
ChatGPT connection verified: false
```

This work owns only the missing local protocol proof.

## Exact probe

The probe starts the local server over stdio using the current Python interpreter and performs an MCP initialize handshake. It requires the exact inventory:

```text
get_current_reality
list_lab_profiles
prepare_lab_request
```

It calls only:

```text
list_lab_profiles
prepare_lab_request
```

The prepared request is fixed to:

```text
profile: servicetracer-demo-api@1.0.0
environment: test
location: westus2
TTL: 6 hours
request id: local-mcp-probe-001
expected resource group: rg-st-demo-api-test-westus2
expected operation: prepare_only
expected next gate: preflight_required
```

Test-only parameter values are transmitted to the repository planner so the request can reach `preflight_required`. They must not appear in the returned plan, receipt, workflow logs, contract, handoff, or promoted evidence.

## Security and authority controls

Before the subprocess is started, Azure, ARM, OpenAI, managed-identity, and API-key environment variables are removed from the server environment. The probe contains no Azure CLI command, OpenAI SDK client, Streamable HTTP client, workflow dispatcher, deployment command, or cleanup command.

```text
Azure credentials forwarded: false
Azure authentication authorized: false
Azure query authorized: false
ARM What-If authorized: false
Azure mutation authorized: false
deployment authorized: false
RBAC mutation authorized: false
model call authorized: false
remote MCP deployment authorized: false
ChatGPT connection authorized: false
cleanup authorized: false
```

The presence of `get_current_reality` in the advertised tool inventory does not authorize calling it. The probe fails if its source contains a call to that tool.

## Required receipt evidence

The exact-head workflow must create:

```text
azure-mcp-local-client-probe.json
azure-mcp-local-client-probe.sha256
```

under a GitHub Actions artifact named:

```text
azure-mcp-local-client-probe
```

Required receipt claims:

```text
protocol initialized: true
transport: stdio_subprocess
network listener created: false
remote endpoint used: false
profile list returned: servicetracer-demo-api / candidate
prepared operation: prepare_only
prepared next gate: preflight_required
ARM What-If required: true
explicit deployment authorization required: true
Azure queries performed: false
Azure mutations performed: false
deployment authorized: false
parameter values returned: false
```

## Validation method

```bash
python -m pip install -r requirements/azure-mcp-reality-tool.txt
python -m unittest infra.tests.test_azure_mcp_local_client_probe -v
python -m azure_mcp_reality.local_client_probe \
  --output /tmp/azure-mcp-local-client-probe.json
sha256sum /tmp/azure-mcp-local-client-probe.json \
  > /tmp/azure-mcp-local-client-probe.sha256
```

The workflow has `id-token: none` and receives no Azure credentials. The receipt artifact is GitHub evidence only; it is not Azure runtime evidence.

## Failure, rollback, and cleanup

A handshake, inventory, tool-call, schema, gate, digest, or redaction failure fails CI and blocks merge. The local server process is closed by the MCP stdio context manager. Repository rollback is an exact revert or pull-request closure.

No Azure rollback or Azure cleanup is applicable because this increment has no Azure execution path.

## Cost

```text
expected recurring Azure resource cost delta: CAD $0
model tokens authorized: 0
actual Azure cost freshly observed: false
Azure quota freshly observed: false
```

## Next gate

After the first exact-head workflow succeeds, download and hash-verify the probe artifact, promote its sanitized receipt and manifest, record the exact source head and workflow run, and rerun exact-head CI. A successful local protocol call still does not authorize remote hosting, ChatGPT connection, Azure preflight, ARM What-If, deployment, service validation, RBAC, or cleanup.
