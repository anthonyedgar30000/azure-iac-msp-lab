# Existing-collector public report publication design

## Decision

Deploy the sanitized ServiceTracer public-report endpoint independently from collector compute. The publication increment consumes the **currently observed system-assigned managed-identity principal ID** of the existing collector and creates only the dedicated Azure Storage configuration and its narrowly scoped Blob data role assignment.

```text
existing collector identity
!= collector VM redeployment

report endpoint deployed
!= live report published

live report published
!= incident root cause proven
```

This avoids routing a small presentation-layer requirement through the collector replacement path. The current collector image differs from the desired image contract, so an ordinary deployment that also manages collector compute is not an acceptable way to add report publication.

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
dedicated Azure Storage $web container
        ↓
GitHub Pages operator console fetch with no-store
```

The browser receives only the bounded public envelope. Raw evidence, bearer tokens, private collector endpoints, Azure credentials, customer identifiers, and exact-root-cause claims are not publication inputs.

## Region and resource scope

- Existing resource group: `rg-servicetracer-dev-westus2` after fresh verification.
- Expected region: `westus2` after fresh verification.
- Existing collector name: `vm-stcollector-mst-dev` for the current dev naming contract.
- New mutable scope: one deterministic report Storage account, its Blob service configuration, and one Storage-scope role assignment for the currently verified collector principal.
- Explicitly protected: collector VM, NIC, OS disk, evidence disk, image, extensions, guest configuration, load balancer, backend VMs, network topology, budgets, alerts, and unrelated RBAC.

The dedicated template is `infra/report-publication-existing-collector.bicep`. It accepts an externally resolved collector principal ID and invokes only `infra/modules/report_publication.bicep`.

## Dependencies

Before any future deployment:

1. Resolve live GitHub `main`, pull-request, and exact-head CI state.
2. Authenticate to the intended Azure tenant and subscription using workload identity federation.
3. Verify the resource-group name, region, workload tag, and purpose tag.
4. Verify the existing collector exists with `provisioningState: Succeeded`.
5. Re-resolve its current system-assigned principal ID; never copy the historical value from documentation.
6. Capture report Storage resources and all visible role assignments at resource-group and report-Storage scope, then classify assignments for the current collector principal versus obsolete collector principals.
7. Run ARM validation and exact What-If against the dedicated template.
8. Obtain fresh region-appropriate price evidence and explicit cost review.
9. Obtain explicit human authorization for the Azure mutation and for any separately identified obsolete-role revocation.

The repository-only increment does not satisfy steps 2 through 9.

## Identity and permissions

### Deployment identity

A future promoted workflow should use GitHub OIDC and a protected `azure-lab` environment. Its Azure role must be bounded to the target resource group and sufficient only to deploy the report Storage resources and role assignment. The exact deployment identity and effective permissions require fresh verification before promotion.

### Collector identity

The existing collector uses a system-assigned managed identity. The future workflow must read its current `principalId` immediately before validation and again before deployment. A mismatch between reviewed planning evidence and predeployment identity is a stop condition.

The collector receives **Storage Blob Data Contributor** only at the dedicated report Storage account. No subscription-wide, resource-group-wide, VM-management, network-management, or secret-management role is introduced by this design.

A system-assigned identity changes when the VM is replaced. The role-assignment resource name is derived from the Storage account, principal ID, and role definition, so a replacement identity produces a different role-assignment resource. An incremental ARM deployment that declares the new assignment does **not** automatically delete an older assignment that is no longer declared.

```text
new collector principal authorized
!= old collector principal revoked
```

Before and after any collector-identity change, the workflow must inventory publication roles, identify obsolete collector principals from governed evidence, require explicit approval for each removal, delete only those approved obsolete assignments, and verify they are absent. An unexplained or unapproved obsolete Storage data role is a security blocker, not harmless residue.

```text
role assignment exists
!= effective permission verified
```

Effective permission is proven only when the current collector publishes a fresh envelope and the result is fetched and validated from the public URL.

## Network paths

- Browser read path: HTTPS from the exact allowed GitHub Pages origin to the Azure Storage static website endpoint.
- Collector write path: HTTPS to Azure Blob Storage using managed-identity OAuth.
- Collector token path: link-local Azure Instance Metadata Service, available only from the VM.
- No browser path to the private collector endpoint is created.
- No public IP, inbound NSG rule, load-balancer rule, peering, route, DNS record, or collector listener change is required.

CORS must remain an exact HTTPS-origin allowlist. Wildcard origins are prohibited.

## Security controls

The existing module enforces:

- HTTPS-only traffic and TLS 1.2 minimum;
- shared-key authorization disabled;
- OAuth as the default write authentication;
- blob public access disabled;
- exact-origin CORS limited to `GET`, `HEAD`, and `OPTIONS`;
- Blob versioning and seven-day soft-delete retention;
- deterministic Storage-scope RBAC for the current collector principal;
- sanitized public envelope projection;
- generation and expiry metadata for stale-data detection.

The Storage static website is intentionally public for the bounded report object, while account-level anonymous Blob access remains disabled. That distinction must be verified against actual Azure behavior before claiming the endpoint operational.

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

No deployment should proceed when the reviewed estimate exceeds the approved ceiling or when current price evidence is missing.

## Repository-only planning method

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

The script performs Azure reads, ARM validation, and What-If only. It contains no deployment, RBAC creation, VM Run Command, or deletion command.

## Expected planning outputs

- `azure-context.json`
- `resource-group.json`
- `existing-collector.json`
- `existing-report-storage.json`
- `visible-resource-group-role-assignments-all.json`
- `visible-report-storage-role-assignments-all.json`
- `visible-collector-role-assignments.json`
- `deployment-parameters.json`
- `arm-validation.json`
- `arm-what-if.json`
- `cost-boundary.json`
- `plan-summary.json`

The raw role-assignment files are protected planning evidence because unrelated principal and scope metadata may be present. Public evidence should contain only the reviewed, sanitized classification needed to support the decision.

A successful plan is evidence that the template was evaluated against a specific observed Azure context. It is not deployment evidence and grants no execution authority.

## Future deployment method

The inactive candidate at `infra/workflow-designs/existing-collector-report-publication.yml` defines the promotion contract. It cannot run from GitHub Actions in its present location and intentionally fails closed before authentication.

A separate authority-changing pull request must promote a reviewed implementation into `.github/workflows`. The promoted workflow must preserve this order:

1. validate exact reviewed commit, bounded inputs, current cost evidence, and typed confirmation;
2. authenticate through the protected environment;
3. re-resolve Azure context and collector identity;
4. capture prechange Storage and complete visible RBAC inventory;
5. classify current and obsolete collector-principal publication assignments;
6. rerun validation and What-If;
7. obtain human approval of the exact plan, current cost evidence, and any explicitly identified obsolete-role removal;
8. deploy only the dedicated template for the current principal;
9. verify Storage security, CORS, retention, versioning, outputs, and current role scope;
10. publish a fresh sanitized envelope through the current collector identity;
11. fetch and validate the envelope from the public URL;
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

- the deployment changed only the intended Storage and current-principal role-assignment resources;
- no collector VM, NIC, disk, image, extension, network, load balancer, or backend resource changed;
- the current role assignment scope equals the new Storage account;
- no unapproved or obsolete collector-principal publication role remains;
- the publisher succeeds using managed identity rather than shared key or embedded secret;
- the public object matches `servicetracer.public-report.v1`;
- source ID, ServiceTracer version, `generated_at`, and `expires_at` are present;
- the report is fresh at browser fetch time;
- raw evidence and secrets are absent;
- the console displays live provenance rather than `Controlled demo fixture`.

## Failure behavior

Stop without deployment when:

- tenant, subscription, resource group, region, or tags differ from the reviewed target;
- the collector is absent, not succeeded, or lacks the expected system-assigned identity;
- the principal ID changes after review;
- multiple unexpected report Storage resources exist;
- an obsolete publication role cannot be tied to governed identity evidence or lacks explicit removal approval;
- ARM validation or What-If fails;
- What-If includes protected resources;
- current price evidence is missing or exceeds the approved ceiling;
- effective deployment permissions are broader or narrower than reviewed;
- explicit mutation authorization is absent.

After deployment, treat publication, obsolete-role cleanup, or browser verification failure as an unsuccessful change. Do not point `docs/report-source.json` at an unverified endpoint and do not suppress fixture labeling.

## Rollback and cleanup

Rollback is bounded to the resources introduced by this increment:

1. capture failed verification evidence;
2. remove the new current-principal Storage-scope role assignment;
3. delete the dedicated report Storage account only after preserving any required non-secret evidence;
4. verify both resources are absent;
5. verify the collector VM, NIC, OS disk, evidence disk, identity, load balancer, and backend resources are unchanged;
6. preserve the GitHub Pages fixture configuration.

An obsolete assignment removed only after successful current-principal publication is not silently recreated during rollback. Its disposition must remain recorded in the authorization and evidence package. Any rollback that would reauthorize an obsolete identity requires a new explicit security decision.

No collector replacement, restart, deallocation, disk action, NIC action, or guest rollback is part of this publication rollback.

## Evidence to capture

- exact repository commit and promoted workflow revision;
- approval record and typed confirmation;
- Azure tenant and subscription identifiers, appropriately redacted for public evidence;
- target resource group, region, and tags;
- collector resource ID and current principal ID fingerprint;
- prechange Storage and complete visible RBAC inventory;
- sanitized classification of current and obsolete collector publication assignments;
- explicit approval and deletion evidence for each obsolete assignment removed;
- ARM validation and exact What-If;
- current price source, timestamp, estimate, and approved ceiling;
- deployment outputs and resource IDs;
- postdeployment Storage configuration and current role scope;
- proof that no obsolete publication role remains;
- collector publication result without access token or raw evidence;
- public-envelope digest, source metadata, generation time, expiry, and fetch result;
- frontend screenshot showing the live source and evidence age;
- rollback or cleanup evidence when applicable.

## Claim boundary

This design can eventually prove that the frontend ingested a fresh report generated from real Azure observations and published by the current collector identity. It does not convert an engineered lab fault into an uncontrolled production incident, prove an exact device root cause, or prove that every virtual-infrastructure component is production-grade.

The defensible demonstration claim is:

```text
controlled scenario
+ real Azure resources
+ real frontend transactions
+ current Azure metrics
+ deterministic analysis
+ fresh provenance-bearing publication
!= static fixture simulation
```
