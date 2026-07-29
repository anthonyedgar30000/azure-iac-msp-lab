# Azure AI go-live run 3 — terminal handoff

## Terminal result

```text
pull request: #202
exact merge commit: 0749e1e1f99e57576726c1aaa9f25b1a6092e0d9
workflow run: 30422253001 / attempt 1
artifact: 8712343242
artifact digest: sha256:f1f8e9b6a0ee0f363def055395e79c48d3e8957245fe31af8ecb2aa34b66129a
Azure OIDC login: succeeded
subscription: Azure for Students / Enabled
Microsoft.CognitiveServices: Registered
Canada East model listing: gpt-4.1-mini 2025-04-14 listed
East US 2 model listing: gpt-4.1-mini 2025-04-14 listed
Canada East What-If: blocked by RequestDisallowedByAzure
East US 2 What-If: blocked by RequestDisallowedByAzure
resource group created: false
Azure OpenAI account created: false
model deployed: false
RBAC changed: false
model request performed: false
endpoint live: false
cleanup required: false
```

## Root cause

The selected regions were blocked by the Azure for Students subscription policy that limits deployments to its current best-available region set. This was not a Bicep compilation, OIDC authentication, provider-registration, or established model-availability failure.

## Authorization state

Run 3 is consumed. Do not use GitHub's **Re-run** control. A new run requires a fresh instruction, a new request record, a new exact workflow path, and a new merge-triggered execution.

## Next bounded target

Anthony Edgar subsequently selected `westus2`. A later run may target West US 2 only, with no regional fallback, only under fresh single-attempt authority.
