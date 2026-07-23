# Existing collector publication predeployment readiness

## Purpose

Capture current cost, quota, Azure Policy, identity, RBAC, and ARM validation evidence for the bounded ServiceTracer public-report path without deploying or changing anything.

```text
readiness evidence captured
!= deployment authorized
!= Azure mutation performed
!= publisher guest preflight completed
```

The workflow is intentionally separate from both the read-only architecture planner and the mutation-capable publication workflow.

## Repository and planner anchor

The readiness workflow is pinned to the verified read-only planner evidence:

```text
planner_run_id: 29979955391
planner_commit: c3a17f8765fc7b9e43ef5f92a490ee43246ef35e
planner_artifact_digest: sha256:cb2b3ec7f9563d376e0ac4bae4e089af03a506ee272573445bf6510b946712bc
```

That planner artifact proved 21 `Ignore`, exactly four `Create`, and zero `Modify`, `Delete`, or `Replace` changes. The four creates remain one Standard LRS Storage account, one Blob service, one `$web` container with Blob-only anonymous object reads, and one Storage-scoped Storage Blob Data Contributor assignment for the current collector identity.

## Read-only authority

The workflow may:

- authenticate through GitHub OIDC to the protected `azure-lab` environment;
- read subscription, resource-group, collector, Storage, quota, policy, deny-assignment, role-assignment, and role-definition state;
- decode the management access token's `oid` claim locally without persisting the token;
- call the unauthenticated Azure Retail Prices API;
- run ARM `Provider` validation;
- run ARM `Provider` and `ProviderNoRbac` What-If;
- upload protected non-secret evidence.

It may not:

- run `az deployment group create`;
- create, update, or delete Azure role assignments;
- create or delete Storage resources;
- invoke VM Run Command;
- change quota or policy;
- publish a report;
- change the frontend source.

## Dispatch

After this workflow PR is merged and a separate read-only dispatch decision is recorded, open:

**Actions → Existing collector report publication readiness → Run workflow**

Use:

```text
reviewed_commit: <exact merged readiness-workflow commit>
confirmation: READINESS-PUBLICATION:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev
```

Keep the other defaults unless current architecture evidence requires a separately reviewed change.

## Cost evidence

The workflow queries the official Azure Retail Prices API in CAD for Storage consumption meters in `westus2`. It saves the complete response and its SHA-256 digest.

The deterministic estimate selects the highest matching Hot LRS Blob price found for each category:

- data stored;
- write operations;
- read operations;
- other operations;
- data retrieval.

The model assumes:

```text
10 GB-month stored
100,000 writes per month
1,000,000 reads per month
100,000 other operations per month
10 GB data retrieval per month
CAD 2.00 contingency for uncaptured small charges
```

Selecting the highest matching meter is intentionally conservative. Missing or ambiguous required meters fail the cost check closed. The result is a retail-rate planning estimate, not a bill, negotiated price, tax calculation, Microsoft quotation, or actual-cost measurement.

## Quota evidence

The workflow calls the Storage resource provider's regional usage endpoint:

```text
/subscriptions/<subscription>/providers/Microsoft.Storage/locations/westus2/usages
```

It extracts the `StorageAccounts` current value and limit and requires at least one account of headroom.

```text
general documented limit
!= subscription-specific available quota
```

## Policy and deny evidence

The workflow captures applicable Azure Policy assignments at the resource-group scope, including inherited assignments, and lists deny assignments visible at the same scope.

Inventory alone does not prove that deployment is permitted. Default ARM `Provider` validation and What-If remain the effective policy and permission checks.

## Identity and RBAC evidence

The workflow:

1. re-resolves the collector VM and system-assigned identity;
2. compares the current principal with the pinned planner artifact;
3. resolves the GitHub OIDC execution principal from the management-token `oid` claim;
4. lists its direct, group, and inherited role assignments;
5. resolves assigned role definitions;
6. evaluates whether an applicable role declaration grants `Microsoft.Authorization/roleAssignments/write` at the future report Storage scope.

This role-declaration analysis is supporting evidence only. Deny assignments, policy, conditions, propagation, and runtime authorization can still block the operation. Default `Provider` validation is authoritative for the current execution context.

## ARM checks

The workflow runs:

- default `Provider` validation;
- default `Provider` What-If;
- `ProviderNoRbac` What-If.

Both What-If results are checked against the existing exact four-create classifier. Any additional create, modify, delete, replace, wrong scope, wrong principal, wrong public-access setting, wrong CORS origin, or protected-resource change fails readiness closed.

## Readiness result

`readiness-summary.json` records each check independently and lists blockers. A fully green result means only that current evidence supports a separate human deployment decision.

```text
ready_for_separate_deployment_decision = true
!= workflow_dispatch_authorized
!= Azure_mutation_authorized
!= deployment_succeeded
```

Publisher availability is deliberately recorded as `not_run_by_design_requires_execution_authority`. The mutation-capable execution workflow performs publisher preflight before deployment because guest VM Run Command is outside this read-only workflow.

## Expected blockers

The current planning identity was previously observed with Contributor. Contributor does not normally grant `Microsoft.Authorization/roleAssignments/write`; therefore default Provider validation and the declared-permission check may report a blocker until a separately reviewed, narrowly scoped execution permission exists.

Do not grant subscription-wide Owner merely to make the check green. Review the smallest scope and role capable of the one planned Storage-scoped assignment.

## Evidence artifact

Expected evidence includes:

- request and exact planner verification;
- Azure context and resource-group state;
- current collector state and identity;
- all visible Storage accounts and matching report-account result;
- regional Storage usage and quota assessment;
- applicable policy and deny-assignment inventories;
- execution-principal object ID, role assignments, role definitions, and permission assessment;
- raw CAD Retail Prices response, digest, assumptions, selected meters, and estimate;
- Provider validation and both What-If command results;
- final readiness summary;
- portable SHA-256 manifest.

## Failure and rollback

There is no Azure rollback because this workflow performs no Azure mutation. A failed evidence capture should preserve the artifact, identify the exact failed read or API call, and remain blocked.

Repository rollback is closing the readiness PR or reverting its commits.
