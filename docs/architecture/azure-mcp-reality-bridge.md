# Azure MCP Reality Bridge — governed integration contract

## Status

This increment is **repository-only design and validation**.

```text
remote_endpoint_deployed = false
Azure_authentication_authorized = false
Azure_resource_creation_authorized = false
Entra_application_mutation_authorized = false
Azure_RBAC_mutation_authorized = false
ChatGPT_app_connected = false
OpenAI_API_execution_authorized = false
```

It creates no Azure resources, identities, role assignments, GitHub secrets, ChatGPT apps, or OpenAI API calls.

## Purpose

The bridge will give an authorized AI client a direct, evidence-bearing observation path into Azure while GitHub remains the declaration and change-control path.

```text
GitHub exact commit and CI
        +
Azure MCP time-bounded observations
        +
.project/ durable evidence boundaries
        ↓
Project Reality Synchronizer
        ↓
matched | drifted | unknown | conflicting | unverifiable
```

The bridge is not a new source of unquestioned truth. It is an observer whose identity, scope, tool inventory, freshness, and limitations must be recorded.

## Canonical distinctions

```text
mcp_endpoint_deployed != client_connected
tool_advertised != tool_authorized
read_only_annotation != effective_least_privilege
Azure_observed != repository_declared
authentication_succeeded != scope_authorized
resource_listed != service_validated
not_observed != absent
evidence_collected != action_authorized
```

## Current repository and Azure boundary

The repository was branched from observed `main` commit `92b0c3b1064158684a4b280348c77eeedba6dfc3`. No open pull request was observed immediately before branch creation.

The newest promoted Azure evidence in `.project/` remains historical workflow evidence. No Azure MCP endpoint, hosting resource group, region, identity, RBAC assignment, endpoint URL, tool inventory, or client connection is currently established by this increment.

The existing dual-subscription planner ratification gate remains independent and unresolved. This bridge does not ratify it, dispatch it, or authorize its administrative prerequisites.

## Intended architecture

Candidate architecture, pending a separate human decision:

```text
OpenAI Responses API or an approved MCP client
        |
        | OAuth access token / approved client authentication
        v
optional Azure API Management gateway
        |
        | TLS, JWT validation, rate limits, request logging,
        | tool exposure policy, correlation identifiers
        v
Azure MCP Server on Azure Container Apps
        |
        | selected identity model
        v
explicit Azure tenant, subscription, and resource scopes
```

Microsoft documents remote Azure MCP Server hosting on Azure Container Apps and remote MCP governance through Azure API Management. Remote MCP uses Streamable HTTP, conventionally at `/mcp`.

## Client availability boundary

There are three different client paths; they must not be collapsed:

1. **OpenAI Responses API** can call a remote MCP server using an MCP tool definition, an explicit server URL, an OAuth access token, an exact allowed-tools filter, and approval policy. This requires a separately configured and billed OpenAI API project.
2. **ChatGPT custom MCP apps** are plan- and workspace-dependent. A remote endpoint does not prove this ChatGPT account can register or use it.
3. **IDE MCP clients** such as supported GitHub Copilot, Visual Studio Code, or Cursor configurations can be used for bounded engineering validation, but an IDE connection is not a ChatGPT connection.

The project must verify the chosen client path before paying to host the endpoint.

## Authentication decision

No authentication model is selected yet.

### Candidate A — OAuth identity passthrough

The remote server operates with the signed-in user’s effective Azure permissions.

Benefits:

- preserves per-user accountability;
- avoids one shared Azure authority boundary;
- aligns observations with the human user’s effective access.

Risks and prerequisites:

- Entra server and client application design;
- OAuth scopes, redirect URIs, consent, token exchange, and client compatibility;
- accidental use of a user who has broader Azure permissions than the observation contract permits.

### Candidate B — shared managed identity

The server uses one managed identity with narrowly assigned Reader-style access.

Benefits:

- deterministic service identity;
- simpler audit and rotation than static credentials;
- easier to scope to specific subscriptions or resource groups.

Risks:

- all clients inherit the same service identity boundary;
- a broad role assignment silently broadens every client;
- the server can advertise write-capable tools even when RBAC blocks their execution.

### Selection rule

Choose the model only after recording:

- intended client;
- tenant;
- subscriptions and resource groups;
- required observation domains;
- administrator and consent requirements;
- cost;
- revocation path;
- proof that permissions are no broader than intended.

## Tool admission policy

The server’s complete tool catalog is **not** automatically authorized.

Initial requested observation domains are:

- subscription inventory;
- resource-group and resource inventory;
- activity logs;
- Azure Monitor logs and metrics;
- resource health;
- quota and usage;
- retail pricing and bounded cost observations;
- policy-assignment inventory;
- RBAC-assignment inventory;
- Advisor recommendations.

Every exact tool must pass all of these gates:

```text
exact server version captured
→ exact tool inventory captured
→ inventory digest recorded
→ read-only annotation present
→ destructive annotation false
→ secret annotation false
→ local-required annotation false
→ effective Azure RBAC reviewed
→ tenant/subscription/resource scope reviewed
→ exact tool name explicitly approved
```

