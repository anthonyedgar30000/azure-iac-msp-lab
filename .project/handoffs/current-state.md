# Current project handoff

## Live repository reality

Observed on `2026-07-23` before opening PR #45:

- repository: `anthonyedgar30000/azure-iac-msp-lab`;
- default branch: `main`;
- live `main` head: `e77d5e9c59537a6cd0ad05858565b2a51942e278`;
- latest merged pull request: PR #44, **Repin live publication to planner run 29979955391**;
- no open pull requests were observed before PR #45 was created;
- the mutation-capable publication workflow is present on `main` and pinned to the current verified planner artifact;
- no post-merge CI status was attached to merge commit `e77d5e9...`; PR #44 exact-head CI passed before merge.

Active repository-only increment:

- branch: `feat/publication-predeployment-readiness`;
- draft pull request: PR #45, **Add read-only publication predeployment readiness**;
- authority: add a read-only predeployment-readiness workflow and supporting evidence controls only.

Live GitHub, exact-head CI, and fresh Azure evidence remain authoritative.

## Current planner evidence

Planner run `29979955391` completed successfully against exact commit `c3a17f8765fc7b9e43ef5f92a490ee43246ef35e`.

```text
artifact: existing-collector-report-publication-plan-29979955391-1
digest:   sha256:cb2b3ec7f9563d376e0ac4bae4e089af03a506ee272573445bf6510b946712bc
```

The downloaded artifact and all 13 internal manifest entries verified. The plan proved:

- resource group and collector inventory succeeded;
- the collector retained the reviewed system-assigned principal;
- no report Storage account or visible publication role existed;
- ProviderNoRbac validation succeeded;
- What-If contained 21 `Ignore`, exactly four `Create`, and zero `Modify`, `Delete`, or `Replace` changes;
- the four creates were one Standard LRS Storage account, one Blob service, one `$web` Blob-only container, and one Storage-scoped Storage Blob Data Contributor assignment;
- no Azure mutation was authorized or performed.

```text
planner_evidence_verified
!= current_cost_verified
!= current_quota_verified
!= effective_execution_permission_verified
!= deployment_authorized
```

## Merged execution workflow

The execution workflow on `main` is pinned to:

```text
planner_run_id: 29979955391
planner_commit: c3a17f8765fc7b9e43ef5f92a490ee43246ef35e
planner_artifact_digest: sha256:cb2b3ec7f9563d376e0ac4bae4e089af03a506ee272573445bf6510b946712bc
```

It has not been dispatched. No Azure execution login, Provider execution validation, Storage creation, role assignment, VM Run Command, report publication, Blob response, or browser rendering has been observed.

## Draft PR #45

Declared paths:

- `.github/workflows/existing-collector-report-publication-readiness.yml`;
- `infra/scripts/assess_existing_collector_publication_readiness.py`;
- `infra/tests/test_existing_collector_report_publication_readiness.py`;
- `docs/runbooks/existing-collector-report-publication-readiness.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

The workflow is manually dispatched, uses exact reviewed-commit checkout, requires protected `azure-lab` OIDC, and requires:

```text
READINESS-PUBLICATION:<resource-group>:vm-stcollector-<prefix>-<environment>
```

It pins the same planner run, commit, artifact digest, ZIP digest, internal manifest, current collector principal, and exact four-create classifier used by the execution workflow.

## Read-only evidence contract

The readiness workflow may capture:

1. current Azure account, resource group, and collector state;
2. all visible Storage accounts and the deterministic report-account absence check;
3. subscription-specific `StorageAccounts` current usage and regional limit from the Storage resource provider;
4. applicable Azure Policy assignments and visible deny assignments at resource-group scope;
5. the OIDC execution principal from the management token's locally decoded `oid` claim without persisting the token;
6. direct, group, and inherited role assignments and their role definitions;
7. whether an applicable role declaration grants `Microsoft.Authorization/roleAssignments/write` at the future report Storage scope;
8. the complete CAD Azure Retail Prices response for West US 2 Storage consumption meters plus SHA-256 digest;
9. a conservative deterministic cost estimate with explicit assumptions and CAD 2.00 contingency;
10. default Provider validation;
11. exact Provider and ProviderNoRbac What-If evidence;
12. a blocker list and readiness classification.

The workflow and assessor contain no command that deploys resources, creates or deletes RBAC, changes quota or policy, invokes VM Run Command, publishes a report, or changes the frontend source.

The readiness regression test parses assembled Azure CLI command arrays in the Python abstract syntax tree and restricts them to the reviewed read-only command families. It does not rely only on substring matching.

## Cost model

The estimate uses the highest matching current Blob LRS retail meter for each required category:

```text
10 GB-month stored
100,000 writes/month
1,000,000 reads/month
100,000 other operations/month
10 GB retrieval/month
CAD 2.00 uncaptured-cost contingency
```

Missing required meters fail readiness closed. The estimate is deliberately conservative retail planning evidence, not a bill, quotation, negotiated rate, tax calculation, or actual cost. The artifact preserves each selected meter for human review.

## Permission and policy boundary

The role-declaration evaluator supports the Provider result but does not supersede it.

```text
role_definition_contains_action
!= effective_permission
```

Deny assignments, Azure Policy, conditions, propagation, and runtime authorization can still block deployment. Default Provider validation and exact Provider What-If remain the current effective checks.

The current planning identity was previously observed with Contributor, so `roleAssignments/write` is expected to remain a blocker unless a separately reviewed, narrowly scoped execution role exists. Do not grant subscription-wide Owner merely to make readiness green.

## Publisher boundary

Publisher guest preflight is deliberately not run by readiness:

```text
publisher_preflight_status = not_run_by_design_requires_execution_authority
```

VM Run Command is outside the read-only workflow. The execution workflow performs publisher preflight before its single bounded deployment.

## Authority state

```text
readiness_workflow_authored
!= readiness_workflow_merged
!= readiness_dispatch_authorized
!= Azure_authentication_authorized_for_readiness
!= publication_dispatch_authorized
!= Azure_mutation_authorized
```

Current classifications:

- PR #44 merged: **true**;
- execution workflow pinned to planner run `29979955391`: **true**;
- execution workflow dispatched: **false**;
- draft PR #45 open: **true**;
- proposed readiness workflow present on `main`: **false**;
- readiness workflow dispatched: **false**;
- Azure mutation authorized: **false**;
- Azure deployment observed: **false**;
- RBAC mutation observed: **false**;
- managed-identity publication observed: **false**;
- browser rendering verified: **false**.

## PR verification gates

Before PR #45 can merge:

1. `.project/validate.py` must pass;
2. the complete unit-test suite must pass;
3. Bicep lint/build must pass;
4. the readiness-specific tests must prove the workflow and script are non-mutating;
5. Python compilation and pure cost/RBAC unit tests must pass;
6. the final diff must remain limited to the six declared paths;
7. exact-head technical review must distinguish owner-account review from independent approval;
8. explicit merge authorization is required.

After merge, a separate explicit read-only dispatch decision is required. A successful readiness run still does not authorize the mutation-capable publication workflow.

## Failure and rollback

A repository failure keeps PR #45 draft and limits repairs to the six declared paths.

There is no Azure rollback because neither this PR nor the proposed workflow performs Azure mutation. Repository rollback is closing PR #45 or reverting its commits.
