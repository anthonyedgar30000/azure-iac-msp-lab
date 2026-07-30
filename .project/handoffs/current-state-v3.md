# Current project handoff v3

## Interpretation boundary

This is the authoritative repository and evidence handoff selected by `.project/CURRENT.json`. It records GitHub state after PR #251 merged and terminal evidence for Azure AI run 8 and ServiceTracer planning run 1.

```text
repository record != continuously refreshed dashboard
merged repository state != deployed Azure state
workflow dispatch accepted != authority validation passed
authority consumed != Azure login started
ARM What-If != Azure mutation
planning attempt failed != deployment attempted
not observed != absent
```

## Authoritative files

```text
selector: .project/CURRENT.json
current reality: .project/current-reality-v4.json
state index: .project/state-index-v13.json
current handoff: .project/handoffs/current-state-v3.md
completion gate: .project/lab-v1-completion-gate-v2.json
repository sync: .project/reconciliations/post-pr251-canonical-sync-20260730.json
latest operational overlay: .project/reconciliations/servicetracer-demo-api-plan-run1-terminal-20260730.json
ServiceTracer terminal: .project/reconciliations/servicetracer-demo-api-plan-run1-terminal-20260730.json
Azure AI terminal: .project/reconciliations/azure-ai-go-live-run8-terminal-20260730.json
prior run-8 trigger sync: .project/reconciliations/azure-ai-go-live-run8-trigger-sync-20260730.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 09fe72e3a82ea6ae56e1e85fd9745c9940ed6c12
latest merged PR: #251
latest merged source head: 2d17b70edc2d0474967db388bd3d425fb5400b74
PR #251 exact-head CI: 30512881241 / success
sync PR: #252
local working tree: not observed through connector
```

## ServiceTracer planning run 1

The direct workflow dispatch was accepted and consumed the one-shot planning authority:

```text
workflow: .github/workflows/servicetracer-demo-api-subproject-plan.yml
workflow run: 30513630134 / attempt 1
job: 90778676285
head: 09fe72e3a82ea6ae56e1e85fd9745c9940ed6c12
artifact: 8748027710
artifact digest: sha256:a3bb46d90bdff6329bcfe15f5b00b1f144b68b009724f9e912ca890ced9384d9
conclusion: failure
failure stage: validate_main_bound_dual_subscription_read_only_authority
failure class: confirmation_input_mismatch
authority consumed: true
rerun authorized: false
```

The job failed before Azure login because the supplied confirmation did not exactly match:

```text
PLAN-DEMO-API-SUBPROJECT:dev:st-demo-api-vm-aeg30000
```

The actual supplied value is not persisted.

```text
repository tests started: false
Azure login started: false
dependency subscription query started: false
target subscription query started: false
provider/policy/quota/SKU/inventory queried: false
ARM validation performed: false
ARM What-If performed: false
Azure mutation/deployment observed: false
planning ceiling: CAD $25.00
planning ceiling is spend authority: false
deployment authorized: false
```

The protected artifact contains only an empty `artifact-manifest.sha256`; it contains no planning summary or Azure evidence.

Promoted evidence:

```text
.project/evidence/servicetracer-demo-api-plan-run1-terminal-summary.json
SHA-256: 3c79f43342356bd448531ba35501d9ab0591f1eee8d2bba1f0437d44c88a71da
```

## Azure AI run 8

```text
workflow run: 30510660758
job: 90769840287
artifact: 8746964307
artifact digest: sha256:e05dccbc1618e052f905f12f03d3576a05357bdf6c298d380a140f3ecef25f51
failure stage: existing_direct_role_validation
direct account-scoped Cognitive Services OpenAI User matches: 0
Azure mutation: none
deployment started: false
model request performed: false
active Azure AI authorization: none
```

The GitHub OIDC principal did not have the required direct account-scoped inference role at the recorded time. This does not prove every inherited access path is absent.

The separately verified `gpt-5-mini` runtime remains distinct and was not modified by run 8.

## Azure and operational unknowns

Neither terminal failure freshly established all operational reality. Still unverified:

```text
tenant context
Azure OpenAI deployment inventory
model listing or capacity
actual Azure cost
Azure quota
ServiceTracer target-subscription state
ServiceTracer dependency-subscription state
policy effects
monitoring alert delivery
backup or recovery
```

## Authority after sync

```text
active Azure AI authority: none
active ServiceTracer planning authority: none
active deployment authority: none
Azure resource cost delta established by these terminal runs: CAD $0
```

This sync performs no workflow dispatch, Azure login/query, What-If, mutation, deployment, role change, model request, rollback, or cleanup.

## Next gate

A new ServiceTracer planning attempt requires corrected confirmation-input handling and fresh explicit one-attempt authority. A new Azure AI attempt requires the exact direct account-scoped inference role and fresh explicit authority. Deployment remains a separate later decision after successful planning evidence.
