# Existing collector live-report publication runbook

## Purpose

Operate the bounded path that makes the GitHub Pages ServiceTracer console consume a fresh report derived from real Azure observations instead of the committed demonstration fixture.

```text
controlled lab fault
+ real Azure load-balancer metrics
+ real frontend transactions through Azure VMs
+ deterministic ServiceTracer analysis
+ collector managed-identity publication
+ provenance-bearing Blob endpoint fetch
!= static fixture simulation
```

This increment does not replace, redeploy, restart, resize, reimage, or reconfigure the collector VM, its NIC, either disk, the load balancer, backend VMs, VNets, NSGs, the public IP, or Log Analytics.

## Evidence anchor

The executable workflow is pinned to the successful read-only plan:

- planner run: `29974111656`;
- evaluated repository commit: `d181c48bf718c65015f83e04e1bbf9a7bcf152f4`;
- artifact: `existing-collector-report-publication-plan-29974111656-1`;
- artifact SHA-256: `faed857cbd230e55b206ca6ab05adeeca75c98a9a48b0dc43bb04293cde09333`.

The exact What-If contained 25 entries: 21 `Ignore` and four `Create` changes:

1. one Standard LRS Storage account;
2. one Blob service configuration;
3. one `$web` container with `publicAccess: Blob`;
4. one Storage-scoped Storage Blob Data Contributor assignment for the current collector principal.

It contained zero `Modify`, `Delete`, and `Replace` changes. The planner used `ProviderNoRbac`; therefore it proves the resource graph with read permissions but does not prove role-assignment write permission or authorize deployment.

## Intended architecture

```text
Azure Load Balancer DipAvailability metrics
        +
real HTTPS frontend flows through VPN-01 and VPN-02
        ↓
ServiceTracer source records and durable evidence spool
        ↓
deterministic technician-handoff report
        ↓
strict servicetracer.public-report.v1 sanitizer
        ↓
existing collector system-assigned managed identity
        ↓ OAuth write
$web/reports/technician-handoff-report.json
        ↓ anonymous Blob-only read
https://<account>.blob.core.windows.net/$web/reports/technician-handoff-report.json
        ↓ exact-origin Blob-service CORS
GitHub Pages console ?report=<verified Azure URL>
```

CORS is a browser response policy, not authentication. The report object is intentionally anonymously readable by URL. Only the sanitized public envelope belongs in this dedicated account. Raw evidence, tokens, private endpoints, tenant or subscription identifiers, customer-sensitive data, and exact-root-cause claims are prohibited.

## Scope and region

- resource group: `rg-servicetracer-dev-westus2`;
- expected region: `westus2`;
- existing collector: `vm-stcollector-mst-dev`;
- allowed browser origin: `https://anthonyedgar30000.github.io`;
- mutable Azure scope: one deterministic report Storage account, one Blob service, one `$web` access configuration, and one current-collector Storage-scoped role assignment.

The workflow refuses a pre-existing report Storage account. Initial deployment and later maintenance are separate authority paths.

## Identity and permissions

The workflow authenticates through GitHub OIDC in the protected `azure-lab` environment.

The execution identity needs normal resource deployment permission at the target resource group plus `Microsoft.Authorization/roleAssignments/write` at the smallest reviewed scope sufficient to create the Storage-scoped role. Do not grant subscription-wide Owner merely to execute this workflow.

The collector receives only Storage Blob Data Contributor on the dedicated report Storage account. The workflow re-resolves the system-assigned `principalId` and stops before deployment when it differs from the pinned plan.

## Cost and quota gate

A dispatch requires:

- current West US 2 Storage price evidence identified by a human-reviewed evidence ID;
- a bounded monthly estimate in CAD;
- an approved ceiling no greater than CAD 10.00;
- `estimate <= ceiling`;
- current subscription quota and policy allowance verified separately.

These values are decision evidence, not a Microsoft quotation or actual-cost measurement.

## Dispatch inputs

Use **Actions → Existing collector report publication → Run workflow** only after this workflow PR is merged and separate Azure-mutation authorization is recorded.

