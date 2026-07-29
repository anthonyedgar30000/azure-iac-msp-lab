# Azure AI go-live run 2 — execution handoff

## Live repository boundary

```text
base main: e00d3af08d179f8af945ade689a44e9adfa00da9
latest merged pull request: #197
open pull requests before branch creation: none
run-1 workflow: 30419992872 / consumed failed terminal
run-1 Azure resource creation: none
run-1 cleanup required: false
repair exact-head CI: green
repair Azure AI static validation: green
```

## Fresh authority

Anthony's instruction **“Get this live already”** creates a new one-attempt
authorization. It is not a rerun of run 1.

```text
attempt ID: azure-ai-go-live-run2
attempt limit: 1
automatic retry: unauthorized
manual rerun: unauthorized
rollback: unauthorized
cleanup: unauthorized
```

The first merge commit to `main` introducing
`.github/workflows/azure-ai-go-live-run2.yml` is the exact execution trigger.

## Bounded execution

```text
Azure subscription: configured AZURE_SUBSCRIPTION_ID only
regions: canadaeast, then eastus2
model: gpt-4.1-mini / 2025-04-14
SKU: Standard
capacity: 1
local API keys: disabled
inference role: Cognitive Services OpenAI User
verification request count: 1
maximum output tokens: 32
prompt: Reply with exactly: AZURE AI LIVE
```

Sequence:

```text
exact-commit validation
→ Azure OIDC login
→ provider registration only if required
→ candidate inventory check
→ subscription What-If
→ resource group, Azure OpenAI account, and model deployment
→ exact inference role assignment
→ account, model, and RBAC verification
→ one bounded Responses API request
→ protected evidence and SHA-256 manifest
```

## Failure and recovery

Canada East may fall back to East US 2 inside this single run. A terminal failure
consumes the authorization and preserves evidence. Partial resources are left for
inspection; the workflow does not delete or rerun them.

## Cost boundary

The candidate uses Standard pay-as-you-go model deployment, not provisioned
throughput. Actual Azure token cost and any resource-side charges remain unknown
until live evidence is captured. No budget resource is created by this attempt.

## Canonical distinctions

```text
fresh_instruction != rerun_of_consumed_authority
merge_triggered != deployment_succeeded
deployment_succeeded != model_request_verified
role_assignment_created != role_propagated
endpoint_exists != endpoint_live
failed_run != authorization_to_retry
```
