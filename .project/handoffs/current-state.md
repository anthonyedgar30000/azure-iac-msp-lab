# Current project handoff

## Workspace and repository reality

- Project: **ServiceTracer — Governed Azure Operations Lab**.
- Default branch: `main`.
- `main` observed before this repair branch opened: `3b035171e274819cb9590e32ac2ff752455d4387`, the PR #39 merge commit.
- Open pull requests observed before branch creation: zero.
- Repair branch: `fix/provider-no-rbac-planner-validation`.
- Live GitHub and fresh Azure evidence remain authoritative; this handoff is time-bounded.

## Accepted baseline and second planning attempt

PR #39 repaired scoped RBAC inventory and atomic evidence capture. Its exact-head CI and post-merge `main` CI passed. The read-only planner was then manually dispatched as run `29963170574` against the merge commit.

The run proved:

- exact reviewed-commit checkout succeeded;
- bounded authority and static no-mutation tests succeeded;
- GitHub OIDC login to Azure succeeded;
- the intended Azure subscription, resource group, and existing collector were reached;
- the collector had a system-assigned identity and `Succeeded` provisioning state;
- the collector remained on Ubuntu 22.04 Jammy;
- no tagged report Storage account currently existed;
- resource-group and report-storage RBAC evidence was captured as valid JSON;
- the collector had no visible report-storage role assignment;
- the planning service principal was visible as a subscription-scope Contributor;
- no Azure mutation was authorized or performed;
- the protected artifact was uploaded with digest `8d7891dce5d34b84cf629c64b97202a17421bf019d0dbd92064a1ac57053ee68`.

The run failed at default ARM `Provider` validation because the template contains a proposed `Microsoft.Authorization/roleAssignments` resource and the Contributor planning identity lacks `Microsoft.Authorization/roleAssignments/write`.

```text
complete_inventory_succeeded
!= ARM_plan_completed

Contributor_can_plan_resources
!= Contributor_can_create_role_assignments
```

This is a least-privilege planning boundary, not a reason to grant the read-only planner RBAC-administrator authority.

## Authored repair

- Change: `provider-no-rbac-planner-validation`.
- Authority: repository-only planner reliability repair.
- Pull request: not assigned at branch creation; live status remains external GitHub evidence.

Permitted paths:

- `infra/scripts/plan_existing_collector_report_publication.sh`;
- `infra/tests/test_existing_collector_report_publication_rbac_capture.py`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Protected scope includes workflow authority, OIDC configuration, Bicep resources, Azure permissions, deployment operations, RBAC changes, Storage changes, VM commands, collector compute, networking, frontend configuration, budgets, alerts, and every Azure mutation.

## Repair contract

The planner must:

1. use `--validation-level ProviderNoRbac` for both `az deployment group validate` and `az deployment group what-if`;
2. preserve provider/resource validation while requiring only read permission during planning;
3. explicitly record that ProviderNoRbac does not prove or authorize role-assignment deployment;
4. preserve atomic, non-empty, expected-type JSON evidence capture;
5. preserve the existing read-only Azure command allowlist and mutation prohibitions;
6. preserve the CAD 10.00 planning ceiling and unresolved price boundary;
7. remain fail-closed.

```text
ProviderNoRbac_plan_passed
!= role_assignment_write_permission
!= RBAC_change_authorized
!= deployment_authorized
```

## Intended architecture and scope

The intended architecture remains unchanged:

```text
real Azure transactions and metrics
        ↓
ServiceTracer deterministic analysis
        ↓
sanitized provenance-bearing report
        ↓
existing collector managed identity
        ↓
dedicated Azure Storage endpoint
        ↓
GitHub Pages operator console
```

This repair changes only planner validation semantics and evidence claim boundaries. It does not deploy the Storage endpoint, grant roles, publish a report, modify the collector, or configure the frontend.

## Identity, network, security, and cost boundaries

- OIDC authentication remains through the protected `azure-lab` environment.
- The planning identity remains Contributor and is not to receive `roleAssignments/write` for this workflow.
- Azure mutation authority remains false.
- Collector publication remains managed-identity based and Storage scoped when separately authorized later.
- No browser-to-collector route is introduced.
- CAD 10.00 remains a planning ceiling, not current price evidence or an estimate.
- Current pricing, quota, actual cost, deployment identity, effective post-deployment RBAC, endpoint behavior, and frontend ingestion remain later gates.

## Validation

Before merge:

1. validate `.project` state;
2. run `bash -n` on the planner;
3. run all unit tests, including ProviderNoRbac regression assertions;
4. run Bicep lint and build;
5. inspect every exact-head CI job;
6. confirm the final diff is limited to the four declared paths;
7. record an owner-account technical review, explicitly not independent organizational approval;
8. obtain explicit merge authorization.

## Failure, rollback, and cleanup

If CI or review fails, keep the PR draft, patch only the declared files, and obtain fresh exact-head CI. Do not grant additional Azure permissions or weaken OIDC, protected environment, exact-commit, confirmation, artifact, cost, or no-mutation controls.

Repository rollback is closing the PR or reverting its commits. No Azure rollback or cleanup applies because this repair performs no Azure action.

## Next gate

After merge, manually dispatch the planner against the exact merge commit. Inspect every step and artifact, verify ProviderNoRbac ARM validation and exact What-If, then reconcile current Azure reality before proposing any deployment.

```text
planner_repaired
!= planner_rerun_succeeded
!= endpoint_deployed
!= frontend_live_data_proven
```
