# Azure AI go-live run 6 — adopt portal-created East US account

## Authority

Anthony Edgar provided fresh authority with:

> Proceed.

The instruction followed portal creation of the Azure OpenAI account and screenshots showing the exact East US resource group and account.

This is a fresh run-6 authority. It is not a GitHub Re-run of run 5.

## Repository boundary

```text
base main: 9cbf73741a97f41abe6f0070bfa379f99e5cf1bd
latest merged PR: #206
run 5: consumed terminal failure
open PRs before run-6 branch: none
branch: agent/azure-ai-adopt-eastus-run6
```

## Manual Azure reality supplied by Anthony

```text
subscription: Azure for Students
resource group: rg-ai-msp-dev-eastus
resource group location: East US
resource group deployment: 1 succeeded visible
account: oai-msp-anthony-dev-eastus
resource type: Azure OpenAI
account location: East US
model deployment: not established
inference response: not verified
```

The workflow must freshly query these facts before What-If. Screenshots are evidence of the manual bootstrap, not a substitute for runtime validation.

## Intended adoption path

```text
freshly verify existing rg-ai-msp-dev-eastus
→ freshly verify existing oai-msp-anthony-dev-eastus
→ resource-group-scoped What-If with the account declared existing
→ create or reconcile gpt-41-mini-msp-dev only
→ create or reconcile account-scoped Cognitive Services OpenAI User only
→ harden the verified existing account by disabling local authentication
→ one Entra-authenticated 32-token Responses API call
```

The adoption Bicep contains no resource-group resource and declares the Azure OpenAI account as `existing`. No duplicate resource group or Azure OpenAI account is authorized or structurally available from that template.

## Exact model target

```text
model: gpt-4.1-mini
version: 2025-04-14
deployment name: gpt-41-mini-msp-dev
deployment SKU: GlobalStandard
capacity: 1
region: eastus
```

Run 5 observed the exact model and version listed in East US with reported available Global Standard capacity 200. Run 6 must query availability and capacity again because prior evidence does not guarantee current capacity.

## Identity and permissions

The `azure-lab` GitHub environment supplies the OIDC application and the Azure for Students subscription context. The workflow resolves the service-principal object ID, assigns `Cognitive Services OpenAI User` only at the existing account scope, waits once for propagation, and makes one data-plane request.

The application runtime identity remains unselected. Successful GitHub-runner inference does not itself connect the demo API or Azure MCP.

## Security controls

```text
local API-key authentication: disabled on the verified existing account
API key use: prohibited
public network access: enabled for this demo increment
private endpoint: not configured
role scope: Azure OpenAI account only
model request count: 1
max output tokens: 32
automatic retry: disabled
manual rerun: unauthorized
```

## Cost

The model deployment is Global Standard pay-as-you-go at capacity 1. One bounded verification call is authorized. No provisioned throughput, budget resource, or repeated model traffic is authorized. Actual cost remains unknown until billing evidence is observed.

## Validation and expected evidence

The workflow must capture:

- exact subscription name and enabled state;
- exact resource-group name and East US location;
- exact account name, kind, location, provisioning state, network setting, and local-auth state;
- exact model listing and capacity observation;
- existing-deployment conflict check;
- resource-group-scoped What-If;
- deployment result;
- account-hardening result;
- post-deployment account, model, and RBAC verification;
- one bounded response receipt;
- redacted SHA-256 manifest and terminal summary.

## Failure and rollback

- Missing or mismatched manual account: stop before mutation.
- Conflicting existing deployment: stop before mutation.
- Model, capacity, or What-If failure: stop before mutation.
- Deployment failure: stop after the one deployment attempt and preserve partial state.
- Account-hardening or model-verification failure: preserve the model deployment, role assignment, and evidence.
- Rollback and cleanup are not authorized.

## Canonical distinctions

```text
manual_account_exists != model_deployed
portal_deployment_succeeded != service_validated
existing_resource_reference != account_creation
same_name_resource_group_deployment != duplicate_resource
account_adopted_by_IaC != originally_created_by_IaC
role_assignment_created != role_propagated
model_request_verified != demo_API_integrated
```
