# Azure AI go-live run 8 terminal handoff

## Terminal status

```text
attempt: azure-ai-go-live-run8
source instruction: Fix and proceed
source PR: #237
reviewed source head: c6b95f799f467da95adeb4ed0e815ccd5501171f
execution commit: 798486cb9e7c20fcf7fe508314317605dd4100ba
workflow run: 30510660758 / attempt 1
job: 90769840287
artifact: 8746964307
artifact digest: sha256:e05dccbc1618e052f905f12f03d3576a05357bdf6c298d380a140f3ecef25f51
conclusion: failure
stage: existing_direct_role_validation
status: required_direct_role_missing
authorization consumed: true
rerun authorized: false
```

Run 8 successfully applied the repository repair that removed the invalid `--scope` plus `--all` Azure CLI combination. The scoped role query completed and returned no direct account-scoped `Cognitive Services OpenAI User` assignment for the GitHub OIDC principal.

```text
role query completed != required role present
required direct role missing != all inherited access absent
Azure login succeeded != Azure AI activation succeeded
```

## Fresh Azure observations

```text
subscription: Azure for Students
subscription state: Enabled
subscription fingerprint: sha256:8f27aec6b3012cf0
Microsoft.CognitiveServices registration: Registered
resource group: rg-ai-msp-dev-eastus
resource-group location/state: eastus / Succeeded
account: oai-msp-anthony-dev-eastus
account kind/SKU/state: OpenAI / S0 / Succeeded
public network access: Enabled
disableLocalAuth: null
direct account-scoped inference-role matches: 0
tenant context freshly observed: false
```

The preserved principal fingerprint is `sha256:6f1db3ea4e8c9f6e`. No raw subscription, tenant, principal, token, or API-key material is stored.

## Mutation boundary

The run stopped before deployment inventory, model listing, capacity, ARM What-If, deployment, account hardening, or inference.

```text
Azure mutations performed: false
deployment started: false
account hardening started: false
model request performed: false
tokens consumed: 0
run-8 endpoint live: false
separate verified gpt-5-mini runtime modified: false
Azure MCP connected: false
```

The durable promoted evidence is:

```text
.project/evidence/azure-ai-go-live-run8-terminal-summary.json
SHA-256: 572489ee1380b239b4cd229ad1d99ef8aeb2e9831ee46366ed0b4664d4e417b7
```

## Cost, quota, and service validation

```text
Azure resource cost delta established by run 8: CAD $0
actual Azure account cost freshly observed: false
quota freshly observed: false
model deployment inventory freshly observed: false
monitoring verified: false
backup or recovery verified: false
```

## Next gate

Run 8 is consumed. Do not use GitHub Re-run.

Any later Azure AI activation attempt requires fresh explicit authority and a separately governed identity change that establishes the exact direct account-scoped inference role. Role creation or broadening is not authorized by this handoff.
