# Azure MCP live activation v1

## Target

Deploy one remote Azure MCP endpoint to `westus2` using repository-owned Bicep rather than the moving Azure Developer CLI gallery alias.

```text
hosting: Azure Container Apps consumption
MCP resource group: rg-azure-mcp-dev-westus2
observable lab scope: rg-servicetracer-dev-westus2
runtime identity: user-assigned managed identity
runtime RBAC: Reader at the observable lab resource-group scope
image: digest pinned
namespaces: group, compute, monitor
server mode: namespace
read-only: enabled
replicas: 0–1
public ingress: HTTPS only
```

## Security changes from the sample

- No subscription-wide Reader assignment.
- No moving `latest` image tag.
- No moving gallery template during deployment.
- No `Mcp.Tools.ReadWrite` name for a read-only service; the delegated scope is `Mcp.Tools.Read`.
- Only the Visual Studio Code client is preauthorized initially.
- No client secret is created.
- Application Insights export is disabled for this first bounded deployment.
- Azure OIDC cannot start until the v2 immutable request is atomically claimed.

## Authorization-control repair

The v1 request format required a request to contain the SHA of the commit that contained that same request. That was an impossible self-reference.

Version 2 binds the request to an exact green implementation commit through `reviewed_source`. The claim workflow checks that the only tree delta between that source and the executing commit is the exact request JSON, then atomically creates the durable consumption reference before Azure OIDC is available.

## Cost behavior

The Container App uses the consumption plan and scales to zero. There is no minimum running replica. Actual subscription cost remains unobserved and usage above applicable grants can still create charges.

## Deployment sequence

1. Atomically claim the one-use request.
2. Verify the subscription, tenant fingerprint, target resource group, Azure RBAC write prerequisite, and Microsoft Graph application permission.
3. Register `Microsoft.App` only if required.
4. Verify the pinned Microsoft Container Registry digest.
5. Build and lint Bicep.
6. Run subscription What-If and reject deletes or scope escape.
7. Deploy once.
8. Verify the Container App, exact image, scale configuration, read-only flag, namespaces, managed identity, Reader assignment, Entra application, TLS endpoint, and unauthenticated rejection.
9. Upload protected evidence.

## Preserved limitation

The deployment proves the endpoint is hosted and protected. An authenticated client connection and real MCP tool invocation remain a separate validation step because the deployment workflow does not mint or store a user token.

## Failure and cleanup

No automatic retry, rollback, or cleanup is authorized. Resource-group cleanup would not delete the Entra application registration, so any future decommissioning must explicitly remove both Azure resources and the Entra object under separate authority.
