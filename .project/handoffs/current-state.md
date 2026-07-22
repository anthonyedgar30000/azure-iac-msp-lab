# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and fresh Azure evidence determine implementation and runtime reality.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Repository observation

- Default branch: `main`.
- Observed `main` before this branch opened: `e6dcb9a2cf1ba05620a294137fea5e21f8dba1ed`, the PR #36 merge commit.
- Open pull requests observed before branch creation: zero.
- Last substantive repository-design baseline: PR #34 merge commit `36010582460b393c0667e274144d9700e78721bf`.
- The stored observation is time-bounded. Query live GitHub for current head, pull requests, and CI.

```text
last_substantive_baseline
!= repository_observation.main_head
!= current_repository_head
```

## Authored change

- Change: `existing-collector-report-publication`.
- Branch: `feat/existing-collector-report-publication`.
- Pull request: #37, recorded as authored-change metadata only; live status remains external GitHub evidence.
- Authority: repository design and read-only planning only.
- Objective: prepare a safe publication path that uses the existing collector managed identity without redeploying or replacing collector compute.

Permitted paths:

- `infra/report-publication-existing-collector.bicep`;
- `infra/scripts/plan_existing_collector_report_publication.sh`;
- `infra/workflow-designs/existing-collector-report-publication.yml`;
- `infra/tests/test_existing_collector_report_publication.py`;
- `docs/designs/existing-collector-public-report.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Protected scope includes `.github/workflows/**`, the existing collector VM, NIC, OS disk, evidence disk, image, extensions, network, load balancer, backend VMs, application source, credentials, live evidence, budgets, alerts, and all Azure resources.

## Intended architecture

```text
real Azure transactions and probe metrics
        ↓
ServiceTracer deterministic analysis
        ↓
sanitized provenance-bearing public envelope
        ↓
existing collector system-assigned identity
        ↓
dedicated Azure Storage report endpoint
        ↓
GitHub Pages operator console
```

This increment implements only the repository design and read-only planning boundary. It does not deploy the endpoint or prove that the browser consumed live data.

## Decoupling rule

The existing lifecycle deployment couples `deployPublicReportEndpoint` to `deployOperationsCollector=true`. That is not safe for this increment because the deployed collector uses Ubuntu 22.04 while the desired contract uses Ubuntu 24.04 and replacement is separately governed.

The dedicated template therefore:

- accepts a freshly resolved existing collector principal ID;
- invokes only the report-publication module;
- creates no VM, NIC, disk, image, extension, load-balancer, backend, or network resource;
- exports the Storage account, static website endpoint, public report URL, and role-assignment ID.

```text
report endpoint deployment
!= collector replacement
```

## Read-only planner

`infra/scripts/plan_existing_collector_report_publication.sh` is designed to:

1. capture current subscription and tenant context;
2. verify the existing resource group, region, and tags;
3. resolve the existing collector and its current system-assigned principal ID;
4. capture report Storage and complete visible RBAC state at resource-group and report-Storage scope;
5. produce a collector-principal role-assignment subset without discarding the raw evidence;
6. run ARM validation and exact What-If against the dedicated template;
7. record that current price evidence remains unresolved;
8. emit a plan summary proving no deployment authorization and no Azure mutation.

The script must not contain deployment, role-assignment creation, VM Run Command, or deletion commands. Raw role-assignment inventories are protected evidence and require sanitization before public use.

## Inactive workflow design

`infra/workflow-designs/existing-collector-report-publication.yml` is intentionally outside `.github/workflows` and cannot be dispatched. Its first job fails closed before authentication or mutation, and its candidate phase contract is disabled.

Promotion requires a separate authority-changing pull request after:

- exact-head CI and review;
- fresh Azure context and collector identity evidence;
- exact What-If review;
- current region-appropriate cost evidence;
- explicit human mutation authorization;
- a reviewed rollback and cleanup procedure.

## Security and identity boundary

- Browser reads use HTTPS from the exact GitHub Pages origin.
- Collector writes use managed-identity OAuth to Azure Blob Storage.
- Shared-key authorization remains disabled.
- CORS remains an exact HTTPS-origin allowlist; wildcard origins are prohibited.
- The collector role is Storage Blob Data Contributor at the dedicated Storage account only.
- No browser route to the private collector is introduced.
- No credential, token, private endpoint, raw evidence, or exact-root-cause claim belongs in the public envelope.

A system-assigned principal changes when the collector VM is replaced. Because the deterministic role-assignment name includes the principal ID, deploying a role for the new identity does not remove the old identity's assignment in incremental ARM mode.

```text
new collector principal authorized
!= old collector principal revoked
```

A promoted workflow must classify current and obsolete publication assignments, require explicit approval for each obsolete-role removal, verify the current collector can publish first, remove only approved obsolete assignments, and then prove no obsolete publication role remains. Unexplained or unapproved stale access is a security blocker.

```text
RBAC assignment
!= effective permission verified
```

Effective permission is proven only by a successful current-identity publication and validated browser fetch after a separately authorized deployment.

## Latest Azure evidence boundary

The latest promoted Azure control-plane evidence remains read-only planner run `29856203054`, observed July 21, 2026.

At that observation:

- resource group: `rg-servicetracer-dev-westus2`;
- region: `westus2`;
- collector VM: `vm-stcollector-mst-dev`;
- VM size: `Standard_B2ats_v2`;
- deployed image: Ubuntu 22.04;
- desired image: Ubuntu 24.04;
- evidence disk: attached with `deleteOption: Detach`;
- production NIC: static address and VM `deleteOption: Delete`;
- system-assigned identity: present;
- visible role assignments in that planner result: none;
- Azure mutations: not authorized and not performed.

This branch does not refresh tenant, subscription, resource, RBAC, guest, quota, pricing, report Storage, public endpoint, or browser state.

```text
repository design
!= deployed Azure reality

historical principal observation
!= current principal ID

frontend live-report support
!= live endpoint configured
```

## Cost boundary

The expected resource set is one Standard LRS Storage account, report versions, requests, egress, and one role assignment, with no new compute. That expectation is not a current quotation.

- Current price evidence is required before deployment.
- The planning ceiling is CAD 10 monthly for this bounded endpoint.
- ARM validation and What-If do not prove current price or actual cost.
- Missing or excessive cost evidence is a deployment blocker.

## Verification gates

Before this repository-only pull request is ready to merge:

1. confirm PR #37 is recorded as authored-change metadata;
2. confirm the final diff is limited to the declared paths;
3. run workflow-observability validation;
4. run the existing and new report-publication tests, including shell syntax validation;
5. pass Bicep lint and build for the dedicated template;
6. inspect every exact-head CI job;
7. obtain a repository-design, security/identity, and cost-boundary review of the exact passing head;
8. preserve the statement that no Azure connection or mutation occurred;
9. obtain Anthony Edgar's explicit merge authorization.

## Failure and rollback behavior

If validation or CI fails:

1. keep the pull request draft;
2. inspect the exact failing job and logs;
3. patch only the declared paths;
4. obtain fresh exact-head CI;
5. do not activate the workflow, add credentials, remove cost gates, or couple the change back to collector deployment.

Repository rollback is closing the pull request without merge or reverting its commits. No Azure rollback applies because this increment performs no Azure authentication or mutation.

A future deployment rollback must remove only the new current-principal role assignment and dedicated report Storage account, preserve required non-secret evidence, and verify the collector VM, NIC, disks, identity, load balancer, backends, and network are unchanged. An obsolete assignment removed after explicit approval is not silently recreated; reauthorization requires a new security decision.

## Claim boundary

After this branch, the repository may claim that a decoupled existing-collector publication design and read-only planning path exist and are CI-verified. It may not claim that the endpoint is deployed, the collector can publish to it, the browser consumed live data, the observed incident is current, or the scenario is no longer controlled.

The eventual defensible demonstration claim is:

```text
controlled scenario
+ real Azure resources
+ real transactions
+ current Azure metrics
+ deterministic analysis
+ fresh provenance-bearing publication
!= static fixture simulation
```
