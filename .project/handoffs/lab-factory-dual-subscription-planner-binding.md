# Lab Factory dual-subscription planner binding handoff

## Repository boundary

```text
base main: b81bd342ca59d51ee155c0e69cce9dbe19d70a14
latest merged PR before branch: #229
branch: agent/bind-lab-factory-dual-subscription-planner-v2
candidate head: resolved by live branch state
open PRs before branch: none observed
local working tree: not observed / connector-backed
```

## Objective

Bind the repository catalog and local MCP Lab Factory tools to the already-ratified ServiceTracer dual-subscription planner without dispatching it or contacting Azure.

## Canonical path

```text
profile: servicetracer-demo-api@1.0.0
MCP tools: list_lab_profiles / prepare_lab_request
planner: .github/workflows/servicetracer-demo-api-subproject-plan.yml
GitHub environment: azure-api-payg
dependency subscription: read-only ServiceTracer source
target subscription: planning-only independent workload target
validation level: ProviderNoRbac
ARM validation: required by planner
ARM What-If: required by planner
deployment command: unavailable
```

The MCP response returns workflow and installer SHA-256 digests, input names and provenance, and a closed `live_dispatch_authorized` flag. It returns no parameter values and no confirmation value.

## Authority

```text
repository changes and ordinary CI: authorized
local repository-only MCP smoke: authorized
workflow dispatch: not authorized
Azure authentication/query: not authorized
ARM validation/What-If: not authorized by this increment
Azure mutation/deployment/RBAC: not authorized
remote MCP or ChatGPT connection: not authorized
rollback/cleanup: not authorized
```

## Cost

```text
repository recurring Azure cost delta: CAD $0
planner default monthly ceiling: CAD $25.00
actual cost freshly observed: false
fresh quota/capacity observed: false
```

## Failure and rollback

Missing or changed planner files fail closed through digest and contract tests. Repository rollback is an exact revert of this binding increment. Azure rollback and cleanup do not apply because no Azure operation occurs.

## Evidence and validation

Expected exact-head evidence:

- repository CI;
- direct MCP adapter tests;
- local stdio MCP smoke using reduced environment;
- workflow and installer digests;
- deterministic plan digest;
- proof that supplied values are omitted;
- proof that dispatch and deployment authority remain false.

## Next gate

After green exact-head CI and a live-main freshness recheck, merge the exact candidate. A separate explicit decision is still required to dispatch the canonical dual-subscription planner.

```text
planner bound != workflow dispatched
workflow dispatched != ARM What-If accepted
ARM What-If accepted != deployment authorized
```
