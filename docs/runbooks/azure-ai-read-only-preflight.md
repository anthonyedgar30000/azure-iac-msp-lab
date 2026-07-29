# Azure AI live activation — read-only preflight runbook

## Purpose

Collect the subscription-specific evidence required to choose a deployable Azure
OpenAI model without registering providers, creating resources, assigning roles,
deploying a model, or calling an inference endpoint.

The preflight answers:

- Which candidate Azure regions are available to the subscription?
- Is `Microsoft.CognitiveServices` already registered?
- Do Azure OpenAI or Foundry resources already exist?
- Are the candidate model versions listed in each region?
- What quota lines and current usage are visible?
- What model capacity is currently reported?
- What Azure roles are visible for the GitHub OIDC principal?
- Does the proposed dedicated resource group already exist?

## Candidate scope

```text
resource group: rg-ai-msp-dev-canadaeast
locations: canadaeast, eastus2
models:
  - gpt-4.1-mini / 2025-04-14
  - gpt-5-mini / 2025-08-07
```

These candidates are not deployment claims. Protected evidence decides the final
region, model, deployment type, capacity, and identity.

## Preconditions

Before dispatch:

1. Merge the preflight implementation through an exact-head green pull request.
2. Review the exact merged commit.
3. Verify that the `azure-lab` GitHub environment still contains the intended
   workload-identity configuration.
4. Issue a new non-renewing instruction that authorizes only Azure login and the
   read-only observations in this runbook.
5. Do not reuse the consumed Azure MCP preflight grant.

## Dispatch inputs

```text
resource_group = rg-ai-msp-dev-canadaeast
reviewed_commit = <exact merged 40-character commit>
confirmation = OBSERVE-AZURE-AI:<resource-group>:<reviewed-commit>
```

The workflow checks out the exact commit rather than the moving branch name.

## Read-only operations

The script performs:

- active account-context verification against the configured subscription;
- subscription state and hashed tenant/principal fingerprints;
- location catalog checks;
- `Microsoft.CognitiveServices` registration-state observation;
- proposed resource-group observation;
- existing OpenAI and AI Services account inventory;
- location model inventory through the Azure management API;
- Cognitive Services usage/quota observation;
- OpenAI account SKU observation;
- location/model capacity observation;
- current principal role-assignment observation.

The script does not perform:

```text
az provider register
az group create
az deployment ...
az cognitiveservices account create
az role assignment create
model deployment creation
OpenAI SDK or REST inference request
resource deletion or cleanup
```

## Expected artifact

The protected artifact contains only non-secret observations and hashes:

```text
request.json
account-context.json
location-catalog.json
provider-state.json
resource-group-state.json
existing-ai-accounts.json
models-<location>.json
usage-<location>.json
skus-<location>.json
capacity-<location>-<model>.json
principal-role-assignments.json
preflight-summary.json
artifact-manifest.sha256
```

Raw subscription, tenant, and principal identifiers are not promoted. Role scopes
replace the subscription ID with `<subscription>`.

## Interpretation

```text
observation_failed != not_present
model_listed != quota_available
quota_limit_greater_than_zero != deployable_capacity_available
capacity_available != deployment_authorized
role_assignment_listed != effective_permission_proven
preflight_complete != deployment_authorized
```

A missing quota permission is a material preflight failure. The workflow should
not continue to a deployment plan merely because public region documentation
lists the model.

## Deployment candidate

The repository contains a fail-closed candidate:

```text
infra/azure-ai-live.bicep
infra/modules/azure_ai_openai.bicep
infra/azure-ai-live.dev.bicepparam
```

The committed parameter file sets:

```text
deployAzureAi = false
assignInferenceRole = false
```

After protected evidence is reviewed, update or override the exact region,
model, version, deployment SKU, capacity, inference principal, network decision,
and cost ceiling. Then run Bicep lint, build, validation, and subscription-scope
What-If before requesting deployment authority.

## Security and network decision

The minimal candidate uses:

- Microsoft Entra authentication;
- local authentication disabled;
- Azure public network endpoint enabled;
- `Cognitive Services OpenAI User` for the inference principal;
- no customer or protected operational data in the first prompt.

Public network access is an initial connectivity decision, not the final security
baseline. A private endpoint and private DNS can be evaluated after the minimal
end-to-end path is verified and the runtime location is selected.

## Cost

The preflight creates no Azure resources. Standard Azure OpenAI deployments use
pay-as-you-go input/output token billing. The first deployment increment must
record a current estimate and select a monthly ceiling before mutation.

## Failure and rollback

Preflight failure stops without mutation. Preserve the protected artifact and
classify the missing observation. Do not rerun the same consumed authorization.

Repository rollback is to revert the exact implementation commit through review.
Azure rollback and cleanup are not applicable to this preflight.
