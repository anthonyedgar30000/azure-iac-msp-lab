# Existing-collector public report publication design

## Decision

Deploy the sanitized ServiceTracer public-report path independently from collector compute. The publication increment consumes the **currently observed system-assigned managed-identity principal ID** of the existing collector and creates only a dedicated Azure Storage boundary plus its narrowly scoped Blob data role assignment.

The browser-readable URL must use the Azure **Blob service endpoint**, not the Storage static-website endpoint. Azure Storage static-website endpoints do not apply Blob-service CORS rules, while the Blob endpoint does.

```text
existing collector identity
!= collector VM redeployment

static website is enabled
!= static website endpoint is the browser API

Blob endpoint CORS configured
!= access restricted to one human or browser

report endpoint deployed
!= live report published

live report published
!= incident root cause proven
```

This avoids routing a presentation-layer requirement through the collector replacement path. The current collector image differs from the desired image contract, so an ordinary deployment that also manages collector compute is not an acceptable way to add report publication.

## Intended architecture

```text
real Azure frontend transactions
        +
Azure Load Balancer probe metrics
        ↓
ServiceTracer deterministic analysis
        ↓
sanitized servicetracer.public-report.v1 envelope
        ↓
existing collector system-assigned managed identity
        ↓
dedicated Storage account
        ↓
$web container, anonymous Blob read only
        ↓
blob.core.windows.net/$web/reports/technician-handoff-report.json
        ↓
exact-origin Blob-service CORS
        ↓
GitHub Pages operator console fetch with no-store
```

The browser receives only the bounded public envelope. Raw evidence, bearer tokens, private collector endpoints, Azure credentials, customer identifiers, and exact-root-cause claims are not publication inputs.

## Region and resource scope

- Existing resource group: `rg-servicetracer-dev-westus2` after fresh verification.
- Expected region: `westus2` after fresh verification.
- Existing collector name: `vm-stcollector-mst-dev` for the current dev naming contract.
- New mutable scope: one deterministic report Storage account, its Blob service configuration, one `$web` container access configuration, and one Storage-scope role assignment for the currently verified collector principal.
- Explicitly protected: collector VM, NIC, OS disk, evidence disk, image, extensions, guest configuration, load balancer, backend VMs, network topology, budgets, alerts, and unrelated RBAC.

The dedicated template is `infra/report-publication-existing-collector.bicep`. It accepts an externally resolved collector principal ID and invokes only `infra/modules/report_publication.bicep`.

## Current evidence and supersession boundary

Read-only planner run `29965079470` completed successfully against repository commit `19b8eddf4fb9038a41ba1fb0e81567dcbdfe2e92`. It proved the intended resource group and collector were reachable, no tagged report Storage account existed, no visible collector publication role existed, ProviderNoRbac validation completed, and the old template produced 21 `Ignore` changes plus exactly three `Create` changes. It authorized no Azure mutation.

That plan evaluated the superseded static-website URL architecture. After this Blob-endpoint repair is merged, its What-If is historical evidence only and cannot be used to authorize deployment.

```text
successful_old_plan
!= current_architecture_plan
!= deployment_authority
```

A fresh read-only planner run must evaluate the merged repair. The expected reviewed creation set becomes:

1. one Standard LRS Storage account;
2. one Blob service configuration;
3. one `$web` container resource with `publicAccess: Blob`;
4. one Storage-scoped Storage Blob Data Contributor assignment for the current collector principal.

Any `Modify`, `Delete`, `Replace`, or protected-resource change is a stop condition.

## Dependencies

Before any future deployment:

1. Resolve live GitHub `main`, pull-request, and exact-head CI state.
2. Authenticate to the intended Azure tenant and subscription using workload identity federation.
3. Verify the resource-group name, region, workload tag, and purpose tag.
4. Verify the existing collector exists with `provisioningState: Succeeded`.
5. Re-resolve its current system-assigned principal ID; never copy the historical value from documentation.
6. Capture report Storage resources and all visible role assignments at resource-group and report-Storage scope, then classify assignments for the current collector principal versus obsolete collector principals.
7. Run ProviderNoRbac ARM validation and exact What-If against the merged dedicated template.
8. Obtain fresh region-appropriate price evidence and explicit cost review.
9. Obtain explicit human authorization for Azure mutation and for any separately identified obsolete-role revocation.
10. Use an execution identity with the minimum effective Storage deployment and `roleAssignments/write` permissions required at the reviewed scope.

The repository-only architecture repair does not satisfy steps 2 through 10.

## Identity and permissions

### Deployment identity

A future promoted workflow should use GitHub OIDC and a protected `azure-lab` environment. Its Azure role must be bounded to the target resource group and sufficient only to deploy the report Storage resources and role assignment. The exact deployment identity and effective permissions require fresh verification before promotion.