Default subscription inference is forbidden. Every observation request must carry an explicit tenant and subscription, and resource-specific calls must carry an explicit resource group or resource ID.

Write, deployment, role-assignment, provider-registration, secret-value, guest-command, network-opening, policy-changing, and quota-changing capabilities remain denied.

## Network paths

The deployment design must document and verify:

- public or private ingress decision;
- TLS certificate source and renewal;
- client-to-gateway and gateway-to-server authentication;
- Container Apps ingress restrictions;
- outbound Azure control-plane access;
- diagnostic and correlation logging;
- whether API Management is justified by governance needs and cost.

A public URL without authentication, rate limits, and tool admission is prohibited.

## Security controls

Required before connection:

- no anonymous access;
- no long-lived static Azure credential;
- explicit tenant and subscription allowlists;
- least-privilege Azure RBAC;
- exact MCP tool allowlist;
- secret-bearing tools excluded;
- prompt-injection treatment for all tool output;
- request and result correlation IDs;
- redaction before evidence persistence;
- no raw protected evidence committed to Git;
- fail closed on tool-catalog changes.

MCP output is untrusted input. It may contain resource metadata or log content influenced by external actors. The reasoning layer must not treat tool output as instructions.

## Cost implications

Costs are not yet observed. Candidate costs include:

- Azure Container Apps compute and networking;
- Log Analytics or Application Insights ingestion;
- optional API Management tier;
- egress and DNS/certificate services;
- OpenAI API usage if the Responses API client path is selected.

The project must capture a current estimate and define a monthly ceiling before deployment. API Management must not be added merely because it is architecturally tidy; its governance value must justify its cost.

## Deployment method

No deployment is authorized by this PR.

A later deployment increment should:

1. select client, authentication model, tenant, subscriptions, scopes, region, and cost ceiling;
2. pin an exact Azure MCP Server release or immutable image digest;
3. pin enabled namespaces or tool exposure;
4. produce Bicep or an inspected `azd` template;
5. run lint, build, ARM validation, and What-If;
6. require explicit deployment authority for the exact reviewed commit;
7. deploy;
8. capture endpoint, identity, RBAC, version, inventory, and cost evidence;
9. keep all tools disabled until exact admission review is complete.

Portal-only consent or app-registration steps must be recorded and later evaluated for codification.

## Validation commands

Repository-only checks introduced by this increment:

```bash
python scripts/validate_azure_mcp_reality_bridge.py
python -m unittest tests/test_azure_mcp_reality_bridge.py -v
```

Future deployed verification must additionally prove:

- TLS and `/mcp` reachability;
- expected OAuth metadata or managed-identity path;
- exact tenant and subscription resolution;
- exact server version;
- exact tool inventory and digest;
- denied tools cannot be called;
- allowed observations return provenance and freshness;
- no write activity appears in Azure Activity Log;
- disabling the client or identity immediately removes access.

## Expected evidence

A future evidence package should include, with secrets removed:

```text
azure-mcp-deployment-manifest.json
azure-mcp-server-version.json
azure-mcp-tool-inventory.json
azure-mcp-tool-inventory.sha256
azure-mcp-client-path.json
azure-mcp-authentication-observation.json
azure-mcp-effective-rbac.json
azure-mcp-scope-allowlist.json
azure-mcp-read-only-verification.json
azure-mcp-activity-log-verification.json
azure-mcp-cost-observation.json
azure-mcp-rollback-verification.json
```

Every observation must identify time, tenant, subscription, scope, server version, tool name, correlation ID, result status, limitations, and raw-evidence digest.

## Failure and rollback

Fail closed when:

- the tool inventory or annotations change;
- tenant, subscription, or resource scope differs from the approved allowlist;
- identity cannot be proven;
- a write, secret, or local-only capability appears;
- evidence provenance or digest is missing;
- tool output attempts to redirect the model’s instructions.

Rollback order:

1. disable the client connection;
2. revoke or remove OAuth/federated access;
3. disable external endpoint ingress;
4. preserve redacted logs and evidence;
5. assess whether endpoint resources should be removed;
6. perform deletion only under separate cleanup authorization.

Disabling access is rollback. Resource deletion is cleanup and requires separate authority.

## Cleanup

This increment creates only repository files. Its rollback is to close or revert the PR.

A future Azure deployment must provide a complete decommission procedure for Container Apps, API Management, identities, app registrations, role assignments, DNS, monitoring, and retained logs. No cleanup is pre-authorized.

## Source anchors

- Microsoft Learn: Azure MCP Server documentation and tool catalog.
- Microsoft Learn: remote Azure MCP Server deployment on Azure Container Apps, including managed-identity and on-behalf-of patterns.
- Microsoft Learn: Azure API Management remote MCP support and MCP security controls.
- OpenAI documentation: remote MCP tools in the Responses API.
- OpenAI Help Center: developer mode and custom MCP app availability and controls in ChatGPT.

These sources are implementation inputs, not deployment evidence. Their current behavior must be rechecked at the time of deployment.
