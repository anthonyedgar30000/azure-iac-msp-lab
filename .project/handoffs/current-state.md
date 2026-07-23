# Current project handoff

## Live repository reality

Observed at `2026-07-23T04:01:30Z`:

- repository: `anthonyedgar30000/azure-iac-msp-lab`;
- default branch: `main`;
- live `main` head: `c3a17f8765fc7b9e43ef5f92a490ee43246ef35e`;
- latest merged pull request: PR #41, **Promote bounded live report publication**;
- PR #41 source head: `722dfcf99c367880147c9fd2f183d54d4d960f56`;
- PR #41 merged at `2026-07-23T03:20:47Z`;
- no open pull requests were observed before this reconciliation branch was created;
- the publication execution workflow is present on `main` at `.github/workflows/existing-collector-report-publication.yml`.

Live GitHub supersedes the older handoff that described PR #41 as a draft and the execution workflow as absent.

## Repository implementation and verification state

PR #41 is:

```text
implemented
→ exact-head CI verified
→ owner-account technically reviewed
→ merged
→ workflow present on main
```

Exact-head CI evidence:

- workflow run: `29976628311` / CI run 174;
- source commit: `722dfcf99c367880147c9fd2f183d54d4d960f56`;
- conclusion: `success`;
- `ServiceTracer tests`: passed;
- `Bicep lint and build`: passed.

Technical review evidence:

- review `4760496795`: repository promotion ready;
- review `4760497152`: prior static-website CORS blocker resolved;
- both reviews were submitted through the pull-request owner account and are not independent organizational approval.

## Merged execution contract

The merged workflow is manually dispatched and requires:

- exact reviewed execution commit checkout;
- protected `azure-lab` environment and GitHub OIDC;
- pinned read-only planner run, evaluated commit, artifact digest, ZIP digest, and internal manifest;
- exact four-create What-If allowlist;
- current cost evidence and a maximum monthly ceiling no greater than CAD 10.00;
- default `Provider` validation and a fresh exact four-create What-If before mutation;
- current collector identity and publisher preflight;
- exact typed confirmation;
- one bounded Bicep deployment;
- Blob endpoint, CORS, schema, freshness, content-equality, managed-identity publication, and browser proof;
- rollback limited to the matching collector role assignment and dedicated report Storage account.

The workflow uses the Blob service endpoint and `$web` with `publicAccess: Blob`; it does not use the CORS-incompatible static-website endpoint as the browser fetch target.

## Current read-only Azure evidence

The latest observed planner evidence remains run `29974111656`, evaluated against commit `d181c48bf718c65015f83e04e1bbf9a7bcf152f4`.

Artifact:

```text
existing-collector-report-publication-plan-29974111656-1
sha256:faed857cbd230e55b206ca6ab05adeeca75c98a9a48b0dc43bb04293cde09333
```

The plan proved:

- bounded read-only Azure authentication and inventory succeeded;
- ProviderNoRbac validation succeeded;
- What-If contained 21 `Ignore`, exactly four `Create`, zero `Modify`, zero `Delete`, and zero `Replace`;
- the creates were one Storage account, one Blob service, one `$web` Blob-only container, and one Storage-scoped collector role assignment;
- no Azure mutation was authorized or performed.

This historical plan does not prove current pricing, quota, policy, effective execution permission, collector identity, publisher availability, or unchanged Azure state.

## Current authority and operational state

```text
workflow_present
!= workflow_dispatched
!= Azure_authentication_authorized
!= Azure_mutation_authorized
!= deployment_completed
!= browser_rendering_verified
```

Current observed classifications:

- publication workflow present on `main`: **true**;
- publication workflow dispatch observed: **false**;
- publication workflow dispatch authorized: **false**;
- Azure authentication for publication execution authorized: **false**;
- Azure mutation authorized: **false**;
- Storage or RBAC deployment observed: **false**;
- managed-identity publication observed: **false**;
- manual repair observed: **false**;
- Blob endpoint operationally verified: **false**;
- browser rendering verified: **false**;
- operationally verified: **false**.

The older bounded grant for the read-only planner remains distinct from the publication execution workflow and does not authorize execution or mutation.

## Active repository-only reconciliation

Branch: `chore/reconcile-publication-merge-state`

Pull request: draft PR #43.

Temporary owner: this ChatGPT conversation, explicitly authorized by Anthony Edgar with `Proceed`.

Objective: reconcile project-state and handoff documentation to the live PR #41 merge.

Permitted paths:

- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

No workflow, script, infrastructure, frontend, deployment, runtime, credential, secret, Azure authentication, or Azure resource change is permitted by this increment. Temporary repository-write authority expires when its pull request closes or merges.

## Remaining execution gates

Before any publication workflow dispatch:

1. obtain fresh West US 2 pricing, quota, and Azure Policy evidence;
2. establish the minimum effective deployment permission and narrowly scoped `Microsoft.Authorization/roleAssignments/write` capability;
3. re-resolve the current collector identity and publisher availability;
4. verify the exact merged workflow commit and current Azure state;
5. obtain separate explicit authorization for workflow dispatch, Azure authentication, and the bounded Azure mutation;
6. inspect the complete workflow evidence if execution is later authorized;
7. prove the Blob response, exact CORS behavior, report equality, and browser rendering;
8. update `docs/report-source.json` only through a later repository-only pull request after live proof exists.

## Safest next step

Complete exact-head CI and review for draft PR #43. Do not dispatch the publication workflow or authenticate to Azure as part of reconciliation.