The read-only planning identity must not receive RBAC-administrator permissions merely to make planning pass.

### Collector identity

The existing collector uses a system-assigned managed identity. The future workflow must read its current `principalId` immediately before validation and again before deployment. A mismatch between reviewed planning evidence and predeployment identity is a stop condition.

The collector receives **Storage Blob Data Contributor** only at the dedicated report Storage account. No subscription-wide, resource-group-wide, VM-management, network-management, or secret-management role is introduced by this design.

A system-assigned identity changes when the VM is replaced. The role-assignment resource name is derived from the Storage account, principal ID, and role definition, so a replacement identity produces a different role-assignment resource. An incremental ARM deployment that declares the new assignment does **not** automatically delete an older assignment that is no longer declared.

```text
new collector principal authorized
!= old collector principal revoked
```

Before and after any collector-identity change, the workflow must inventory publication roles, identify obsolete collector principals from governed evidence, require explicit approval for each removal, delete only those approved obsolete assignments, and verify they are absent.

Effective permission is proven only when the current collector publishes a fresh envelope and the result is fetched and validated from the Blob service URL.

## Network paths

- Browser read path: HTTPS from the exact allowed GitHub Pages origin to the Azure Blob service endpoint.
- Collector write path: HTTPS to Azure Blob Storage using managed-identity OAuth.
- Collector token path: link-local Azure Instance Metadata Service, available only from the VM.
- No browser path to the private collector endpoint is created.
- No public IP, inbound NSG rule, load-balancer rule, peering, route, DNS record, or collector listener change is required.

Blob-service CORS remains an exact HTTPS-origin allowlist. Wildcard origins are prohibited.

CORS is a browser response policy, not authentication. The report object is intentionally public and can be fetched directly by any client that knows its URL.

## Security controls

The module enforces:

- a dedicated Storage account containing only sanitized public output;
- HTTPS-only traffic and TLS 1.2 minimum;
- shared-key authorization disabled;
- OAuth as the default write authentication;
- account-level anonymous Blob access enabled only because this dedicated public-output account requires it;
- `$web` container access set to `Blob`, permitting anonymous object reads without anonymous container enumeration;
- exact-origin Blob-service CORS limited to `GET`, `HEAD`, and `OPTIONS`;
- Blob versioning and seven-day soft-delete retention;
- deterministic Storage-scope RBAC for the current collector principal;
- sanitized public envelope projection;
- generation and expiry metadata for stale-data detection.

```text
allowBlobPublicAccess = true
+ $web publicAccess = Blob
+ dedicated sanitized-output account
!= all Storage data is public
```

No other container is granted anonymous access. Adding raw evidence, credentials, private addresses, customer-sensitive identifiers, or unrestricted user content to this account is prohibited.

The static website remains enabled to provision the `$web` container, but `publicReportUrl` resolves through `primaryEndpoints.blob`. The static-website endpoint is not the browser integration contract.

## Cost implications

Expected cost is limited to a small Standard LRS Storage account, stored report versions, requests, egress, and no new compute. That expectation is architectural, not current price evidence.

The read-only planner records:

- a maximum monthly ceiling of CAD 10;
- that ARM validation and What-If do not provide a current quotation;
- that deployment remains blocked until fresh region- and subscription-relevant price evidence is reviewed.

```text
expected low cost
!= current quotation
!= actual cost
```

No deployment should proceed when the reviewed estimate exceeds the approved ceiling or when current price evidence is missing. Quota and policy availability also require fresh Azure evidence.

## Read-only planning method

Run after authenticating in an explicitly authorized **read-only planning session**:

```bash
infra/scripts/plan_existing_collector_report_publication.sh \
  --resource-group rg-servicetracer-dev-westus2 \
  --location westus2 \
  --prefix mst \
  --environment dev \
  --allowed-origin https://anthonyedgar30000.github.io \
  --artifact-dir existing-collector-publication-plan \
  --maximum-monthly-cost-cad 10.00
```

The script performs Azure reads, ProviderNoRbac ARM validation, and What-If only. It contains no deployment, RBAC creation, VM Run Command, or deletion command.

Expected outputs include current Azure context, resource-group and collector observations, Storage and RBAC inventories, deployment parameters, ARM validation, exact What-If, cost boundary, and plan summary.

Raw role-assignment files are protected planning evidence because unrelated principal and scope metadata may be present. Public evidence should contain only the reviewed, sanitized classification needed to support the decision.

A successful plan is evidence that the template was evaluated against a specific observed Azure context. It is not deployment evidence and grants no execution authority.

## Future deployment method

The inactive candidate at `infra/workflow-designs/existing-collector-report-publication.yml` defines the promotion contract. It cannot run from GitHub Actions in its present location and intentionally fails closed before authentication.

