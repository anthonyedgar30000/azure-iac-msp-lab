# Azure MCP remote-server template review

## Decision status

The read-only Azure MCP prerequisite preflight passed. The remote-server template is **not
approved for deployment**.

```text
preflight_passed != template_approved
template_downloaded != source_commit_pinned
server_started_read_only != effective_least_privilege
```

## Evidence-bound architecture

The observed template proposes:

```text
client
→ OAuth through Microsoft Entra
→ public HTTPS Azure Container Apps ingress
→ Azure MCP Server with storage namespace and --read-only
→ user-assigned managed identity
→ Azure Resource Manager using Reader permissions
```

It also creates a client and server Entra application registration and optionally deploys
Application Insights.

## Material review findings

### Source provenance

The Azure Developer CLI gallery alias resolves to the official repository
`Azure-Samples/azmcp-copilot-studio-aca-mi`. The downloaded content has a complete SHA-256
manifest with digest:

```text
sha256:0667efecb0eded85dc69b87deda2022e73b3dd879f0658659749e13587375b8a
```

The artifact did not retain the downloaded files or the exact upstream source commit. The
current upstream `main` was observed at
`f156038315b196e880f3d2352032c01a691b30d9`, but equality with the preflight download has
not been established.

**Gate:** use an immutable commit archive or vendor the reviewed files, then compare every
manifest entry before proceeding.

### Identity and RBAC

The template defaults the MCP server managed identity to Reader at subscription scope.
That may be operationally convenient, but it is not yet proven to be the narrowest scope
required by the selected storage-only demonstration.

**Gate:** document which read-only Azure MCP storage operations require subscription,
resource-group, storage-account, or data-plane permissions. Select the narrowest supported
scope and verify effective access after propagation.

### Entra authorization

The server exposes a delegated scope named `Mcp.Tools.ReadWrite` while the process is
started with read-only tools. The scope name does not itself grant Azure mutation, but the
semantic mismatch is material and must not be treated as a least-privilege proof.

The template also preauthorizes client applications. Every client ID and consent path must
be explicitly reviewed. Tenant consent, preauthorization, and Azure RBAC are separate
controls.

### Network path

The expected path uses Azure Container Apps external HTTPS ingress with TLS termination at
the platform boundary. The exact ingress settings, forwarded-header trust, OAuth metadata,
DNS, outbound access, and image behavior require review from the immutable source.

### Image and supply chain

The successful artifact did not record the Azure MCP container image digest.

**Gate:** resolve the exact image reference and pin an immutable digest. Record registry,
publisher, version, architecture, vulnerability-review boundary, and update procedure.

### Monitoring and operations

Application Insights is available conditionally, but monitoring enabled does not prove that
alerts deliver. Define diagnostic categories, retention, alert recipients, synthetic health,
OAuth failure monitoring, and evidence capture before service validation.

### Cost and cleanup

No Azure resources were created by the preflight. Actual future Container Apps, Log
Analytics, Application Insights, networking, and data-retention costs are not yet observed.
A monthly ceiling must be selected before deployment.

`azd down` does not delete the Entra app registrations created by the template. Cleanup must
include separately authorized removal of both registrations, credentials, federated
credentials, consent grants, custom connectors, and any Power Platform connection.

## Required deployment package

Before What-If:

1. immutable source commit or vendored source matching the recorded manifest;
2. pinned container image digest;
3. explicit namespace and startup arguments;
4. exact identity and RBAC scope;
5. reviewed Entra scopes, preauthorized clients, and consent model;
6. network and DNS diagram;
7. monitoring and alert-validation plan;
8. cost ceiling and quota checks;
9. rollback and cleanup runbook;
10. evidence checklist for What-If, deployment, service validation, and access revocation.
