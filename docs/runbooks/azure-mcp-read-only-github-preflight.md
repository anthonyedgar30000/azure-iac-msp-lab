# Azure MCP read-only GitHub preflight

## Status

This package is a **repository implementation candidate**. It has not been dispatched and does not establish any live Azure MCP runtime state.

```text
workflow_implemented != workflow_dispatched
azure_authentication_configured != azure_authentication_performed
template_downloaded != template_approved
template_hashed != template_source_pinned
preflight_passed != endpoint_deployed
endpoint_deployed != OpenAI_client_connected
```

Observed repository baseline for this increment:

```text
main = 07f32b59eda11b5a3627d398f1ffca00c8c88e69
open pull request = #188
fresh Azure query = not performed
actual Azure cost and quota = not freshly observed
```

## Intended architecture

```text
Human-approved workflow dispatch
        |
        | exact reviewed commit + exact confirmation
        v
GitHub Actions environment: azure-lab
        |
        | workload identity federation
        v
Explicit Azure subscription
        |
        | read-only control-plane observations
        v
Protected evidence artifact
        +
Downloaded Azure MCP managed-identity template
        |
        | file hashes + static risk scan only
        v
Human template, identity, RBAC, namespace, image, cost, and quota review
```

The future runtime architecture remains:

```text
OpenAI Responses API
→ Entra OAuth
→ HTTPS Streamable HTTP /mcp
→ Azure MCP Server on Azure Container Apps
→ managed identity
→ explicitly bounded Azure read scope
```

This preflight does not deploy that runtime.

## Scope and dependencies

Workflow:

```text
.github/workflows/azure-mcp-read-only-preflight.yml
```

Required manual inputs:

- proposed resource group;
- proposed Azure region;
- exact 40-character reviewed repository commit;
- exact confirmation string:
  `OBSERVE-AZURE-MCP:<resource-group>:<location>:<reviewed-commit>`.

Required existing GitHub environment and secrets:

```text
environment = azure-lab
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
```

The workflow uses the repository's established workload-identity pattern. Their current presence, federated-credential validity, effective Azure RBAC, tenant, and subscription scope remain runtime observations until a dispatch is separately authorized and performed.

## Identity and permissions

GitHub workflow permissions:

```text
contents: read
id-token: write
```

Azure authentication is allowed only during an explicitly authorized read-only dispatch. The workflow does not request GitHub contents write permission.

The federated Azure identity must have sufficient read access for:

- account and location-catalog observation;
- provider registration-state observation;
- resource-group observation;
- existing resource inventory.

Read-only intent does not prove effective least privilege. The first protected artifact must be reviewed against the actual federated principal and effective Azure role assignments.

## Network paths

The GitHub-hosted runner requires outbound HTTPS access to:

- GitHub Actions and action dependencies;
- Microsoft Entra ID;
- Azure Resource Manager;
- Azure Developer CLI template sources.

No inbound Azure endpoint is created. No Container Apps ingress, DNS record, certificate, API Management gateway, or `/mcp` path exists from this increment.

## Security controls

The workflow:

- checks out the exact reviewed commit;
- requires an exact confirmation bound to resource group, location, and commit;
- uses OIDC rather than a client secret;
- passes the subscription identifier from a GitHub secret without writing the raw identifier to the artifact;
- persists subscription and tenant fingerprints instead of raw IDs;
- deletes temporary Azure CLI stderr before artifact upload;
- runs static boundary tests before Azure login;
- uses Azure Developer CLI non-interactive mode;
- uploads evidence even when the preflight fails;
- denies all provisioning, RBAC, provider-registration, Entra, OpenAI, and cleanup operations.

The protected artifact can contain resource names and inventory. Do not publish it or commit it to Git.

## Cost and quota implications

Expected Azure recurring-resource cost delta from this preflight is **CAD $0** because it creates no Azure resources. GitHub Actions minutes and artifact storage may count against the repository's plan.

Actual Azure spend, regional availability, provider state, and quota are not established until a separately authorized dispatch produces fresh evidence.

## Execution method

No dispatch is authorized by implementing or merging this workflow.

After merge, a separate authorization must bind:

```text
exact main commit
exact resource group
exact location
read-only Azure authentication
one workflow dispatch
no retry authority
no Azure mutation authority
no deployment authority
no OpenAI API authority
```

The operator then opens **Actions → Azure MCP read-only preflight → Run workflow**, enters the bound values, and submits the exact confirmation string.

The downloaded template remains an unpinned Azure Developer CLI gallery alias. A successful preflight therefore cannot authorize deployment.

## Validation

Repository validation:

```bash
bash -n scripts/azure_mcp_cloud_shell_preflight.sh
python -m unittest infra.tests.test_azure_mcp_read_only_preflight_workflow -v
python -m unittest discover -s infra/tests -v
```

Runtime validation after a separately authorized dispatch:

- exact checked-out commit equals the approved commit;
- OIDC login resolves the intended subscription;
- subscription state is enabled;
- proposed location appears in the subscription catalog;
- each provider observation is typed;
- resource-group state is `observed`, `not_present`, or `observation_failed`;
- existing resource inventory is captured only when applicable;
- template manifest digest is generated;
- no raw tenant or subscription identifier is persisted;
- no Azure mutation appears in the workflow or Azure Activity Log.

## Expected evidence

Protected workflow artifact:

```text
request.json
account-context.json
azure-cli-version.json
azure-developer-cli-version.txt
provider-states.json
resource-group-state.json
existing-resource-summary.json
template-files.sha256
template-risk-scan.txt
preflight-summary.json
artifact-manifest.sha256
```

The artifact must identify the observation time, exact commit, resource group, location, principal type, tenant and subscription fingerprints, template alias, manifest digest, limitations, and terminal status.

## Failure and rollback

The workflow fails closed when:

- the reviewed commit or confirmation does not match;
- the Azure subscription differs from the secret-bound subscription;
- the subscription is disabled;
- the region is absent from the subscription location catalog;
- an Azure observation fails ambiguously;
- the template cannot be downloaded non-interactively;
- hashing or risk scanning fails.

A failed preflight creates no Azure resources. Preserve the protected evidence artifact, then allow the GitHub-hosted runner workspace to be discarded.

Repository rollback is to close or revert the pull request.

## Cleanup

No Azure cleanup is applicable because this workflow contains no provisioning operation. Future removal of Container Apps, identities, Entra applications, role assignments, monitoring, DNS, certificates, API Management, or retained logs requires a separate reviewed cleanup plan and fresh authority.

## Next gate

```text
merge_exact_reviewed_commit
→ separately authorize one read-only dispatch
→ review protected evidence and downloaded-template digest
→ pin template source and container image
→ inspect exact identity, Entra, RBAC, namespace, cost, quota, rollback, and cleanup behavior
→ prepare a separate What-If/deployment increment
```