A separate authority-changing pull request must promote a reviewed implementation into `.github/workflows`. The promoted workflow must preserve this order:

1. validate exact reviewed commit, bounded inputs, current cost evidence, and typed confirmation;
2. authenticate through the protected environment;
3. re-resolve Azure context and collector identity;
4. capture prechange Storage and complete visible RBAC inventory;
5. classify current and obsolete collector-principal publication assignments;
6. rerun Provider validation and exact What-If with the execution identity;
7. obtain human approval of the exact plan, current cost evidence, and any explicitly identified obsolete-role removal;
8. deploy only the dedicated template for the current principal;
9. verify Storage security, account anonymous-access setting, `$web` Blob-only access, CORS, retention, versioning, outputs, and current role scope;
10. publish a fresh sanitized envelope through the current collector identity;
11. fetch and validate the envelope from the Blob service URL with the reviewed Origin header;
12. remove only explicitly approved obsolete collector-principal assignments;
13. verify no obsolete publication assignment remains;
14. test the frontend with the query-string report override;
15. capture non-secret evidence;
16. commit the verified URL to `docs/report-source.json` in a later repository-only increment.

## Validation commands and expected evidence

Repository validation:

```bash
python .project/validate.py
python -m unittest infra.tests.test_report_publication
python -m unittest infra.tests.test_existing_collector_report_publication
bicep build infra/report-publication-existing-collector.bicep --stdout >/dev/null
```

Future Azure validation must prove:

- the exact What-If contains only the four reviewed publication creations;
- no collector VM, NIC, disk, image, extension, network, load balancer, backend, or Log Analytics resource changes;
- account anonymous Blob access is enabled only on the dedicated sanitized-output account;
- `$web` has Blob-only anonymous access and does not permit container enumeration;
- the Blob service CORS rule exactly matches the reviewed origin and methods;
- the current role assignment scope equals the new Storage account;
- no unapproved or obsolete collector-principal publication role remains;
- the publisher succeeds using managed identity rather than shared key or embedded secret;
- the fetched object matches `servicetracer.public-report.v1`;
- source ID, ServiceTracer version, `generated_at`, and `expires_at` are present;
- the report is fresh at browser fetch time;
- raw evidence and secrets are absent;
- the console displays live provenance rather than `Controlled demo fixture`.

## Failure behavior

Stop without deployment when:

- tenant, subscription, resource group, region, tags, collector identity, or reviewed inputs differ;
- multiple or unexpected report Storage resources exist;
- ARM validation or What-If fails;
- What-If differs from the reviewed four-create allowlist or includes protected resources;
- current price evidence is missing or exceeds the approved ceiling;
- deployment permission is missing or broader than reviewed;
- explicit mutation authorization is absent;
- the collector publisher preflight fails.

After deployment, treat publication, CORS, schema, freshness, content-equality, or browser verification failure as an unsuccessful change. Do not point `docs/report-source.json` at an unverified endpoint and do not suppress fixture labeling.

## Rollback and cleanup

Rollback is bounded to resources introduced by this increment:

1. capture failed verification evidence;
2. remove the new current-principal Storage-scope role assignment;
3. delete the dedicated report Storage account after preserving required non-secret evidence;
4. verify the Storage account, Blob service, `$web` container configuration, and role assignment are absent;
5. verify collector compute, disks, identity, networking, load balancer, backends, and Log Analytics are unchanged;
6. preserve the GitHub Pages fixture configuration.

No collector replacement, restart, deallocation, disk action, NIC action, or guest rollback is part of this publication rollback.

## Evidence to capture

- exact repository commit and promoted workflow revision;
- approval record and typed confirmation;
- target tenant/subscription fingerprint, resource group, region, and tags;
- collector resource ID and current principal fingerprint;
- prechange Storage and complete visible RBAC inventory;
- ARM validation and exact What-If;
- current price source, timestamp, estimate, and approved ceiling;
- deployment outputs and resource IDs;
- postdeployment account, Blob service, `$web` access level, CORS, retention, versioning, and role scope;
- collector publication result without access token or raw evidence;
- public-envelope digest, source metadata, generation time, expiry, Origin header, CORS response, and fetch result;
- frontend screenshot showing live source and evidence age;
- rollback or cleanup evidence when applicable.

## Claim boundary

This design can eventually prove that the frontend ingested a fresh report generated from real Azure observations and published by the current collector identity. It does not prove an exact device root cause or that every virtual-infrastructure component is production-grade.

```text
controlled scenario
+ real Azure resources
+ real frontend transactions
+ current Azure metrics
+ deterministic analysis
+ fresh provenance-bearing Blob publication
!= static fixture simulation
```
