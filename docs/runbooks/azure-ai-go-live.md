# Azure AI one-shot go-live runbook

## Scope

The first merge that introduces `.github/workflows/azure-ai-live-deploy.yml`
triggers one bounded deployment-and-verification run on `main`.

```text
locations: canadaeast, then eastus2
model: gpt-4.1-mini / 2025-04-14
deployment SKU: Standard
capacity: 1
identity: GitHub OIDC service principal
inference role: Cognitive Services OpenAI User
verification calls: 1
max output tokens: 32
```

The workflow checks live model inventory inside the same authorized run. It does
not create a separate preflight result or require a second dispatch.

## Deployment sequence

```text
validate exact merge commit and Bicep
→ authenticate with workload identity federation
→ register Microsoft.CognitiveServices if required
→ select first listed regional candidate
→ run subscription What-If
→ deploy resource group, Azure OpenAI account, and model
→ assign the inference role to the exact OIDC principal
→ verify resource, model, and RBAC
→ make one bounded non-sensitive Responses API request
→ upload protected evidence and manifest
```

## Security

- local API-key authentication is disabled;
- inference uses Microsoft Entra authentication;
- the first prompt contains no Azure evidence, customer information, or secrets;
- Azure public network access is used for this minimal path;
- the workflow persists hashes instead of raw tenant and principal identifiers;
- access tokens are never written to evidence.

## Expected evidence

```text
context.json
what-if-<location>.json
deployment-<location>.json
inference-role-assignment.json
account-verification.json
model-verification.json
rbac-verification.json
model-call-receipt.json
go-live-summary.json
artifact-manifest.sha256
```

## Failure and rollback

Canada East failure may continue to the predeclared East US 2 candidate inside
the same run. If both candidates fail, the run terminates and preserves evidence.

Manual rerun, rollback, and cleanup are not authorized by the initial go-live
instruction. Partial resources may remain for inspection. A later action must
first observe the exact Azure result and receive a new explicit instruction.
