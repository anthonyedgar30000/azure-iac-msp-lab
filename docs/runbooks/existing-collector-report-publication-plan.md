# Existing-collector report-publication planning runbook

## Purpose

Use the manually dispatched GitHub Actions workflow to collect fresh Azure control-plane evidence and an exact ARM What-If for the decoupled public-report endpoint without deploying or mutating anything.

```text
read_only_plan
!= deployment

azure_login
!= azure_mutation_authority
```

## Workflow

- Path: `.github/workflows/existing-collector-report-publication-plan.yml`
- Trigger: manual `workflow_dispatch` only
- Protected environment: `azure-lab`
- Authentication: GitHub OIDC through `azure/login@v2`
- Planner: `infra/scripts/plan_existing_collector_report_publication.sh`
- Artifact retention: 30 days

## Default target

Defaults are hints and must be verified by the workflow:

- resource group: `rg-servicetracer-dev-westus2`
- region: `westus2`
- prefix: `mst`
- environment: `dev`
- collector: `vm-stcollector-mst-dev`
- allowed browser origin: `https://anthonyedgar30000.github.io`
- maximum monthly planning ceiling: CAD 10.00

## Required dispatch inputs

1. `resource_group`
2. `location`
3. `prefix`
4. `environment`
5. `allowed_origin`
6. `maximum_monthly_cost_cad`
7. `reviewed_commit` — exact 40-character commit already reviewed and passing CI
8. `confirmation`

The confirmation must equal:

```text
PLAN-PUBLICATION:<resource-group>:vm-stcollector-<prefix>-<environment>
```

For the default dev target:

```text
PLAN-PUBLICATION:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev
```

## Authorized operations

The planner may perform only:

- `az account show`
- `az group show`
- `az vm show`
- `az storage account list`
- `az role assignment list`
- `az deployment group validate`
- `az deployment group what-if`

It may also read repository files, validate inputs, run unit tests, calculate hashes, write the GitHub job summary, and upload the protected artifact.

## Prohibited operations

The workflow must not:

- deploy an ARM or Bicep template;
- create, update, or delete Storage;
- create or delete role assignments;
- execute VM Run Command;
- start, stop, restart, deallocate, replace, or modify the collector;
- change NICs, disks, load balancers, backends, NSGs, routes, DNS, budgets, or alerts;
- publish a report;
- update `docs/report-source.json`;
- change the frontend.

## Expected evidence

The artifact should contain:

- `request.json`
- `azure-context.json`
- `resource-group.json`
- `existing-collector.json`
- `existing-report-storage.json`
- complete visible role-assignment inventories
- collector-principal role-assignment subset
- `deployment-parameters.json`
- `arm-validation.json`
- `arm-what-if.json`
- `cost-boundary.json`
- `plan-summary.json`
- `artifact-manifest.sha256`

Sensitive resource IDs, tenant/subscription identifiers, principal IDs, and unrelated RBAC entries stay in the protected artifact. Sanitize them before portfolio publication.

## Validation after the run

Inspect every workflow job and step. Then verify:

1. the checked-out commit equals the reviewed commit;
2. the tenant, subscription, resource group, region, and tags match the intended target;
3. the collector exists and has `provisioningState: Succeeded`;
4. the current principal ID is a canonical GUID;
5. report Storage inventory is unambiguous;
6. role inventory is complete enough for the decision and any limitations are recorded;
7. ARM validation succeeded;
8. What-If contains only the intended report-publication resources;
9. no collector compute, disk, NIC, load-balancer, backend, or network resource appears in the change set;
10. current pricing and quota evidence are either captured or remain explicit blockers;
11. the plan summary records mutations unauthorized and unperformed;
12. the artifact manifest matches the downloaded files.

## Failure behavior

A failed planner run does not authorize a retry with weaker controls. Inspect the failing step and preserve the artifact. Fix repository code through a reviewed PR or correct only the dispatch input when the failure is clearly an input mismatch.

Stop when target context, identity, tags, inventory, validation, What-If, pricing, quota, or permissions differ from the reviewed expectation.

## Rollback and cleanup

The planner creates no Azure resources, so no Azure rollback or cleanup applies. GitHub artifact retention is 30 days. Preserve a promoted evidence copy and digest only after review; otherwise allow normal expiration.

Removing or disabling the workflow requires a reviewed repository revert. Do not treat deletion of evidence as rollback.

## Claim boundary

A successful run proves that a specific reviewed template was evaluated against a specific observed Azure context at a recorded time.

It does not prove:

- deployment success;
- effective write permission;
- managed-identity publication;
- public endpoint behavior;
- frontend ingestion;
- current guest health;
- exact root cause;
- actual monthly cost.
