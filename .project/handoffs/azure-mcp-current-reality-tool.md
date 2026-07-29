# Azure MCP current-reality tool handoff

## Current state

The repository now contains the first governed MCP operational tool:

```text
name: get_current_reality
server: azure-mcp-reality/0.1.0
local stdio implemented: true
localhost Streamable HTTP implemented: true
local live execution observed: false
remote MCP endpoint deployed: false
Azure OpenAI MCP call verified: false
ChatGPT custom app connected: false
Azure mutation performed: false
```

The branch was created from exact `main` commit
`b2fdf35a1e11803209e7764e047f5112596005b9`, which merged PR #208. No open
pull requests were observed before branch creation.

## What the tool does

The tool observes one explicitly configured subscription and resource group and
the exact repository checkout. It can report:

- the Git commit and working-tree status;
- selected canonical `.project/` pointers;
- the enabled Azure subscription context as fingerprints;
- whether the exact resource group is present;
- bounded resource inventory;
- Azure Cognitive Services account deployment inventory;
- freshness, limitations, and a SHA-256 evidence digest.

It does not validate service health, backup recovery, alert firing, effective
least privilege, policy compliance, cost, quota, or application behavior.

## Scope boundary

Scope is supplied only by:

```text
AZURE_MCP_ALLOWED_SUBSCRIPTION_ID
AZURE_MCP_ALLOWED_RESOURCE_GROUP
AZURE_MCP_REPOSITORY_ROOT
```

The tool accepts no model-supplied parameters, does not infer the default Azure
subscription, and cannot discover across subscriptions.

## Security boundary

Only fixed `git` and read-only `az` commands are constructed. Commands are
executed as argument arrays with no shell. The tool returns fingerprints instead
of raw tenant and subscription IDs, redacts subscription IDs from ARM paths,
returns tag keys instead of values, sanitizes Azure metadata, and fails closed on
scope mismatch or oversized inventories.

The MCP annotations are:

```text
readOnlyHint=true
destructiveHint=false
idempotentHint=true
openWorldHint=true
```

These are hints. Enforcement comes from the code and scope contract.

## Preserved truth boundaries

```text
tool_implemented != tool_called
tool_called_locally != remote_endpoint_deployed
model_inference_verified != MCP_tool_call_verified
read_only_annotation != effective_least_privilege
resource_exists != securely_configured
evidence_collected != action_authorized
```

The existing Azure OpenAI `gpt-5-mini` Entra inference path remains verified and
separate. `azure_ai_mcp_connected` remains false.

## Validation

Ordinary CI must:

- install `mcp[cli]==1.24.0`;
- validate the v3 machine-readable contract;
- run observer and contract tamper tests;
- compile the package;
- build the FastMCP server without Azure access;
- confirm exactly one zero-input tool and the exact annotations;
- confirm no Azure credentials or scope variables exist in CI.

No Azure login or model call is part of CI.

## Cost

Expected recurring Azure resource cost delta from this increment: **CAD $0**.
Current Azure cost and quota were not freshly observed.

## Next operator gate

Do not deploy or tunnel the server yet. After merge, obtain a separate explicit
authorization for one local Cloud Shell execution using an exact subscription and
resource group. Preserve and inspect the structured receipt before considering:

1. remote Azure Container Apps hosting;
2. Entra OAuth client-to-server authentication;
3. managed identity server-to-Azure access;
4. exact remote tool-inventory verification;
5. one Azure OpenAI Responses API MCP call.
