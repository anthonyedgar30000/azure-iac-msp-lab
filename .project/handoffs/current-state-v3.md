# Current project handoff v3

This handoff is selected by `.project/CURRENT.json` for the Lab Factory preflight candidate. It is time-bounded and does not claim the preflight has executed.

## Repository

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 0b6fa63d86ae52119b63ef6c9421c8d13215cb59
latest merged PR: #223
open PRs before branch: none observed
candidate branch: agent/lab-factory-preflight-run1
local working tree: not observed / connector-backed
```

## Current selectors

```text
current reality: .project/current-reality-v4.json
state index: .project/state-index-v13.json
handoff: .project/handoffs/current-state-v3.md
reconciliation: .project/reconciliations/pre-lab-factory-preflight-run1-20260729.json
request: .project/deployment-requests/lab-factory-preflight-run1.json
contract: .project/contracts/lab-factory-preflight-v1.json
```

## Lab Factory boundary

```text
profile: servicetracer-demo-api@1.0.0 / candidate
environment: test
location: westus2
planned resource group: rg-st-demo-api-test-westus2
VM size: Standard_F1als_v7
planning horizon: 8 hours
cost ceiling: CAD $5.00
prepared request verified: true
preflight executed: false
ARM What-If verified: false
Azure deployment verified: false
service validation verified: false
cleanup verified: false
```

## Inherited evidence

The local MCP stdio client previously verified `list_lab_profiles` and `prepare_lab_request`. It did not establish a ChatGPT connection, remote MCP hosting, or Azure deployment authority.

The separately verified Azure AI runtime remains `gpt-5-mini` with Microsoft Entra authentication. Its exact ARM identity remains unreconciled. ServiceTracer evidence remains preserved but was not freshly observed while creating this candidate.

## Authority

```text
repository files, pull request, CI, and exact green merge: authorized
one merge-triggered read-only Azure preflight: authorized
ARM validation and What-If: authorized
provider registration: not authorized
Azure resource changes: not authorized
deployment: not authorized
role changes: not authorized
rerun, rollback, and cleanup: not authorized
```

```text
repository candidate != workflow executed
prepared request != ARM What-If
preflight passed != deployment authorized
retail estimate != actual cost
```

## Next gate

Run exact-head CI, recheck live GitHub state, merge the exact green candidate, observe the single preflight, and reconcile its protected artifact. A failure consumes the attempt. A success still requires separate deployment authority.
