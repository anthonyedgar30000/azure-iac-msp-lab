# Azure AI go-live run 4 — terminal handoff

## Terminal result

```text
pull request: #203
exact merge commit: 697ef172c47e401865a4946a3acbe0df59e24c99
workflow run: 30423217542 / attempt 1
artifact: 8712644748
artifact digest: sha256:ced38cda175aa7172564566982de95199461dd038faaa4f87e260b2c2b86d328
Azure OIDC login: succeeded
subscription: Azure for Students / Enabled
Microsoft.CognitiveServices: Registered
region queried: West US 2
requested model: gpt-4.1-mini / 2025-04-14
requested model listed in West US 2: false
What-If started: false
resource group created: false
Azure OpenAI account created: false
model deployed: false
RBAC changed: false
model request performed: false
endpoint live: false
cleanup required: false
```

## Root cause

The exact requested model version was not present in the live West US 2 regional model listing. The workflow therefore stopped before What-If and before any Azure mutation. This does not establish quota exhaustion, a regional-policy block, or that every Azure OpenAI model is unavailable in West US 2.

## Authorization state

Run 4 is consumed. Do not use GitHub **Re-run**. A new attempt requires a fresh instruction and must choose an exact region/model/version combination grounded in live regional model evidence.

## Cost boundary

No Azure resource or billable model request was created by run 4. Actual subscription cost was not freshly queried; the evidence establishes only that this attempt produced no Azure resource deployment or model call.
