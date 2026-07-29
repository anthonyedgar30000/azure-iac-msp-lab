# Azure AI go-live run 4 — West US 2 only

## Authority

Anthony Edgar authorized exactly:

> Proceed with Azure AI go-live run 4 in westus2 only.

This creates one fresh attempt. It is not a rerun of run 3.

## Exact path

```text
.project/deployment-requests/azure-ai-go-live-run4.json
→ .github/workflows/azure-ai-go-live-run4.yml
→ scripts/azure_ai_go_live_run4.sh
→ exact repaired executor blob 33b5ef111cb4f7b73e2978e9371e59fe9295274b
→ infra/azure-ai-live.bicep
→ infra/modules/azure_ai_openai.bicep
→ configured AZURE_SUBSCRIPTION_ID
```

## Destination

```text
region: West US 2
Azure region code: westus2
resource group: rg-ai-msp-dev-westus2
account: oai-msp-<subscription-hash>-westus2
kind: OpenAI
account SKU: S0
model: gpt-4.1-mini
model version: 2025-04-14
deployment: gpt-41-mini-msp-dev
deployment SKU: Standard
capacity: 1
local API-key authentication: disabled
public network access: enabled
inference role: Cognitive Services OpenAI User
role scope: selected Azure OpenAI account only
verification calls: one
max output tokens: 32
```

## Execution

The first merge to `main` that introduces `.github/workflows/azure-ai-go-live-run4.yml` is the only authorized trigger. The workflow validates the exact merge commit, authenticates with GitHub OIDC, checks the model listing in West US 2, runs subscription-scope What-If, deploys only if allowed, assigns the account-scoped inference role, and makes one bounded verification request.

## Failure and cleanup

There is no regional fallback. Any policy, model, quota, What-If, deployment, RBAC, or model-call failure is terminal and consumes run 4. Automatic retry, manual rerun, rollback, and cleanup are not authorized. Partial resources, if any, remain for exact-state inspection.

## Cost

The candidate uses Standard pay-as-you-go capacity 1 and one response capped at 32 output tokens. Provisioned throughput and budget creation are not authorized. Actual cost remains unknown until Azure produces deployment and usage evidence.
