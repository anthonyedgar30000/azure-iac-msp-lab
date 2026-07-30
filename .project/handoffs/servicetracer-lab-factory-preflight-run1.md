# ServiceTracer Lab Factory preflight run 1 handoff

## Status

```text
source instruction: Proceed
base main: 0b6fa63d86ae52119b63ef6c9421c8d13215cb59
latest merged PR before branch: 223
open PRs before branch: none
branch: agent/servicetracer-lab-factory-preflight-run1
repository implementation: in progress
exact-head CI: not yet run
Azure preflight executed: false
Azure deployment authorized: false
```

## Exact request boundary

```text
profile: servicetracer-demo-api@1.0.0
release state: candidate
environment: dev
location: westus2
TTL: 8 hours
target resource group: rg-st-demo-api-dev-westus2
VM SKU: Standard_F1als_v7
planning ceiling: CAD 5.00
subscription name: Azure for Students
```

The subscription UUID is supplied at runtime and must never be committed or
included in screenshots. The execution commit is the exact merge commit that
lands this increment.

## What the script may do

- verify the exact repository commit and clean working tree;
- authenticate through the existing Cloud Shell user session;
- observe subscription identity and enabled state;
- observe provider registration;
- observe VM SKU restrictions and vCPU quota;
- observe exact target resource-group state;
- query CAD retail VM pricing and optional month-to-date cost context;
- compile Bicep;
- execute ARM subscription validation;
- execute ARM subscription What-If with `ResourceIdOnly` output;
- write sanitized evidence and a SHA-256 manifest.

## What the script may not do

```text
create, update, or delete Azure resources
register providers
assign or remove roles
change policy, quota, networking, or secrets
run commands inside a VM
dispatch or rerun a GitHub workflow
call Azure OpenAI or any model
deploy MCP remotely
connect ChatGPT
clean up or roll back Azure
retry after the attempt is consumed
```

## Consumption

```text
~/.servicetracer-lab-factory-preflight-run1.consumed
```

The marker is created immediately before the first authenticated Azure
observation. A failure after that point consumes the attempt. Preserve partial
evidence and stop.

## Evidence path

```text
~/clouddrive/servicetracer-lab-factory-preflight-run1/evidence
```

The result is one of:

```text
passed
blocked
observation_failed
```

Even `passed` means only that a separate deployment request may be considered.
It does not grant deployment authority.

## Security and network review

The source proposes public TCP/80 and TCP/443 to one dedicated VM. It does not
propose inbound SSH. It also proposes a system-assigned VM identity, but no RBAC
assignment. Current runtime exposure, effective policy, effective least
privilege, and application security remain unverified until deployment and
service validation.

## Cost boundary

The repository increment itself adds CAD $0 in recurring Azure resource cost.
The preflight planning gate uses:

```text
8 × observed CAD hourly VM retail rate
+ CAD 2.00 storage/network contingency
<= CAD 5.00
```

This is deliberately incomplete planning context and not actual or discounted
Azure for Students cost.

## Next gate

Run pull-request CI. After green exact-head validation and a live-main freshness
check, merge. Then execute the exact merge commit once from Cloud Shell and
return the sanitized evidence for reconciliation.
