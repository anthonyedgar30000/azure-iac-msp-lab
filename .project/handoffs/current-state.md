# Current project handoff

## Workspace and repository reality

- Project: **ServiceTracer — Governed Azure Operations Lab**.
- Default branch: `main`.
- `main` observed before this repair branch opened: `e379064b7ee8b6a1a8b7731d31dedef1bca19e6f`, the PR #38 merge commit.
- Open pull requests observed before branch creation: zero.
- Repair branch: `fix/read-only-planner-rbac-query`.
- Live GitHub and fresh Azure evidence remain authoritative; this handoff is time-bounded.

## Accepted baseline and failed planning attempt

PR #38 promoted the guarded read-only planner workflow. Its exact-head CI passed, and the workflow was manually dispatched as run `29957833049` against the merged commit.

The run proved:

- exact reviewed-commit checkout succeeded;
- bounded authority and static no-mutation tests succeeded;
- GitHub OIDC login to Azure succeeded;
- the intended Azure subscription, resource group, and existing collector were reached;
- the collector had a system-assigned identity and `Succeeded` provisioning state;
- no Azure mutation was authorized or performed;
- the protected artifact was uploaded with digest `3dcd7f93d2842b873ef25b466a6686a334f77c908c0b0b2a21b9d07a37010f13`.

The run failed at scoped RBAC inventory because the planner combined `az role assignment list --scope ...` with `--all`. Current Azure CLI treats those as incompatible selection modes.

```text
Azure_login_succeeded
!= complete_Azure_plan

zero_byte_RBAC_file
!= zero_RBAC_assignments
```

ARM validation and What-If were not reached. The report endpoint remains undeployed, managed-identity publication remains unverified, and the frontend still has no live-data proof.

## Authored repair

- Change: `repair-read-only-planner-rbac-query`.
- Authority: repository-only reliability repair.
- Pull request: not yet assigned; live PR state remains external GitHub evidence.

Permitted paths:

- `infra/scripts/plan_existing_collector_report_publication.sh`;
- `infra/tests/test_existing_collector_report_publication_rbac_capture.py`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Protected scope includes workflow authority, OIDC configuration, Bicep resources, deployment operations, RBAC changes, Storage changes, VM commands, collector compute, networking, frontend configuration, budgets, alerts, and every Azure mutation.

## Repair contract

The planner must:

1. use scoped `az role assignment list` queries with `--include-inherited` and without `--all`;
2. capture command output into a temporary file;
3. require a non-empty JSON document of the expected top-level type;
4. move the temporary file to the final evidence path only after validation;
5. remove temporary evidence on failure;
6. preserve empty JSON arrays as valid evidence of no visible assignments;
7. remain read-only.

```text
command_created_empty_file
!= valid_empty_inventory

file_hash_valid
!= evidence_semantically_valid
```

## Intended architecture and scope

The architecture remains unchanged:

```text
real Azure transactions and metrics
        ↓
ServiceTracer deterministic analysis
        ↓
sanitary provenance-bearing report
        ↓
existing collector managed identity
        ↓
dedicated Azure Storage endpoint
        ↓
GitHub Pages operator console
```

This repair changes only planner compatibility and evidence integrity. It does not deploy the Storage endpoint, grant roles, publish a report, modify the collector, or configure the frontend.

## Identity, network, security, and cost boundaries

- OIDC authentication remains through the protected `azure-lab` environment.
- Azure mutation authority remains false.
- Collector publication remains managed-identity based and Storage scoped when separately authorized later.
- No browser-to-collector route is introduced.
- CAD 10.00 remains a planning ceiling, not current price evidence or an estimate.
- Current pricing, quota, actual cost, effective RBAC, endpoint behavior, and frontend ingestion remain deployment gates.

## Validation

Before merge:

1. validate `.project` state;
2. run `bash -n` on the planner;
3. run all unit tests, including the new RBAC-capture regression tests;
4. run Bicep lint and build;
5. inspect every exact-head CI job;
6. confirm the final diff is limited to the four declared paths;
7. record an owner-account technical review, explicitly not independent organizational approval;
8. obtain explicit merge authorization.

## Failure, rollback, and cleanup

If CI or review fails, keep the PR draft, patch only the declared files, and obtain fresh exact-head CI. Do not weaken OIDC, protected environment, exact-commit, confirmation, artifact, cost, or no-mutation controls.

Repository rollback is closing the PR or reverting its commits. No Azure rollback or cleanup applies because this repair performs no Azure action.

## Next gate

After merge, manually dispatch the planner against the exact merge commit. Inspect every step and artifact, verify complete RBAC evidence, ARM validation, and exact What-If, then reconcile current Azure reality before proposing any deployment.

```text
planner_repaired
!= planner_rerun_succeeded
!= endpoint_deployed
!= frontend_live_data_proven
```
