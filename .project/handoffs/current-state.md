# Current project handoff

## Workspace and repository reality

- Project: **ServiceTracer — Governed Azure Operations Lab**.
- Default branch: `main`.
- Current substantive baseline: PR #42 merge commit `d181c48bf718c65015f83e04e1bbf9a7bcf152f4`.
- Active repository-only increment: draft PR #41 on `feat/promote-live-report-publication`.
- PR #41 was reset onto current `main` rather than mechanically merging its obsolete static-website branch history.
- Live GitHub, exact-head CI, and fresh Azure evidence remain authoritative.

## Current read-only Azure evidence

Existing collector report publication plan run `29974111656` completed successfully against exact commit `d181c48bf718c65015f83e04e1bbf9a7bcf152f4`.

Evidence artifact:

```text
existing-collector-report-publication-plan-29974111656-1
sha256:faed857cbd230e55b206ca6ab05adeeca75c98a9a48b0dc43bb04293cde09333
```

The plan proved:

- exact reviewed-commit checkout and bounded read-only authority validation;
- Azure OIDC login to the intended context;
- the expected resource group, region, existing collector, and current system-assigned principal;
- no tagged report Storage account;
- no visible collector report-writer assignment;
- ProviderNoRbac validation success;
- 25 What-If entries: 21 `Ignore`, exactly four `Create`, zero `Modify`, zero `Delete`, and zero `Replace`;
- the four creates were one Standard LRS Storage account, one Blob service, one `$web` container with `publicAccess: Blob`, and one Storage-scoped Storage Blob Data Contributor assignment;
- no Azure mutation was authorized or performed.

```text
successful_read_only_plan
!= current_price_verified
!= execution_permission_verified
!= deployment_authorized
```

## Active PR #41 repair

PR #41 promotes a manually dispatched execution workflow. The repair is repository-only and was explicitly authorized by Anthony Edgar with `Proceed`.

Declared paths:

- `.github/workflows/existing-collector-report-publication.yml`;
- `infra/scripts/verify_existing_collector_publication_plan.py`;
- `infra/scripts/execute_existing_collector_report_publication.sh`;
- `infra/tests/test_existing_collector_report_publication.py`;
- `docs/runbooks/existing-collector-report-publication.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

No Azure login, permission grant, workflow dispatch, deployment, role change, VM Run Command, report publication, or frontend source update is authorized by this repair.

## Promoted execution contract

The workflow is pinned to:

```text
planner_run_id: 29974111656
planner_commit: d181c48bf718c65015f83e04e1bbf9a7bcf152f4
planner_artifact_digest: sha256:faed857cbd230e55b206ca6ab05adeeca75c98a9a48b0dc43bb04293cde09333
```

The dispatch requires:

- the exact merged workflow commit;
- protected `azure-lab` environment approval;
- current price evidence ID and bounded CAD estimate;
- maximum monthly ceiling no greater than CAD 10.00;
- exact confirmation `PUBLISH:<resource-group>:vm-stcollector-<prefix>-<environment>:29974111656`;
- separate explicit Azure-mutation authorization.

## Execution order and fail-closed gates

1. Verify exact reviewed commit, bounded inputs, cost evidence, and typed confirmation.
2. Run project validation, infrastructure tests, shell syntax checks, and verifier compilation before Azure login.
3. Download the exact planner artifact and verify GitHub digest, ZIP digest, internal manifest, clean initial state, ProviderNoRbac validation, and exact four-create What-If.
4. Authenticate through GitHub OIDC.
5. Re-resolve tenant/subscription context, resource-group tags and region, collector state and principal, publisher executable, backend VM state, and empty report-Storage state.
6. Run default `Provider` validation and a fresh exact four-create What-If. Missing `roleAssignments/write`, drift, extra resources, or protected-resource changes stop before deployment.
7. Arm rollback, then run one deployment of `infra/report-publication-existing-collector.bicep`.
8. Verify TLS 1.2, HTTPS, OAuth-default writes, shared-key disabled, account anonymous Blob allowance, exact CORS, versioning, seven-day retention, `$web` Blob-only access, Blob endpoint output, and current-principal Storage role.
9. Capture real `DipAvailability` metrics and real frontend transactions.
10. Run deterministic ServiceTracer analysis and sanitizer projection.
11. Publish through the existing collector managed identity using bounded VM Run Command.
12. Fetch the Blob URL with the reviewed `Origin` and verify schema, source, freshness, CORS, and report-content equality.
13. Produce the GitHub Pages `?report=` test URL and upload protected evidence.

## Security and network boundary

```text
allowBlobPublicAccess = true
+ $web publicAccess = Blob
+ dedicated sanitized-output account
!= anonymous container enumeration
!= raw evidence public
```

CORS is not authentication. The sanitized report is intentionally public by object URL. Raw evidence, credentials, tokens, private endpoints, customer identifiers, and exact-root-cause claims are prohibited from the account.

No browser-to-collector route is introduced. No VNet, NSG, public IP, load balancer, backend, collector VM, NIC, disk, image, extension, or Log Analytics resource may change.

## Identity and permission boundary

- The existing read-only planning principal remains least-privileged and must not receive RBAC administrator permissions merely for planning.
- The later execution identity needs normal resource deployment rights plus narrowly scoped `Microsoft.Authorization/roleAssignments/write`.
- Do not grant subscription-wide Owner.
- The collector receives only Storage Blob Data Contributor at the dedicated report Storage account.
- A changed collector principal is a stop condition.

## Failure and rollback

Before deployment, failures exit without creating publication resources.

After rollback is armed, a failure attempts to delete only:

1. the matching current-collector Storage Blob Data Contributor assignment;
2. the dedicated report Storage account, including its Blob service and `$web` container.

Rollback verifies account absence and records that collector compute and network were unchanged. Rollback failure is an operational incident requiring Activity Log and resource-state inspection.

## Remaining gates

Before PR #41 can merge:

1. exact-head project validation and all unit tests must pass;
2. Bicep lint/build must pass;
3. the PR must be conflict-free and exactly seven files different from `main`;
4. workflow, verifier, executor, rollback, and claim boundaries require technical review;
5. PR #41 must be marked ready only after review is clean;
6. explicit merge authorization is required.

After merge:

1. obtain current West US 2 pricing, quota, and policy evidence;
2. establish the minimum effective deployment/RBAC permission at the reviewed scope;
3. confirm publisher preflight and current collector identity;
4. obtain separate explicit Azure-mutation dispatch authorization;
5. run the workflow and inspect the complete evidence artifact;
6. open the generated frontend test URL and prove browser rendering;
7. commit the verified Blob URL to `docs/report-source.json` in a later repository-only PR.

```text
workflow_repaired
!= workflow_merged
!= dispatch_authorized
!= endpoint_deployed
!= browser_live_data_proven
```
