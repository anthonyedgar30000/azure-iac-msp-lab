# Runbook: Azure MCP live deployment

## Before dispatch

Confirm the implementation pull request is merged, the activation branch was created from that exact merge, its exact-head CI is green, and its only tree delta is `.project/deployment-requests/azure-mcp-live-run1.json`.

The request must be active, its `reviewed_source` must equal the implementation merge commit, and no deployment workflow or Bicep file may differ on the activation branch.

## Dispatch inputs

Use **Actions → Azure MCP live deployment → Run workflow** and select the exact activation branch recorded in the active request handoff—not a later moving `main`.

```text
request_path: .project/deployment-requests/azure-mcp-live-run1.json
confirmation: DEPLOY-AZURE-MCP-LIVE:<request-id-from-the-request-file>
```

Never use **Re-run**. A second attempt is not authorized and the durable claim should reject it.

## Expected mutations

- register `Microsoft.App` if not already registered;
- create `rg-azure-mcp-dev-westus2`;
- create one user-assigned managed identity;
- create one single-tenant Entra server application and its home-tenant service principal;
- assign Reader to that identity only at `rg-servicetracer-dev-westus2`;
- create one Container Apps environment and one Container App.

No existing ServiceTracer resource is modified except the new Reader role assignment at its resource-group scope.

## Success evidence

The workflow artifact must contain the Azure-resource What-If result, separate Entra deployment result, Azure deployment result and outputs, provider transition, pinned-image inspection, Container App state, role assignment, Entra application and service-principal observations, HTTP headers/status, live-verification summary, and SHA-256 manifest. Microsoft Graph extensible resources cannot be previewed by ARM What-If, so the Entra deployment remains a separately evidenced mutation boundary.

## Failure

Stop. Do not rerun. Preserve the artifact and reconcile the exact failure boundary. Partial Azure resources can exist after a failed ARM deployment. Cleanup requires a separately reviewed request, including manual Entra application deletion.
