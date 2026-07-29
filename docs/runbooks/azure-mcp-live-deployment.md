# Runbook: Azure MCP live deployment

## Before dispatch

Confirm the implementation pull request and its exact-head CI are green, the authorization request is active, and no other branch has changed the deployment workflow or Bicep after the request's `reviewed_source`.

Confirm the protected `azure-lab` environment identity has:

- Azure permission to create resources and role assignments at the exact authorized scopes;
- Microsoft Graph application permission `Application.ReadWrite.All`;
- the existing GitHub OIDC federation used by prior successful read-only preflight runs.

The workflow verifies these prerequisites before provider registration or deployment.

## Dispatch inputs

Use **Actions → Azure MCP live deployment → Run workflow** on `main`.

```text
request_path: .project/deployment-requests/azure-mcp-live-run1.json
confirmation: DEPLOY-AZURE-MCP-LIVE:<request-id-from-the-request-file>
```

Never use **Re-run**. A second attempt is not authorized and the durable claim must reject it.

## Expected mutations

- register `Microsoft.App` if not already registered;
- create `rg-azure-mcp-dev-westus2`;
- create one user-assigned managed identity;
- create one single-tenant Entra server application;
- assign Reader to that identity only at `rg-servicetracer-dev-westus2`;
- create one Container Apps environment and one Container App.

No existing ServiceTracer resource is modified except the new Reader role assignment at its resource-group scope.

## Success evidence

The workflow artifact must contain the What-If result, deployment result and outputs, provider transition, pinned-image inspection, Container App state, role assignment, Entra app observation, HTTP headers/status, live-verification summary, and SHA-256 manifest.

Success at this gate establishes:

```text
endpoint hosted = true
HTTPS ingress verified = true
unauthenticated access rejected = true
read-only runtime flag observed = true
resource-group Reader observed = true
authenticated MCP tool execution = not yet verified
```

## Failure

Stop. Do not rerun. Preserve the artifact and reconcile the exact failure boundary. Partial Azure resources can exist after a failed ARM deployment. Cleanup requires a separately reviewed request, including manual Entra application deletion.
