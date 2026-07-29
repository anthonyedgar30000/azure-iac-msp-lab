# Post-PR #194 Azure AI direct go-live handoff

## Reality boundary

```text
repository main = 375255c6bca57f672a326915e5a18708de3eaaad
latest merged PR = #194
PR #194 exact source = 8bcdef27a662ab8686a4ef1382777017353de0b8
PR #194 CI = 30419045145 / success
PR #194 Azure AI static validation = 30419045125 / success
Azure query at this boundary = false
Azure mutation at this boundary = false
```

The merged provider and Bicep candidate are real. The endpoint is not yet live.

## Direct activation

Anthony instructed: **“No more readonly preflight”** and **“Go live already.”**

The separate read-only workflow, script, and runbook are removed. A single
merge-triggered workflow now performs the bounded sequence:

```text
exact merge commit validation
→ GitHub OIDC login
→ verify/register Microsoft.CognitiveServices
→ select first viable candidate: canadaeast, then eastus2
→ subscription What-If
→ deploy gpt-4.1-mini 2025-04-14 / Standard / capacity 1
→ assign Cognitive Services OpenAI User to the exact OIDC principal
→ verify account, model, and RBAC
→ make one non-sensitive request with max_output_tokens=32
→ capture protected evidence
```

## Canonical boundaries

```text
merge_triggered != deployment_succeeded
model_listed != quota_available
what_if_succeeded != deployment_succeeded
account_created != model_deployed
role_assignment_created != role_propagated
deployment_succeeded != model_request_verified
model_request_verified != Azure_MCP_connected
failed_run != authorization_to_rerun
estimated_cost != actual_cost
```

## Cost and security

The candidate uses Standard pay-as-you-go token billing, Microsoft Entra
authentication, local API keys disabled, and one 32-output-token verification
request. Actual cost remains unobserved until execution evidence exists.

The first network path uses the Azure public endpoint with Entra authentication.
Private endpoint hardening is not part of this minimal go-live run.

## Authority and failure behavior

The exact candidate may be merged, and that merge may trigger one deployment run.
Azure login, bounded queries, provider registration if required, What-If,
resource creation, model deployment, exact inference-role assignment, and one
bounded model request are authorized.

Manual rerun, rollback, and cleanup are not authorized. If both regional
candidates fail, the workflow stops and preserves evidence. Partial resources may
remain for inspection.
