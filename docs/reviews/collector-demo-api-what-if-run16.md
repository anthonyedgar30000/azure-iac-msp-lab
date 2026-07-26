# Collector-hosted demo API What-If run 16

## Evidence identity

- Workflow: `Collector-hosted demo API`
- Event: `workflow_dispatch`
- Operation: `what-if`
- Workflow run number: `16`
- Numeric workflow run ID: `not_observed`
- Reviewed commit: `8de1f61f8a0ea06dcf94b94c798edde2aace357d`
- Resource group: `rg-servicetracer-dev-westus2`
- Region: `westus2`
- Environment: `dev`
- Prefix: `mst`
- DNS label: `st-demo-api-aeg30000`
- Browser origin: `https://anthonyedgar30000.github.io`
- UI conclusion: `success`
- UI duration: `1m21s`
- Observation timestamp: `2026-07-26T03:37:14-04:00`
- Evidence source: user-provided GitHub Actions workflow-list screenshot

The screenshot proves that run number 16 reached a terminal successful conclusion. The available GitHub connector does not enumerate `workflow_dispatch` runs by workflow, so the numeric run ID, artifact identity, job logs, and artifact payload remain unobserved.

## Proven sequence

The workflow contract is fail-fast and sequential. A terminal success therefore establishes:

```text
exact reviewed commit checked out
→ bounded request and authority validated
→ repository tests passed
→ Azure workload-identity login passed
→ live collector and dependency state captured
→ deployment readiness passed
→ ARM validation completed
→ FullResourcePayloads What-If completed
→ deterministic classifier accepted the plan
→ evidence manifest and scoped artifact steps completed
```

Because the selected operation was `what-if`:

```text
deployment step = skipped
post-deploy capture = skipped
runtime verification = skipped
transaction replay = not performed
Azure mutation = false
```

## Accepted-plan claim boundary

The successful run proves that the current deterministic classifier accepted the live ARM What-If generated from `main@8de1f61f…`.

It does **not** yet prove the exact resource-level change list because these files have not been retrieved:

- `arm-what-if.json`
- `what-if-assessment.json`
- `readiness-assessment.json`
- `effective-collector-parameters.json`
- the evidence manifest

Therefore:

```text
WhatIf_terminal_success = true
exact_accepted_resource_changes = not_observed
artifact_identity = not_observed
cost_delta = not_observed
deployment_authorized = false
```

No resource change should be inferred from earlier failed What-If attempts. Azure may have changed between attempts, and the accepted run used a newer reviewed commit.

## Deployment-review gate

Before any `deploy` operation is authorized, inspect and promote:

1. Numeric run ID and all job/step conclusions.
2. Artifact name, ID, retention, and digest.
3. Verified internal evidence manifest.
4. Exact target-resource states and approved reconciliations from `what-if-assessment.json`.
5. Exact `Create`, `Modify`, `NoChange`, `Delete`, and replacement set from `arm-what-if.json`.
6. Current Azure inventory, quota, resource locks, and cost/budget evidence.
7. Expected failure and rollback behavior for each proposed mutation.
8. Explicit confirmation that the accepted plan stays within the collector-hosted demo API boundary.

A later deployment grant must be exact-source, exact-scope, one-shot, and non-renewing. It must not inherit authority from run number 16.

## Authority

This review records the successful bounded What-If and authorizes ordinary pull-request CI only.

It authorizes no:

- deployment;
- `verify` operation;
- transaction replay;
- cleanup;
- rollback;
- RBAC mutation;
- pull-request merge.

```text
workflow_success != deployment
WhatIf_accepted != deployment_authorized
artifact_expected != artifact_inspected
not_observed != false
```
