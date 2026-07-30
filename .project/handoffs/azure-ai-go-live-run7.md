# Azure AI go-live run 7 — existing account and existing inference role

## Authority

Anthony Edgar authorized:

> Proceed with Azure AI run 7 using the existing account and existing account-scoped inference role.

This is a fresh one-attempt authority. It is not a rerun of run 6.

## Repository boundary

```text
repository: anthonyedgar30000/azure-iac-msp-lab
base main: 0b6fa63d86ae52119b63ef6c9421c8d13215cb59
latest merged PR: #223
open PRs before branch: none
branch: agent/azure-ai-go-live-run7-existing-role
canonical selector: .project/CURRENT.json
current authoritative state: v3 reality / v12 state index / v2 handoff
```

The current canonical snapshot is historical at the moment run 7 is prepared. The run-7 request and protected runtime evidence govern this one attempt; a terminal reconciliation must supersede the canonical selector afterward.

## Existing Azure target

```text
subscription: Azure for Students
resource group: rg-ai-msp-dev-eastus
location: eastus
account: oai-msp-anthony-dev-eastus
kind: OpenAI
SKU: S0
required direct role: Cognitive Services OpenAI User
role definition: 5e0bd9bd-7b93-4f28-af87-19fc36ad61bd
```

Run 6 proved the resource group and account existed, the exact `gpt-4.1-mini` version was listed, and Global Standard capacity 200 was reported. It stopped before mutation because its template tried to create a role assignment. Run 7 must freshly re-query every mutable fact.

## Separate runtime boundary

A different Azure endpoint and deployment were separately verified:

```text
endpoint: https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/
deployment: gpt-5-mini
response verified: true
ARM identity reconciled: false
```

Run 7 does not modify, replace, or claim ownership of that runtime.

## Request path

```text
.project/deployment-requests/azure-ai-go-live-run7.json
→ .github/workflows/azure-ai-go-live-run7.yml
→ scripts/azure_ai_go_live_run7.sh
→ infra/azure-ai-existing-account-model-only.bicep
→ existing rg-ai-msp-dev-eastus/oai-msp-anthony-dev-eastus
```

The Bicep template declares the account as `existing` and contains only the child model deployment. It cannot create a resource group, account, or role assignment.

## Intended architecture

```text
GitHub Actions azure-lab OIDC identity
→ Azure Resource Manager
→ verify exact existing account and direct account-scoped inference role
→ model-only What-If
→ one idempotent gpt-41-mini-msp-dev deployment
→ one account hardening update
→ Microsoft Entra token
→ HTTPS /openai/v1/responses
→ one bounded response
```

## Model target

```text
model: gpt-4.1-mini
version: 2025-04-14
deployment: gpt-41-mini-msp-dev
SKU: GlobalStandard
capacity: 1
prompt: Reply with exactly: AZURE AI RUN 7 LIVE
max output tokens: 32
```

The workflow records current lifecycle metadata. `Retired`, missing, unavailable capacity, conflicting deployment state, or deployment-policy rejection stops before mutation.

## Identity and permissions

Run 7 verifies the GitHub OIDC service principal has a **direct** `Cognitive Services OpenAI User` assignment whose scope equals the exact target account ID. It does not create, update, or broaden RBAC.

The identity must separately have enough control-plane permission to run What-If, create or reconcile the child model deployment, and update account authentication settings. Data-plane inference permission does not imply those control-plane permissions.

## Network and security

```text
public network access: Enabled for this demo increment
private endpoint: not configured
local API-key authentication after run: disabled
API keys used or persisted: no
role scope: exact Azure OpenAI account
model requests: exactly one
automatic retry: disabled
manual GitHub Re-run: unauthorized
```

## Cost and quota

The account uses token-metered Azure OpenAI service with one Global Standard deployment at capacity 1. Run 7 authorizes one short request only. Regional capacity is freshly queried; actual billing cost is not established. No provisioned throughput or budget resource is authorized.

## Validation and evidence

The protected artifact must capture:

- exact subscription name and state;
- provider registration;
- resource-group and account baselines;
- direct role assignment baseline;
- full deployment inventory and conflict check;
- model listing, lifecycle metadata, and regional capacity;
- model-only What-If;
- one deployment result;
- one account-hardening result;
- post-deployment account, model, and role verification;
- one response receipt or exact error;
- terminal summary and SHA-256 manifest.

Raw subscription and principal identifiers must be redacted.

## Failure, rollback, and cleanup

- Missing/mismatched account or role: stop before mutation.
- Model, capacity, conflict, or What-If failure: stop before mutation.
- Deployment failure: stop after the one deployment attempt.
- Hardening or inference failure: preserve model and account state for diagnosis.
- No automatic retry, rollback, model deletion, account deletion, or role change is authorized.
- A later cleanup procedure must verify no dependent client uses `gpt-41-mini-msp-dev`, delete only that deployment if approved, and separately decide whether local authentication should remain disabled.

## Canonical distinctions

```text
existing role assignment != effective inference
model listed != deployable now
What-If success != deployment success
deployment success != model response verified
run7 original account != separately verified gpt5 runtime
model response verified != application integrated
estimated cost != actual cost
```
