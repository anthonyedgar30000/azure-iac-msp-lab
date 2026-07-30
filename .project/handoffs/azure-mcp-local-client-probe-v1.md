# Azure MCP local Lab Factory client probe v1

## Terminal status

```text
protocol initialized: verified
transport: local stdio subprocess
exact probed source head: d2cd7e68a6dd954d5c114b827817a1d866827ca3
workflow run: 30505927462 / success
workflow job: 90755550858 / success
artifact: 8745291415
receipt SHA-256: 1f1cf91c47fdd347f835894b2ac8a7c9fb37552170cddbee7d1805740d54ab81
internal receipt digest: sha256:70f236ea8d17b96d8586845a96f2cff09e02fc08888c78554c3d41137a07de8f
parameter values promoted: false
Azure access performed: false
```

The exact-source artifact and its manifest are promoted at:

```text
.project/evidence/azure-mcp-local-client-probe.json
.project/evidence/azure-mcp-local-client-probe.sha256
```

## Objective

Verify the actual MCP protocol path for the two merged repository-only Lab Factory tools:

```text
MCP ClientSession
  -> local azure_mcp_reality.server subprocess
  -> list_lab_profiles
  -> prepare_lab_request
  -> sanitized digest-bearing receipt
```

This increment did not call `get_current_reality`, authenticate to Azure, query Azure, run ARM What-If, deploy, assign RBAC, call a model, expose a remote MCP endpoint, connect ChatGPT, or execute cleanup.

## Starting boundary

```text
repository: anthonyedgar30000/azure-iac-msp-lab
base main: 8926a5b48db9bb7cb08523d337e43d20ba7ed69d
latest merged PR at start: #220
open PRs before branch: none
branch: agent/verify-local-mcp-lab-factory-client-v1
pull request: #222
```

PR #218 had already merged the three-tool local MCP server. PR #220 correctly recorded that a live Lab Factory MCP client call was not yet observed. This work supplies that missing local protocol proof without widening Azure authority.

## Verified MCP session

The client initialized the MCP session and observed the exact advertised inventory:

```text
get_current_reality
list_lab_profiles
prepare_lab_request
```

It called only:

```text
list_lab_profiles
prepare_lab_request
```

Observed profile-list result:

```text
profile: servicetracer-demo-api
release state: candidate
Azure queries: false
Azure mutations: false
deployment authorized: false
cleanup authorized: false
```

Observed prepared request:

```text
profile: servicetracer-demo-api@1.0.0
environment: test
location: westus2
TTL: 6 hours
request id: local-mcp-probe-001
resource group: rg-st-demo-api-test-westus2
operation: prepare_only
missing required parameters: none
ready for preflight: true
ARM What-If required: true
explicit deployment authorization required: true
next gate: preflight_required
plan digest: sha256:4e9a858383ab78e2fef896421be4c65f122484394667d332bc6c0dea51e3bb71
```

Test-only parameter values were transmitted to the repository planner so the request could reach `preflight_required`. Hash and content inspection verified that none of those values appears in the receipt or promoted evidence.

## Security and authority controls

Before the subprocess started, Azure, ARM, OpenAI, managed-identity, and API-key environment variables were removed from its environment. The probe contains no Azure CLI command, OpenAI SDK client, Streamable HTTP client, workflow dispatcher, deployment command, or cleanup command.

```text
get_current_reality called: false
Azure credentials forwarded: false
Azure authentication performed: false
Azure query performed: false
ARM What-If performed: false
Azure mutation performed: false
deployment authorized: false
deployment performed: false
RBAC mutation performed: false
model call performed: false
remote MCP endpoint deployed: false
ChatGPT connection configured: false
cleanup authorized: false
cleanup performed: false
```

The presence of `get_current_reality` in the advertised inventory did not authorize calling it.

## Evidence provenance repairs

Three fail-closed issues were found and repaired before evidence promotion:

1. Full infrastructure CI does not install the optional MCP SDK. Imports were made lazy, and only the live protocol test skips there; the focused workflow installs the pinned SDK and executes the real call.
2. Pinned MCP SDK 1.24 exposes result aliases as `isError` and `structuredContent`. The probe now accepts those aliases and their snake-case counterparts.
3. GitHub's default pull-request checkout used a synthetic merge ref. The workflow now checks out `pull_request.head.sha` explicitly and rejects a receipt whose repository head differs.

The earlier synthetic-merge-ref artifact was not promoted.

## Claim boundary

```text
local MCP protocol call verified != ChatGPT connected
local MCP protocol call verified != remote MCP endpoint deployed
profile listed != released lab
prepared request != ARM What-If
prepared request != deployment authorized
allowed location != live capacity available
protocol call succeeded != Azure service validated
cleanup defined != cleanup verified
```

## Cost, failure, and rollback

```text
expected recurring Azure resource cost delta: CAD $0
model tokens consumed: 0
actual Azure cost freshly observed: false
Azure quota freshly observed: false
```

A protocol, inventory, schema, gate, digest, or redaction failure blocks merge and performs no cloud action. The subprocess is closed by the stdio context manager. Repository rollback is an exact revert or pull-request closure. No Azure rollback or cleanup applies.

## Next gate

Run final exact-head CI with the promoted evidence and terminal reconciliation. After merge, refresh the canonical repository watermark. A fresh Azure preflight—subscription, providers, region/SKU availability, quota, resource-group state, template validation, ARM What-If, and cost ceiling—remains a new separately authorized operation.
