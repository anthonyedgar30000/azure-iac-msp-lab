# Azure AI go-live run 3 — execution handoff

## Authority

Anthony Edgar supplied the fresh instruction `Proceed` after reviewing the exact Azure request path and destination.

This authorizes one new exact-commit attempt identified as:

```text
azure-ai-go-live-run3
```

It is not a rerun of run 1 or run 2.

## Repository boundary

```text
base main: 5c34b17eb7ccd3098d3c723261fa0f8a4d6e0c95
latest merged pull request: #199
run 1: consumed terminal failure before resource creation
run 2: consumed terminal failure before first Azure query after login
open pull requests before branch: none
candidate branch: agent/azure-ai-go-live-run3
```

## Exact deployment destination

Only the Azure subscription configured by the protected GitHub secret `AZURE_SUBSCRIPTION_ID` is in scope.

Candidate 1:

```text
region: Canada East
resource group: rg-ai-msp-dev-canadaeast
account: oai-msp-<subscription-hash>-canadaeast
```

Candidate 2, used only if candidate 1 is not viable inside the same run:

```text
region: East US 2
resource group: rg-ai-msp-dev-eastus2
account: oai-msp-<subscription-hash>-eastus2
```

Inside the selected resource group:

```text
resource type: Microsoft.CognitiveServices/accounts
kind: OpenAI
account SKU: S0
model: gpt-4.1-mini
model version: 2025-04-14
deployment name: gpt-41-mini-msp-dev
deployment SKU: Standard
capacity: 1
local API-key authentication: disabled
public network access: enabled
inference role: Cognitive Services OpenAI User
```

## Execution path

```text
merge exact run-3 candidate
→ GitHub push trigger
→ exact-commit validation
→ Azure OIDC login through environment azure-lab
→ subscription and principal verification
→ Microsoft.CognitiveServices provider verification
→ bounded regional model lookup
→ subscription-scope What-If
→ resource-group/account/model deployment
→ account-scoped inference role assignment
→ account/model/RBAC verification
→ one Responses API request capped at 32 output tokens
→ protected evidence artifact and SHA-256 manifest
```

The final request URL is:

```text
https://<selected-account>.openai.azure.com/openai/v1/responses
```

## Failure and rollback behavior

A terminal failure consumes run 3. There is no workflow-dispatch trigger and no automatic retry. Canada East to East US 2 fallback is allowed only inside the original workflow run.

Partial resources are left in place for exact-state inspection. Rollback and cleanup are not authorized by this request.

## Cost boundary

The account and model use standard pay-as-you-go capacity, not provisioned throughput. The verification request is capped at 32 output tokens. Actual cost remains unknown until Azure deployment and usage evidence exist.
