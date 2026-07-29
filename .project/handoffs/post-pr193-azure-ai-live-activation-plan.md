# Post-PR #193 Azure AI live activation plan

## Reality boundary

```text
repository main = 2099b6c60268976f95d8b9ebcc20601aa1fce7f1
latest merged PR = #193
PR #193 exact source = 643f6f81fdb39d50a6476a3dc9a99bdfff026dc6
PR #193 exact-head CI = 30417651771 / success
open pull requests before this branch = none observed
Azure query in this increment = false
Azure mutation in this increment = false
```

The merged provider is real repository capability. It is not a live endpoint.

```text
provider_on_main != endpoint_live
preflight_implemented != preflight_dispatched
preflight_passed != deployment_authorized
model_listed != quota_available
quota_available != capacity_available
account_created != model_deployed
model_deployed != inference_rbac_effective
role_assignment_created != role_propagated
model_request_succeeded != Azure_operations_authorized
```

## Candidate live slice

```text
resource group candidate: rg-ai-msp-dev-canadaeast
preferred location: canadaeast
fallback location: eastus2
preferred model: gpt-4.1-mini / 2025-04-14
secondary model: gpt-5-mini / 2025-08-07
preferred deployment type: Standard
candidate capacity: 1
account candidate: oai-msp-aeg30000-dev
deployment candidate: gpt-41-mini-msp-dev
local API-key authentication: disabled
inference role: Cognitive Services OpenAI User
```

These values are deployment candidates, not subscription-specific availability
claims. The protected preflight must prove model inventory, quota, capacity,
provider state, existing resources, and OIDC principal RBAC before a mutation is
prepared.

## Repository increment

The candidate adds:

- a manual exact-commit Azure AI read-only preflight workflow;
- a non-mutating preflight script;
- a subscription-scope Bicep root;
- a resource-group Azure OpenAI module;
- fail-closed development parameters;
- static validation, evidence contract, reconciliation, and runbook.

The committed deployment switch is `false`. The committed inference role
assignment switch is also `false`.

## Network and identity boundary

The first candidate uses the Azure public endpoint with Microsoft Entra
authentication and local API keys disabled. This permits a GitHub-hosted runner
or another authorized identity to reach the service without opening an
application-specific inbound path.

Public endpoint reachability does not provide inference permission. The selected
principal must receive the exact inference role at the Azure OpenAI resource and
role propagation must be verified. A private endpoint remains a later hardening
decision after the minimal live path works.

## Cost boundary

```text
repository recurring cost delta: CAD $0
read-only preflight Azure resource cost delta: CAD $0
Azure Standard model billing: pay-as-you-go input and output tokens
actual subscription cost: not freshly observed
quota and capacity: not freshly observed
monthly cost ceiling: not selected
```

The first model request must be one bounded non-sensitive prompt with a small
output-token limit. It must not send protected Azure evidence or customer data.

## Authority

Anthony's instruction, **“Lets get it live,”** authorizes preparation of the live
activation path. It does not resolve the material unknowns required to bind a
cloud mutation to an exact region, model, quota line, capacity, identity, RBAC
scope, and cost ceiling.

Authorized now:

- branch creation from exact `main`;
- declared repository files;
- ordinary exact-head CI;
- a draft pull request.

Not authorized now:

- merge;
- workflow dispatch;
- Azure authentication or query;
- provider registration;
- resource-group or Azure OpenAI creation;
- model deployment;
- RBAC mutation;
- model request;
- rollback or cleanup.

## Failure, rollback, and cleanup

A preflight observation failure stops without mutation and preserves a typed
failure rather than converting it to absence. Repository rollback is to close or
revert the candidate PR. Azure rollback and cleanup are not applicable until a
separately authorized cloud operation occurs.

## Next gate

```text
exact-head CI
→ review and merge under fresh authority
→ exact-commit-bound read-only preflight authority
→ protected model/quota/capacity/RBAC evidence
→ select final architecture and cost ceiling
→ separate exact-scope What-If and deployment authority
→ deploy
→ verify resource, model, RBAC, endpoint, token path, and one bounded response
→ capture evidence
```
