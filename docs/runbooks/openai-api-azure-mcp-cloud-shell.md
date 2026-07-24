# OpenAI Responses API to Azure MCP — Cloud Shell runbook

## Purpose

Prepare, review, and eventually deploy a remote Azure MCP Server for an OpenAI Responses API client without treating a convenient Cloud Shell command as unlimited authority.

The selected architecture is:

```text
OpenAI Responses API client
→ Entra OAuth access token
→ HTTPS Streamable HTTP /mcp
→ Azure MCP Server on Azure Container Apps
→ user-assigned managed identity
→ explicitly bounded Azure read scope
```

The current increment stops before Azure provisioning.

## Current reality

Repository baseline:

```text
main = df0458a4d0a9075787726a3205c6c7b454cfa15e
PR #78 source = cc6d2c2b4a238d22f2ab56f68a0722d3f9f1423a
PR #78 exact-head CI = 30072601791
open pull requests observed = none
```

Azure MCP runtime:

```text
endpoint deployed = false
endpoint URL = null
managed identity created = false
Entra applications created = false
RBAC changed = false
tool inventory observed = false
allowed tools = []
OpenAI API execution = false
```

The ServiceTracer planner conflict remains separate: current code declares `westus2 / Standard_F1als_v7`, while the latest protected Azure evidence is the older `eastus / Standard_B2ats_v2` run. Neither is evidence that Azure MCP hosting exists.

## Official behavior that shapes the plan

Microsoft documents remote Azure MCP hosting on Azure Container Apps. The managed-identity reference template grants the server identity Subscription Reader and enables the storage namespace by default. The template must therefore be inspected and narrowed before use:

- https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/how-to/deploy-remote-mcp-server-copilot-studio
- https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/

Azure MCP Server supports `--read-only`, namespace filtering, specific-tool exposure, and multiple server modes. Read-only annotations and flags are defense layers, not substitutes for effective least-privilege RBAC.

OpenAI remote MCP tools accept a `server_url`, OAuth `authorization`, `allowed_tools`, and `require_approval`. The application, not the model, must complete OAuth and provide the token:

- https://platform.openai.com/docs/api-reference/responses

## Phase 1 — reviewable Cloud Shell preflight

Do not put subscription IDs, tenant IDs, access tokens, client secrets, or OpenAI API keys in GitHub or chat.

In Azure Cloud Shell, set explicit values:

```bash
export AZURE_MCP_HOSTING_SUBSCRIPTION_ID='<exact-subscription-uuid>'
export AZURE_MCP_LOCATION='<proposed-region>'
export AZURE_MCP_RESOURCE_GROUP='<dedicated-resource-group>'
export AZURE_MCP_TEMPLATE='azmcp-copilot-studio-aca-mi'
```

After this package is merged and its exact commit is reviewed, download the script from that immutable commit, inspect it, and run it:

```bash
curl -fsSL \
  'https://raw.githubusercontent.com/anthonyedgar30000/azure-iac-msp-lab/<exact-reviewed-commit>/scripts/azure_mcp_cloud_shell_preflight.sh' \
  -o azure_mcp_cloud_shell_preflight.sh

sha256sum azure_mcp_cloud_shell_preflight.sh
less azure_mcp_cloud_shell_preflight.sh
bash azure_mcp_cloud_shell_preflight.sh
```

The script performs only:

- account-context observation against the explicit subscription;
- location-catalog verification;
- provider registration-state observation;
- typed resource-group observation;
- existing resource summary when the resource group exists;
- local template download through `azd init`;
- template file hashing;
- static risk scanning.

It does not register providers, create a resource group, create identities, assign roles, provision Container Apps, run the OpenAI API, or perform cleanup.

## Required evidence

Preserve the generated evidence directory privately. Share only redacted content:

```text
account-context.json
provider-states.json
resource-group-state.json
existing-resource-summary.json
template-files.sha256
template-risk-scan.txt
preflight-summary.json
```

Expected success:

```text
subscription matches the explicit input
subscription is Enabled
location exists in the subscription catalog
provider states are observed or typed observation_failed
resource group is observed, not_present, or observation_failed
template manifest digest is produced
Azure mutations performed = false
deployment performed = false
```

## Failure behavior

Stop without provisioning when:

- the subscription does not match;
- the subscription is disabled;
- the location is invalid;
- an Azure observation fails ambiguously;
- the template cannot be downloaded;
- template hashing or risk scanning fails.

`observation_failed` must not be converted to `not_present`.

Rollback for this phase is deletion of the Cloud Shell working directory only.

## Phase 2 — mandatory template review

Before deployment, record and approve:

1. exact template source commit and manifest digest;
2. exact Azure MCP container image version or digest;
3. resources and Entra objects the template creates;
4. requested API scopes and redirect URIs;
5. managed-identity RBAC assignments and their exact scope;
6. Azure MCP server mode;
7. namespace allowlist;
8. `--read-only` enforcement;
9. secret-returning and local-only tool exclusion;
10. cost estimate, budget ceiling, regional availability, and quota;
11. cleanup coverage, including Entra objects that `azd down` may not remove.

The first deployment should not use subscription-wide Reader unless a separate review accepts that scope. Prefer exact resource-group scope.

## Phase 3 — separate deployment authorization

The Azure mutation point is the template provisioning operation. It is not authorized by this runbook or by merging its pull request.

A future authorization must bind:

```text
exact main commit
exact template manifest digest
exact container image version
hosting subscription fingerprint
tenant fingerprint
region
resource group
managed identity
RBAC role and scope
namespace allowlist
server read-only setting
monthly cost ceiling
rollback and cleanup procedure
```

Only after that gate may the provisioning command be supplied and run.

## Phase 4 — post-deployment validation

A successful deployment is not a validated integration. Capture:

- Container App provisioning state;
- TLS endpoint and exact `/mcp` URL;
- Entra resource and token audience;
- managed-identity principal fingerprint;
- effective RBAC at the approved scope;
- Azure MCP version and image digest;
- live tool inventory and annotations;
- tool inventory digest;
- evidence that write, secret, and local-only tools are unavailable;
- Application Insights or equivalent telemetry;
- endpoint disable and rollback test.

## Phase 5 — OpenAI client gate

The first OpenAI request should use:

```text
server_url = exact HTTPS /mcp endpoint
authorization = short-lived Entra OAuth access token
allowed_tools = exact approved names
require_approval = always
```

Keep the OpenAI API key in a secret store or server-side environment variable. Never put it in Cloud Shell history, source code, browser code, screenshots, evidence artifacts, or chat.

The first end-to-end proof should reconcile one known Azure resource against one exact Git commit and record provenance, freshness, scope, limitations, and evidence digests.

## Cleanup

Cleanup requires separate authorization. It must account for:

- Container App and environment;
- managed identity;
- role assignments;
- Log Analytics and Application Insights;
- resource group;
- Entra client and server applications;
- federated credentials and API permissions;
- OpenAI client configuration and stored tokens.

`azd down` coverage must be verified rather than assumed.
