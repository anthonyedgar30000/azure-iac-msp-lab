# Current project handoff v3

## Interpretation boundary

This handoff is selected by `.project/CURRENT.json` for the ServiceTracer Lab
Factory preflight authorization increment. It records repository state observed
at **2026-07-29 21:49 -04:00**. No live Azure preflight evidence exists yet.

```text
repository authorization != Azure execution
prepared request != ARM What-If
ARM What-If passed != deployment authorized
estimated cost != actual cost
not observed != false
```

## Authoritative files

```text
selector: .project/CURRENT.json
current reality: .project/current-reality-v4.json
state index: .project/state-index-v13.json
current handoff: .project/handoffs/current-state-v3.md
completion gate: .project/lab-v1-completion-gate-v2.json
authorization reconciliation: .project/reconciliations/servicetracer-lab-factory-preflight-run1-authorization-20260729.json
```

The previous v3 reality, v12 state index, and v2 handoff remain immutable
historical records for the post-PR221 boundary.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 0b6fa63d86ae52119b63ef6c9421c8d13215cb59
latest merged PR: 223
open PRs before branch: none
active branch: agent/servicetracer-lab-factory-preflight-run1
exact-head CI: not yet run
local working tree: not observed through connector
```

## Verified foundations

```text
Azure OpenAI gpt-5-mini Entra invocation: verified
local get_current_reality execution: verified
local MCP list_lab_profiles call: verified
local MCP prepare_lab_request call: verified
prepared request deterministic: verified
parameter values returned by MCP: false
```

These proofs do not establish current ServiceTracer capacity, quota, policy,
cost, What-If safety, deployment, runtime health, or cleanup.

## Active preflight authority

```text
file: .project/observation-requests/servicetracer-lab-factory-preflight-run1.json
attempts: 1
execution environment: Azure Cloud Shell Bash
subscription: Azure for Students
profile: servicetracer-demo-api@1.0.0
environment: dev
location: westus2
TTL: 8 hours
resource group: rg-st-demo-api-dev-westus2
VM SKU: Standard_F1als_v7
planning ceiling: CAD 5.00
```

Authorized after merge:

- bounded subscription/provider/SKU/quota/resource-group observations;
- CAD retail price planning context;
- optional Cost Management context;
- Bicep compilation;
- ARM subscription validation;
- ARM subscription What-If;
- sanitized evidence generation.

Not authorized:

- Azure deployment or other resource mutation;
- provider or RBAC mutation;
- policy, networking, quota, or secret changes;
- VM guest execution;
- model calls;
- remote MCP or ChatGPT connection;
- cleanup, rollback, or retry.

## Proposed architecture under review

The source proposes a dedicated resource group with one NSG, VNet, subnet,
Standard Regional static public IP, NIC, Ubuntu VM, system-assigned identity, and
Custom Script extension.

```text
public ingress: TCP/80 and TCP/443
SSH ingress: none declared
VNet: 10.30.0.0/24
subnet: 10.30.0.0/27
```

This is source inspection only. Runtime exposure and effective security controls
remain unverified.

## Cost and quota

```text
repository increment recurring cost delta: CAD $0
preflight planning ceiling: CAD $5.00
actual Azure cost freshly observed: false
westus2 quota freshly observed: false
Standard_F1als_v7 restrictions freshly observed: false
```

The preflight will calculate a partial estimate from the observed CAD VM retail
rate plus a CAD $2.00 storage/network contingency. The estimate is not actual
cost or deployment spend authority.

## Failure behavior

A consumed preflight cannot be retried. A blocked result or observation failure
must be reconciled into a new terminal record. No Azure rollback applies because
no mutation is admitted.

## Next gate

Open a pull request, run full exact-head CI plus the dedicated preflight contract
workflow, and recheck live `main`. After merge, execute the exact merge commit
once from Cloud Shell and upload the sanitized evidence directory or archive.
