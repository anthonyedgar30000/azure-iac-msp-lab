# Current project handoff v2

## Interpretation boundary

This is the authoritative repository and evidence handoff selected by `.project/CURRENT.json`. It records GitHub state observed at **2026-07-29T21:15:00-04:00** before this canonical-sync increment. It does not replace live GitHub or fresh Azure, runtime, cost, quota, RBAC, monitoring, backup, or recovery observations.

```text
repository_record != continuously refreshed dashboard
merged_repository_state != deployed Azure state
resource_exists != service validated
open PR initial success != terminal evidence promoted
local MCP implementation != local client call verified on main
model response verified != Azure OpenAI connected to MCP
not observed != absent
```

## Authoritative files

```text
selector: .project/CURRENT.json
state index: .project/state-index-v12.json
current reality: .project/current-reality-v3.json
current handoff: .project/handoffs/current-state-v2.md
completion gate: .project/lab-v1-completion-gate-v2.json
sync reconciliation: .project/reconciliations/post-pr220-canonical-sync-20260729.json
```

Legacy `.project/current-reality-v2.json`, `.project/state-index.json`, and `.project/handoffs/current-state.md` remain historical compatibility records for deterministic validators. They are not selected for current operations.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed default branch: main
observed main: 8926a5b48db9bb7cb08523d337e43d20ba7ed69d
latest merged PR: #220
PR #220 merge commit: 8926a5b48db9bb7cb08523d337e43d20ba7ed69d
PR #220 exact source head: 5d5e8cf2e9022204f3cd032945f777237c9d8f4d
PR #220 exact-head CI: 30504354336 / success
PR #220 merge-commit PR-triggered workflows: not observed
local working tree: not observed / connector-backed
```

## Concurrent pull request

PR #221 is a separate, non-overlapping draft candidate for a bounded local MCP client smoke test.

```text
PR #221 state: open draft
base: 8926a5b48db9bb7cb08523d337e43d20ba7ed69d
head: 1aeead3a987dbe2af9af1c46c5ac1e85033991ce
changed-path overlap with this sync: false
initial CI: 30505375909 / success
initial local MCP smoke: 30505376018 / success
terminal evidence reconciliation observed: false
merged: false
authority inherited by this sync: false
```

Initial green checks do not establish that PR #221 has completed its planned terminal evidence promotion or that its local-client result exists on `main`.

## Current implementation classification

```text
Azure Lab Factory Lite v1: merged repository implementation
Lab Factory profile: servicetracer-demo-api@1.0.0 / candidate
Lab Factory ARM What-If: not verified
Lab Factory Azure deployment: not verified
Lab Factory cleanup: not verified

local MCP server: implemented on main
tool inventory: get_current_reality, list_lab_profiles, prepare_lab_request
repository-only Lab Factory tools called by live client on main: false
remote MCP endpoint deployed: false
ChatGPT connected: false
Azure OpenAI called MCP tool: false
```

## Latest preserved Azure evidence

Azure MCP current-reality run 1 completed at `2026-07-29T12:01:23.289717Z`.

```text
subscription: Azure for Students
subscription state: Enabled
resource group: rg-ai-msp-dev-eastus
resource-group location: eastus
resource-group provisioning: Succeeded
resource count: 1
OpenAI account: oai-msp-anthony-dev-eastus
account kind / SKU: OpenAI / S0
deployments in observed account: 0
Azure mutations performed: false
secrets returned: false
authority consumed: true
rerun authorized: false
```

Separately verified Azure OpenAI runtime evidence remains:

```text
base URL: https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/
deployment: gpt-5-mini
authentication: Microsoft Entra bearer token
model response verified: true
verified runtime ARM scope reconciled: false
Azure OpenAI called MCP tool: false
ChatGPT connected: false
```

```text
empty deployment inventory in observed account != verified runtime absent globally
observed account name != verified endpoint ARM identity reconciled
verified model response != MCP connection verified
```

## ServiceTracer evidence boundary

ServiceTracer collector and demo evidence remains preserved historical operational evidence. Earlier evidence established successful ARM and VM-extension convergence, a healthy collector service, and a 20-transaction scenario with 10 successes and 10 failures. No fresh Azure or runtime query occurred during this sync.

```text
current collector power state: not freshly verified
current service health: not freshly verified
exact device root cause claimed: false
monitoring and alert delivery freshly verified: false
effective least privilege freshly verified: false
actual cost freshly verified: false
backup or recovery freshly verified: false
```

## Authority and cost

The user instruction **“Fix and sync”** grants this bounded repository-only increment authority to create its branch and declared files, run ordinary pull-request CI, and merge after the exact head is green and live `main` remains fresh.

```text
workflow dispatch or rerun authorized: false
Azure authentication or query authorized: false
ARM What-If authorized: false
Azure mutation authorized: false
RBAC mutation authorized: false
model call authorized: false
local MCP client call authorized by this sync: false
remote MCP deployment authorized: false
ChatGPT connection authorized: false
cleanup authorized: false
rollback authorized: false
expected recurring Azure cost delta: CAD $0
actual Azure cost freshly observed: false
quota freshly observed: false
```

## Next gate

Merge this repository-only canonical sync after exact-head CI and a final live-main/PR recheck. PR #221 remains a separate workstream unless its state changes before merge. Any Azure observation, What-If, deployment, model call, MCP client call, remote hosting, ChatGPT connection, RBAC change, cleanup, rollback, or retry requires separate bounded authority.

## Historical compatibility anchors

The following strings are intentionally retained so earlier deterministic validators continue to reproduce their original handoff boundary. They are historical, not current authority.

```text
observed main: f8f29d8601666646d354ffc450a85348e891483f
latest merged PR: #212
PR #212 merge commit: f8f29d8601666646d354ffc450a85348e891483f
Azure Lab Factory Lite v1: merged repository implementation and exact-source CI verified
Azure Lab Factory deployment or operational use: not established
merged planner != deployment authority
cleanup definition != cleanup verified
Draft PR #213
PR #213 merged: false
PR #213 authority inherited by this branch: false
MCP run-1 rerun authorized: false
Azure authentication or query authorized: false
Azure mutation authorized: false
pull-request merge authorized by this handoff: false
deployments in observed account: 0
deployment: gpt-5-mini
verified runtime ARM scope reconciled: false
Azure OpenAI called MCP tool: false
remote MCP endpoint deployed: false
workflow dispatch or rerun: unauthorized
Draft PR #186
```