```text
reviewed_commit: <exact merged workflow commit>
planner_run_id: 29974111656
planner_commit: d181c48bf718c65015f83e04e1bbf9a7bcf152f4
planner_artifact_digest: sha256:faed857cbd230e55b206ca6ab05adeeca75c98a9a48b0dc43bb04293cde09333
current_price_evidence_id: <reviewed evidence identifier>
estimated_monthly_cost_cad: <reviewed estimate>
maximum_monthly_cost_cad: 10.00
confirmation: PUBLISH:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev:29974111656
```

The PR and merge do not authorize dispatch. The exact `PUBLISH:` phrase is valid only after Anthony Edgar explicitly authorizes Azure mutation against the final merged commit, current price evidence, current Azure state, and reviewed permission scope.

## Ordered execution

1. Check out and verify the exact reviewed execution commit.
2. Validate bounded inputs, cost evidence, and typed confirmation.
3. Run project validation, unit tests, shell syntax checks, and verifier compilation before Azure login.
4. Download the exact successful planner artifact through the GitHub API.
5. Verify run status, commit, artifact name, GitHub digest, ZIP digest, internal manifest, clean baseline, ProviderNoRbac validation, and the exact four-create What-If.
6. Authenticate through workload identity federation.
7. Re-resolve Azure context, resource-group tags and region, collector state and identity, publisher executable, and backend VM state.
8. Run default `Provider` validation and a fresh exact four-create What-If to prove current execution permission and unchanged scope.
9. Deploy only `infra/report-publication-existing-collector.bicep`.
10. Verify TLS, OAuth-only writes, account anonymous Blob allowance, exact CORS, versioning, retention, `$web` Blob-only access, Blob endpoint, and current-principal role scope.
11. Capture current `DipAvailability` metrics and generate real frontend transactions.
12. Run deterministic analysis and sanitizer projection.
13. Invoke the installed collector publisher through bounded VM Run Command; the publisher obtains its Storage token from managed identity.
14. Fetch the Blob endpoint with the reviewed `Origin` and verify schema, source, freshness, CORS, and report-content equality.
15. Emit the exact GitHub Pages `?report=` URL.
16. Upload protected non-secret evidence with a portable relative-path SHA-256 manifest.

## Success evidence

A successful artifact should contain request and planner verification, prechange Azure inventory, Provider validation and What-If, deployment output, postchange Storage/Blob/container/RBAC state, live probe metrics and transactions, deterministic reports, publisher Run Command result, public response headers, fetched envelope, and generated frontend test URL.

```text
public report path verified
!= browser rendering verified
!= default frontend source committed
```

After workflow success, open the generated test URL and capture the console showing **Azure collector report — live**, the collector ID, ServiceTracer version, generation time, and freshness. A later repository-only PR may then set `docs/report-source.json.live_report_url`.

## Failure and rollback

Before `az deployment group create`, any failure exits without publication-resource deployment.

Immediately before deployment, the executor arms a rollback trap. Any later failure attempts to:

1. inventory the new Storage account and matching collector role;
2. delete only the matching Storage Blob Data Contributor assignment;
3. delete only the deterministic report Storage account, which removes its Blob service and `$web` container;
4. verify the account is absent;
5. record that collector compute and network were unchanged.

Rollback never deletes, replaces, restarts, deallocates, resizes, or updates the collector, disks, NIC, load balancer, backends, VNet, NSGs, public IP, or Log Analytics. A failed rollback is an operational incident: preserve the artifact, inspect Azure Activity Log and current resources, and avoid unrelated cleanup.

## Cleanup and decommissioning

A separately authorized cleanup operation should stop publication, preserve required evidence, remove the collector's Storage-scoped role, delete the dedicated Storage account, verify absence, clear the committed live URL through a repository PR, prove fixture fallback, and capture final cost and deletion evidence.

## Authority boundary

```text
workflow_merged
!= dispatch_authorized
!= Azure_mutation_authorized
!= deployment_succeeded
!= browser_live_data_verified
```
