# Azure AI go-live run 8 — repaired direct-role query

## Authority

Anthony Edgar instructed:

> Fix and proceed

This is fresh authority for exactly one new run. It does not reactivate or rerun consumed run 7.

## Repository boundary

```text
repository: anthonyedgar30000/azure-iac-msp-lab
base main: cb5385dc95e23d782ca564d87c5e9fd8f6357a62
latest merged PR before branch: #233
open PRs before branch: #234 (ServiceTracer reconciliation; no overlapping files)
branch: agent/azure-ai-go-live-run8-fixed-role-query
canonical selector: .project/CURRENT.json
```

## Established live reality before run 8

Run 7 freshly established only the following Azure facts:

```text
subscription: Azure for Students
subscription state: Enabled
Microsoft.CognitiveServices: Registered
resource group: rg-ai-msp-dev-eastus
resource-group location/provisioning: eastus / Succeeded
account: oai-msp-anthony-dev-eastus
account kind/SKU/provisioning: OpenAI / S0 / Succeeded
public network access: Enabled
disableLocalAuth: null
```

Run 7 did not establish whether the direct inference role exists because Azure CLI rejected the query before returning role data. It performed no Azure mutation, deployment, hardening update, or model request. Run 8 must freshly re-query every mutable fact.

## Repair

The historical run-7 executor remains unchanged and pinned by Git blob:

```text
scripts/azure_ai_go_live_run7.sh
blob: 21261d6e563fc3a55eae8cb1dd9306e69cacae5a
```

`scripts/azure_ai_go_live_run8.sh` derives a temporary run-8 executor from that exact blob and applies the recorded repair:

- remove `--all` from exactly three `az role assignment list` commands that also provide `--scope`;
- retain `--all` on the unscoped principal-discovery fallback;
- change the attempt, request path, temporary names, and verification prompt from run 7 to run 8;
- bind the derived executor to the exact source instruction `Fix and proceed`.

Any source drift, repair-count mismatch, or remaining invalid `--scope` plus `--all` combination fails before Azure login.

## Intended architecture

```text
GitHub Actions azure-lab OIDC identity
→ fresh Azure context and existing-resource validation
→ exact account-scoped Cognitive Services OpenAI User verification
→ deployment inventory, model listing, and regional capacity query
→ model-only ARM What-If
→ one idempotent gpt-41-mini-msp-dev deployment
→ one account hardening update: disable local authentication
→ Microsoft Entra data-plane token
→ one HTTPS /openai/v1/responses request
→ protected evidence artifact and SHA-256 manifest
```

## Scope and dependencies

```text
region: eastus
resource group: rg-ai-msp-dev-eastus
existing account: oai-msp-anthony-dev-eastus
model: gpt-4.1-mini
version: 2025-04-14
deployment: gpt-41-mini-msp-dev
SKU/capacity: GlobalStandard / 1
required direct role: Cognitive Services OpenAI User
role definition: 5e0bd9bd-7b93-4f28-af87-19fc36ad61bd
```

Dependencies are the pre-existing group, account, direct account-scoped inference role, registered provider, currently listed model/version/SKU, sufficient capacity, and enough control-plane permission for What-If, child deployment reconciliation, and account authentication hardening.

## Identity, network, and security

The workflow uses workload identity federation and persists no Azure credential. It does not create or broaden RBAC. Public network access remains enabled for this demo increment; no private endpoint is introduced. API keys are forbidden. Local authentication is disabled only after successful model deployment. The model call uses Microsoft Entra authentication, one non-sensitive prompt, and at most 32 output tokens.

The separately verified `gpt-5-mini` runtime is outside run-8 ownership and must not be modified.

## Cost and quota

The intended deployment is token-metered Global Standard capacity 1 with one short verification request. Capacity must be freshly observed. Provisioned throughput, a budget resource, fallback models, fallback regions, and additional requests are not authorized. Estimated cost is not actual cost.

## Deployment method and validation

The first merge commit to `main` that introduces `.github/workflows/azure-ai-go-live-run8.yml` is the single activation trigger.

Pre-merge/static validation:

```bash
python -m unittest infra.tests.test_azure_ai_go_live_run8 -v
bash -n scripts/azure_ai_go_live_run8.sh
az bicep lint --file infra/azure-ai-existing-account-model-only.bicep
az bicep build --file infra/azure-ai-existing-account-model-only.bicep
```

Runtime validation must produce fresh evidence for context, resource baselines, direct role assignment, deployment inventory, model lifecycle, capacity, What-If, deployment, account hardening, post-deployment account/model/role state, and one response receipt or exact failure.

Expected terminal success indicators:

```text
direct_account_role_verified: true
deployment_started: true
model deployment provisioningState: Succeeded
disableLocalAuth: true
model request HTTP status: 200
response contains: AZURE AI RUN 8 LIVE
endpoint_live: true
```

## Failure, rollback, cleanup, and evidence

Any mismatch before deployment stops without mutation. Deployment failure consumes the single deployment attempt and preserves partial state. Hardening or inference failure preserves the deployment and account state for diagnosis. There is no automatic retry, GitHub Re-run, rollback, model deletion, account deletion, or RBAC change.

Cleanup requires separate approval and must first verify no dependent client uses `gpt-41-mini-msp-dev`; only then may that deployment be deleted. Whether local authentication should remain disabled is a separate decision.

The protected artifact is retained for 30 days and must include a SHA-256 manifest. Raw subscription IDs, principal IDs, access tokens, and secrets must not be persisted.

## Canonical distinctions

```text
run7 consumed != run8 authorized
repair applied != role verified
role assignment exists != effective inference
What-If succeeded != deployment succeeded
deployment succeeded != response verified
endpoint live != application integrated
estimated cost != actual cost
```
