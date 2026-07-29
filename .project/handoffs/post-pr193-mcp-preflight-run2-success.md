# Azure MCP preflight run 2 success — repository handoff

## Live boundary

```text
repository: anthonyedgar30000/azure-iac-msp-lab
main: 2099b6c60268976f95d8b9ebcc20601aa1fce7f1
latest merged PR: #193
open draft PR: #194 / Azure AI activation / exact-head CI green
MCP preflight run: 30418812664 / attempt 1 / success
exact reviewed checkout: 02efa653cea281cf2b12781b1d2f63865b4dea2f
local working tree: not observed; connector-backed operations
```

This increment intentionally does not modify `.project/state-index.json` because active
PR #194 already owns that path. The reconciliation remains reviewable without creating
a cross-workstream merge collision. A later current-main reconciliation must select the
merged evidence after the active branches are resolved.

## Azure result

```text
Azure OIDC identity: servicePrincipal
subscription: Azure for Students
location westus2: available
proposed resource group: rg-azure-mcp-dev-westus2 / not present
Microsoft.App: NotRegistered
Microsoft.OperationalInsights: Registered
Microsoft.Insights: Registered
Microsoft.ManagedIdentity: Registered
Microsoft.Authorization: Registered
observation failures: 0
Azure mutation: none
```

The absence of the resource group and the unregistered `Microsoft.App` namespace are
observations only. They do not authorize creation or provider registration.

## Protected evidence

```text
artifact: 8711131933
name: azure-mcp-read-only-preflight-30418812664-1
artifact digest: sha256:4867d34fd9ee64881f27a58ae5f534052de30583d830d9602d5833c4097a826b
template manifest digest: sha256:0667efecb0eded85dc69b87deda2022e73b3dd879f0658659749e13587375b8a
expires: 2026-08-28T03:10:23Z
```

The complete non-secret template manifest is preserved at:

```text
infra/evidence/azure-mcp/azmcp-copilot-studio-aca-mi-20260729.sha256
```

## Template review

The official template repository is
`Azure-Samples/azmcp-copilot-studio-aca-mi`. Its observed current `main` is
`f156038315b196e880f3d2352032c01a691b30d9`.

The successful preflight downloaded a gallery alias, not an immutable repository commit.
The artifact preserves hashes but not the downloaded template files or an exact upstream
commit identifier. Therefore the content is fingerprinted but the upstream source remains
unresolved.

```text
content_manifest_pinned != upstream_source_commit_pinned
```

Observed security-sensitive template elements include:

- Azure Container Apps hosting;
- a user-assigned managed identity;
- Reader at subscription scope;
- storage tools started with `--read-only`;
- two Entra app registrations;
- a delegated scope named `Mcp.Tools.ReadWrite`;
- preauthorized client behavior;
- Microsoft Graph application resources;
- manual Entra app deletion outside `azd down`.

These are review inputs, not approved deployment decisions.

## Cost and authority

```text
repository recurring Azure cost delta: CAD $0
preflight Azure resource delta: CAD $0
actual Azure cost: not observed
quota: not observed
provider registration: not authorized
What-If: not authorized by this increment
deployment: not authorized
RBAC or Entra mutation: not authorized
```

## Next gate

Resolve an immutable upstream source commit and verify every manifest entry against it—or
vendor the exact reviewed template—then pin the container image digest and finish the
identity, RBAC, Entra, network, monitoring, cost, rollback, and cleanup review before a
no-mutation What-If is prepared.
