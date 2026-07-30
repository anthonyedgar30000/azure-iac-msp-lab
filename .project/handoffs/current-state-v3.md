# Current project handoff v3

## Interpretation boundary

This is the authoritative repository and evidence handoff selected by `.project/CURRENT.json`. It records GitHub state after PR #251 merged, the recovered Azure AI run-8 terminal artifact, and the direct-manual ServiceTracer planning gate.

```text
repository record != continuously refreshed dashboard
merged repository state != deployed Azure state
human authority recorded != workflow dispatched
connector paths closed != planning authority consumed
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
repository sync: .project/reconciliations/post-pr251-canonical-sync-20260730.json
Azure AI terminal: .project/reconciliations/azure-ai-go-live-run8-terminal-20260730.json
prior run-8 trigger sync: .project/reconciliations/azure-ai-go-live-run8-trigger-sync-20260730.json
ServiceTracer connector blocker: .project/reconciliations/servicetracer-demo-api-plan-run1-connector-event-blocked-20260729.json
```

Previous versioned and unversioned files remain historical compatibility records.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 09fe72e3a82ea6ae56e1e85fd9745c9940ed6c12
latest merged PR: #251
latest merged source head: 2d17b70edc2d0474967db388bd3d425fb5400b74
PR #251 exact-head CI: 30512881241 / success
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

The GitHub OIDC principal did not have the required direct account-scoped inference role at the recorded time. This does not prove every inherited access path is absent.

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

PR #251 removed all failed connector-event dispatcher paths. The one-shot planning authority remains active and unconsumed:

```text
attempt: servicetracer-demo-api-plan-run1
tracking issue: #232
connector dispatcher paths present: false
fresh human authorization comment: 5126316629
fresh instruction: Proceed you have my authority.
expected dispatch main: 09fe72e3a82ea6ae56e1e85fd9745c9940ed6c12
direct manual dispatch authorized: true
dispatch performed: false
authority consumed: false
accepted child dispatches observed: 0
remaining authorized dispatches: 1
Azure authentication/query observed: false
ARM validation/What-If observed: false
Azure mutation/deployment observed: false
planning ceiling: CAD $25.00
planning ceiling is spend authority: false
deployment authorized: false
```

The only remaining authorized operation is one direct GitHub Actions **Run workflow** on the canonical planner from `main` using the exact recorded inputs. Authority is consumed when the dispatch is accepted. This sync does not dispatch it.

## Azure and operational unknowns

Run 8 freshly established the enabled Azure for Students subscription, registered Cognitive Services provider, East US resource group, and S0 OpenAI account. It did not freshly establish:

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

Authorized and performed:

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

Complete this repository-only canonical sync. Afterward, the only active operational authorization is one direct manual ServiceTracer planning dispatch. Its protected planning artifact must be reviewed before any deployment authorization is created.
