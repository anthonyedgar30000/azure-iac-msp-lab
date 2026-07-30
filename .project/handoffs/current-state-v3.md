# Current project handoff v3

## Interpretation boundary

This is the authoritative repository and evidence handoff selected by `.project/CURRENT.json`. It records GitHub state observed after PR #246 merged and incorporates the Azure AI run-8 terminal artifact plus issue #232 evidence for the still-unconsumed ServiceTracer planning authorization.

```text
repository record != continuously refreshed dashboard
merged repository state != deployed Azure state
authorization recorded != workflow dispatched
merge trigger completed != child dispatch accepted
ARM What-If != Azure mutation
planning succeeded != deployment authorized
not observed != absent
```

## Authoritative files

```text
selector: .project/CURRENT.json
current reality: .project/current-reality-v4.json
state index: .project/state-index-v13.json
current handoff: .project/handoffs/current-state-v3.md
completion gate: .project/lab-v1-completion-gate-v2.json
repository sync: .project/reconciliations/post-pr246-canonical-sync-20260730.json
Azure AI terminal: .project/reconciliations/azure-ai-go-live-run8-terminal-20260730.json
```

Previous v3/v12/v2 and older unversioned files are historical compatibility records.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 8387c44aa4b82ae77cf32f53053187488d13d6ba
latest merged PR: #246
latest merged source head: 2a499d1c0cf71388705d03df893441e90a7f6cab
PR #246 exact-head CI: 30511634610 / success
open PRs observed: none
local working tree: not observed through connector
```

## Azure AI

Run 8 is terminal and consumed:

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

The GitHub OIDC principal did not have the required **direct** account-scoped inference role at the recorded time. That does not establish that every possible inherited access path is absent.

The separately verified `gpt-5-mini` runtime remains distinct:

```text
endpoint: https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/
deployment: gpt-5-mini
Entra response previously verified: true
ARM identity reconciled: false
modified by run 8: false
Azure OpenAI MCP invocation verified: false
ChatGPT MCP connection verified: false
```

## ServiceTracer Lab Factory planning

The Lab Factory profile is bound to the ratified dual-subscription planner:

```text
profile: servicetracer-demo-api@1.0.0
state: candidate
canonical workflow: .github/workflows/servicetracer-demo-api-subproject-plan.yml
GitHub environment: azure-api-payg
dependency subscription role: read-only existing dependency
target subscription role: planning only
ARM validation: available
ARM What-If: available
deployment command: absent
```

The one-shot planning authority remains active and unconsumed:

```text
attempt: servicetracer-demo-api-plan-run1
tracking issue: #232
latest trigger PR: #246
latest trigger merge: 8387c44aa4b82ae77cf32f53053187488d13d6ba
accepted child dispatches observed: 0
remaining authorized dispatches: 1
Azure authentication/query observed: false
ARM validation/What-If observed: false
Azure mutation/deployment observed: false
planning ceiling: CAD $25.00
planning ceiling is spend authority: false
deployment authorized: false
```

The remaining safe execution path is one manual `workflow_dispatch` of the canonical planner from `main` with the exact authorized inputs. This sync does not perform that dispatch.

## Azure and operational unknowns

The run-8 evidence freshly established the enabled Azure for Students subscription, registered Cognitive Services provider, East US resource group, and S0 OpenAI account. It did not freshly establish:

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

Authorized and performed by this sync:

```text
repository branch and declared files
pull-request creation
ordinary exact-head CI
merge after green CI and a live-main freshness recheck
```

Not performed:

```text
workflow dispatch or rerun
Azure authentication or query
ARM What-If
Azure mutation or deployment
RBAC mutation
model request
new MCP client call
remote MCP hosting
ChatGPT connection
cleanup or rollback
```

## Next gate

Complete this repository-only canonical sync. Afterward, the only active operational authorization is the one manual ServiceTracer planning dispatch. Protected planning evidence must be reviewed before any deployment authorization is created.
