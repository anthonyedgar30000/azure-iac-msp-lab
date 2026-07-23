# Current project handoff

## Workspace and repository reality

- Project: **ServiceTracer — Governed Azure Operations Lab**.
- Default branch: `main`.
- `main` observed before this repair branch opened: `19b8eddf4fb9038a41ba1fb0e81567dcbdfe2e92`, the PR #40 merge commit.
- Open pull requests observed before branch creation: draft PR #41 only.
- Architecture-repair branch: `fix/blob-endpoint-browser-cors`.
- Draft architecture-repair pull request: #42.
- Live GitHub and fresh Azure evidence remain authoritative; this handoff is time-bounded.

## Successful read-only planning evidence

The existing-collector publication planner completed successfully as run `29965079470` against exact commit `19b8eddf4fb9038a41ba1fb0e81567dcbdfe2e92`.

The run proved:

- exact reviewed-commit checkout and bounded authority validation succeeded;
- GitHub OIDC login to the intended Azure context succeeded;
- the expected resource group, region, and existing collector were reached;
- the collector had a current system-assigned identity and `Succeeded` provisioning state;
- no tagged report Storage account existed;
- no visible collector publication role assignment existed;
- ProviderNoRbac validation completed;
- What-If completed with 21 `Ignore` and exactly three old-architecture `Create` changes;
- current price evidence remained unresolved and deployment remained blocked;
- no Azure mutation was authorized or performed;
- artifact `existing-collector-report-publication-plan-29965079470-1` was uploaded with digest `0f0ba512d1c61acc3149cb11c33e66ad7218cc1391f6b32f2fa1176459c2be10`.

The successful plan evaluated the pre-repair architecture. It remains protected historical evidence but cannot authorize the revised deployment.

```text
successful_old_plan
!= current_architecture_plan
!= deployment_authority
```

## Defect discovered during PR #41 review

Draft PR #41 promoted an execution workflow that expected the browser to fetch the report from Azure Storage's static-website endpoint while relying on Blob-service CORS.

The static-website endpoint does not apply Blob-service CORS. A deployment could therefore create resources and publish successfully, then fail browser/CORS verification and trigger rollback.

PR #41 exact-head CI passed, but CI success did not validate that Azure product-boundary assumption.

```text
CI_passed
!= browser_architecture_valid
```

PR #41 remains draft and changes-required. It must not be merged or dispatched against the old three-create planner artifact.

## Authored repair

- Change: `blob-endpoint-browser-cors`.
- Authority: repository-only browser endpoint architecture correction.
- Pull request: #42.
- Azure authentication authorized by this repair: **false**.
- Azure mutations authorized by this repair: **false**.

Permitted paths:

- `infra/modules/report_publication.bicep`;
- `infra/report-publication-existing-collector.bicep`;
- `infra/tests/test_report_publication.py`;
- `infra/tests/test_existing_collector_report_publication.py`;
- `docs/designs/existing-collector-public-report.md`;
- `docs/collector-vm.md`;
- `docs/implementation-status.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

No workflow dispatch, Azure permission change, Storage deployment, RBAC mutation, VM Run Command, report publication, collector modification, frontend source update, or cost approval is in scope.

## Corrected architecture

```text
real Azure transactions and metrics
        ↓
ServiceTracer deterministic analysis
        ↓
sanitized servicetracer.public-report.v1 envelope
        ↓
existing collector managed identity
        ↓ OAuth write
$web/reports/technician-handoff-report.json
        ↓ anonymous Blob-only read
https://<account>.blob.core.windows.net/$web/reports/technician-handoff-report.json
        ↓ exact-origin Blob-service CORS
GitHub Pages operator console
```

Repository declarations now require:

- a dedicated Standard LRS sanitized-output Storage account;
- `allowBlobPublicAccess: true` only on that dedicated account;
- shared-key authorization disabled;
- OAuth as the default write path;
- exact-origin Blob CORS restricted to `GET`, `HEAD`, and `OPTIONS`;
- `$web` declared with `publicAccess: Blob`, not `Container`;
- Blob versioning and seven-day delete retention;
- Storage-scoped Storage Blob Data Contributor for the current collector principal;
- `publicReportUrl` built from `primaryEndpoints.blob`, not `primaryEndpoints.web`.

CORS is not authentication. The sanitized report object is intentionally public by URL. Blob-only access permits object reads without anonymous container enumeration.

```text
allowBlobPublicAccess = true
+ $web publicAccess = Blob
+ dedicated sanitized-output account
!= raw evidence public
!= container enumeration allowed
```

Raw evidence, credentials, private addresses, customer-sensitive identifiers, unrestricted user content, and unsupported root-cause claims are prohibited from the publication account.

## Revised planning boundary

After PR #42 merges, manually rerun the existing read-only planner against the exact merge commit.

The expected reviewed creation set is:

1. one Storage account;
2. one Blob service configuration;
3. one `$web` container access resource;
4. one Storage-scoped role assignment for the current collector principal.

Any `Modify`, `Delete`, `Replace`, protected Compute/Network/Log Analytics change, unexpected role scope, wildcard CORS, Container-level anonymous access, or additional Storage resource is a blocker.

```text
fresh_four_create_plan_passed
!= current_price_verified
!= role_assignment_write_permission
!= Azure_mutation_authorized
```

## Identity, network, security, cost, and quota boundaries

- The read-only planner remains Contributor and must not receive RBAC-administrator permission merely to plan.
- A later execution identity needs separately reviewed minimum Storage deployment and `roleAssignments/write` permissions at the intended scope.
- The collector writer remains system-assigned managed identity plus Storage-scoped Blob Data Contributor.
- No browser-to-collector network path is introduced.
- No load-balancer, VNet, NSG, public IP, backend, collector VM, NIC, disk, image, extension, or Log Analytics change is permitted by this increment.
- CAD 10 remains only a planning ceiling, not a quotation or actual-cost fact.
- Current West US 2 price, quota, policy allowance, retention cost, request cost, and actual cost remain unresolved.

## Validation required before merge

1. validate `.project` state;
2. run all unit tests;
3. lint and build Bicep, including `infra/report-publication-existing-collector.bicep`;
4. inspect every exact-head CI job and any uploaded test evidence;
5. confirm the final diff is limited to the nine declared paths;
6. inspect the complete Bicep resource graph and output URL;
7. record an owner-account technical review, explicitly not independent organizational approval;
8. mark PR #42 ready only when exact-head CI and review are clean;
9. obtain explicit merge authorization.

Green CI alone does not prove Azure behavior. Fresh Azure planning remains a post-merge gate.

## Failure, rollback, and cleanup

If CI or review fails, keep PR #42 draft, patch only the declared files, and obtain fresh exact-head CI. Do not broaden anonymous access to `Container`, introduce wildcard CORS, enable shared-key writes, weaken report sanitization, modify PR #41, or perform Azure actions.

Repository rollback is closing PR #42 or reverting its commits. No Azure rollback or cleanup applies because this repair performs no Azure action.

## Next gate

After PR #42 merges:

1. dispatch the read-only planner against the exact merge commit;
2. inspect the complete artifact and revised four-create What-If;
3. obtain fresh cost, quota, policy, and execution-permission evidence;
4. rebase or repin draft PR #41 to the new planner run and digest;
5. re-review PR #41's execution and rollback logic;
6. obtain separate explicit merge and later dispatch authorization.

```text
architecture_repaired
!= architecture_merged
!= fresh_plan_succeeded
!= PR41_repaired
!= endpoint_deployed
!= frontend_live_data_proven
```
