# Current project handoff

## Live repository reality

Observed on `2026-07-23` before opening PR #44:

- repository: `anthonyedgar30000/azure-iac-msp-lab`;
- default branch: `main`;
- live `main` head: `2d5ad327e45d430105f72eaaf678fe7331464db4`;
- latest merged pull request: PR #43, **chore: reconcile merged publication project state**;
- no open pull requests were observed;
- the bounded publication execution workflow is present on `main` at `.github/workflows/existing-collector-report-publication.yml`.

Active repository-only increment:

- branch: `chore/repin-publication-plan-29979955391`;
- draft pull request: PR #44;
- authority: repin the merged execution workflow to current verified planner evidence only.

Live GitHub, exact-head CI, and fresh Azure evidence remain authoritative.

## Current read-only Azure evidence

Planner run `29979955391` completed successfully against exact commit `c3a17f8765fc7b9e43ef5f92a490ee43246ef35e`.

```text
artifact: existing-collector-report-publication-plan-29979955391-1
digest:   sha256:cb2b3ec7f9563d376e0ac4bae4e089af03a506ee272573445bf6510b946712bc
```

The artifact was unexpired when reviewed. The downloaded ZIP matched GitHub's digest, and all 13 internal evidence-file hashes verified.

The plan proved:

- exact reviewed-commit checkout and bounded read-only authority validation succeeded;
- Azure OIDC login and current resource-group and collector inventory succeeded;
- the resource group remained healthy in `westus2`;
- the existing collector remained provisioned successfully with the reviewed system-assigned identity;
- no tagged report Storage account existed;
- no visible collector publication role existed;
- ProviderNoRbac validation succeeded;
- What-If contained 25 entries: 21 `Ignore`, exactly four `Create`, zero `Modify`, zero `Delete`, and zero `Replace`;
- the four creates were one Standard LRS Storage account, one Blob service, one `$web` container with `publicAccess: Blob`, and one Storage-scoped Storage Blob Data Contributor assignment;
- no Azure mutation was authorized or performed.

```text
read_only_plan_succeeded
!= current_price_verified
!= execution_permission_verified
!= deployment_authorized
```

## PR #44 planner-repin scope

Permitted paths:

- `.github/workflows/existing-collector-report-publication.yml`;
- `infra/tests/test_existing_collector_report_publication.py`;
- `docs/runbooks/existing-collector-report-publication.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

The workflow, test, and runbook now pin:

```text
planner_run_id: 29979955391
planner_commit: c3a17f8765fc7b9e43ef5f92a490ee43246ef35e
planner_artifact_digest: sha256:cb2b3ec7f9563d376e0ac4bae4e089af03a506ee272573445bf6510b946712bc
```

The exact confirmation phrase becomes:

```text
PUBLISH:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev:29979955391
```

The workflow rejects the superseded run and digest before Azure login.

No Bicep module, deployment template, executor command, rollback behavior, anonymous-access setting, CORS rule, collector resource, network resource, Azure permission, or frontend source is changed by PR #44.

## Merged execution contract retained

The manually dispatched execution workflow still requires:

1. exact reviewed execution commit checkout;
2. protected `azure-lab` environment and GitHub OIDC;
3. pinned planner run, commit, artifact digest, ZIP digest, and internal manifest;
4. exact four-create What-If allowlist;
5. current price evidence and a maximum monthly ceiling no greater than CAD 10.00;
6. default `Provider` validation and a fresh exact four-create What-If before mutation;
7. current collector identity and publisher preflight;
8. exact typed confirmation;
9. one bounded Bicep deployment;
10. Blob endpoint, CORS, schema, freshness, report equality, and managed-identity publication verification;
11. rollback limited to the matching collector role assignment and dedicated report Storage account.

The browser target remains the Blob service endpoint. `$web` remains `publicAccess: Blob`; shared-key writes remain disabled; managed-identity OAuth remains the writer path.

## Current authority and operational state

```text
workflow_present
+ current_plan_pinned_in_draft_PR
!= workflow_merged_with_new_pin
!= workflow_dispatched
!= Azure_authentication_authorized_for_execution
!= Azure_mutation_authorized
!= deployment_completed
!= browser_rendering_verified
```

Current observed classifications:

- publication workflow present on `main`: **true**;
- PR #44 merged: **false**;
- publication workflow dispatch observed: **false**;
- publication workflow dispatch authorized: **false**;
- Azure authentication for publication execution authorized: **false**;
- Azure mutation authorized: **false**;
- Storage or RBAC deployment observed: **false**;
- managed-identity publication observed: **false**;
- Blob endpoint operationally verified: **false**;
- browser rendering verified: **false**;
- operationally verified: **false**.

The existing read-only planner grant remains distinct and does not authorize the execution workflow.

## Remaining gates

Before PR #44 can merge:

1. exact-head project validation and all unit tests must pass;
2. Bicep lint/build must pass;
3. the PR must remain limited to the five declared paths;
4. the exact workflow pins, test assertions, runbook, and authority boundaries require technical review;
5. explicit merge authorization is required.

Before any later publication workflow dispatch:

1. obtain current West US 2 pricing, quota, and Azure Policy evidence;
2. establish the minimum effective deployment permission and narrowly scoped `Microsoft.Authorization/roleAssignments/write` capability;
3. re-resolve the current collector identity and publisher availability;
4. verify the exact merged workflow commit and current Azure state;
5. obtain separate explicit authorization for workflow dispatch, Azure authentication, and the bounded Azure mutation;
6. inspect the complete execution evidence artifact;
7. prove the Blob response, exact CORS behavior, report equality, and browser rendering;
8. update `docs/report-source.json` only through a later repository-only pull request after live proof exists.

## Failure and rollback

If PR #44 CI or review fails, keep it draft and patch only the declared files. Do not dispatch workflows or authenticate to Azure.

Repository rollback is closing PR #44 or reverting its repository-only commits. No Azure cleanup applies because this increment performs no Azure action.
