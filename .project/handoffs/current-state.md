# Current project handoff

## Interpretation boundary

This handoff records the accepted architecture, promoted evidence, unresolved gates, and safe next decision boundary after a full repository and evidence reconciliation on `2026-07-23`.

It is not a live GitHub or Azure dashboard. Query the current default-branch head, pull requests, branch ownership, exact-head CI, and Azure state whenever it is read.

```text
durable_handoff != live_status
promoted_evidence != current_Azure_state
declared_in_code != deployed_in_Azure
resource_exists != service_healthy
failed_deploy != proof_of_zero_partial_mutation
```

## Repository synchronization watermark

The branch was rebased onto the live repository state containing:

- `main@ffe83c2966985dc4fa4d736d178ade9e9fd085b7`;
- PR #59, **Fix collector demo API deployment name collision**;
- PR #58, **Add governed persistence controller**;
- PR #57, **Supersede stale backend deployment fact**;
- PR #56, **Isolate collector demo API from base infrastructure**.

Exact PR-head CI:

- PR #56 run `30041552071`: success;
- PR #57 run `30042254963`: success;
- PR #58 run `30042848348`: success;
- PR #59 run `30045980827`: success.

A local clone, uncommitted working tree, unpushed branch, or local Azure CLI context is not observable through the GitHub connector and must be inspected separately.

## Current active architecture

The active demo strategy is collector-hosted and does not use Microsoft.Web:

```text
GitHub Pages
→ dedicated Azure public IP and DNS
→ second frontend on the existing Standard Load Balancer
→ IP-based backend pool targeting collector private IP 10.20.40.10
→ Nginx TLS termination and rate limiting
→ loopback-only Python API on 127.0.0.1:8090
→ existing remote-access transaction endpoint
→ synthetic VPN-01 / VPN-02 backends
```

Repository implementation includes:

- `.github/workflows/collector-demo-api.yml`;
- `infra/collector-demo-api.bicep`, the isolated deployment root;
- distinct parent and nested ARM deployment names;
- a bounded What-If classifier;
- a typed readiness assessor;
- the hardened installer and standalone API;
- deterministic service verification;
- the Governed Persistence Loop controller.

The legacy Azure Function/App Service workflow is retired from the active path.

## Azure reality established by evidence

### Collector and dependencies

The newest authenticated Azure observation is collector-hosted demo API deploy run `30044644501`, generated at `2026-07-23T21:05:01Z`.

Before deployment it observed:

- subscription type: Azure for Students;
- resource group: `rg-servicetracer-dev-westus2`;
- region: `westus2`;
- collector VM: `vm-stcollector-mst-dev`;
- collector power state: running;
- collector size: `Standard_B2ats_v2`;
- collector private IP: `10.20.40.10`;
- collector public IP: none;
- dedicated demo API public IP: not present;
- Public IP Addresses quota: 1 used, 3 limit, 2 remaining;
- resource-group read-only locks: none.

These are time-bounded control-plane facts. They do not prove current guest health, running ServiceTracer version, evidence-disk readability, publisher availability, effective permissions, actual cost, or post-failure target-resource state.

### Backend VMs and legacy partial mutation

Retired App Service run `30029515018` partially mutated Azure before Microsoft.Web quota failure.

Promoted evidence records:

- two synthetic backend VMs exist;
- Application Insights `appi-demo-api-mst-dev` exists;
- storage account `storfxczr3fewce` exists;
- the Function plan was not established;
- the Function App was not established;
- listeners and transaction behavior remain unverified.

Cleanup is not authorized by this handoff.

### Broad planning failure and isolated-root repair

Run `30040676542` passed readiness and ARM validation but used the broad base template. Its What-If predicted:

```text
Create    9
Modify   13
Ignore   11
NoChange  5
```

Protected collector, disk, NIC, VNet, subnet, load-balancer, NSG, and public-IP modifications caused the workflow to fail closed.

PR #56 introduced the isolated root `infra/collector-demo-api.bicep`.

### Accepted isolated plan and failed deploy

Run `30044644501` used the isolated root.

It established:

- readiness passed;
- ARM validation passed;
- nine isolated Create changes;
- no protected base-infrastructure modifications classified;
- the isolated What-If status was `accepted_isolated_collector_api_changes`;
- deployment was explicitly authorized for that run.

The deployment command then failed because the parent CLI deployment and nested Bicep module both used:

```text
collector-demo-api-dev
```

`deployment-result.json` is empty and service verification was skipped.

```text
isolated_WhatIf_accepted = true
deployment_attempted      = true
deployment_succeeded      = false
post_failure_mutation     = not_proven
service_verified          = false
```

PR #59 changed only the nested deployment name to:

```text
collector-demo-api-resources-dev
```

That repository fix does not prove the Azure fix executed. Because the template changed and the failed run does not prove zero partial mutation, a fresh Azure inventory and isolated What-If are required before a retry decision.

## Frontend configuration reality

No live report or demo API URL is committed. The controlled fixture remains the default.

After an authorized deployment, a verified endpoint can be tested without repository promotion:

```text
?api=https://<verified-fqdn>/api/demo/run
```

A live URL may be committed only after public-IP existence, DNS, TLS, API health, 20 correlated transactions, CORS, provenance, and browser rendering are verified.

## Report-publication workstream

Read-only planner run `29979955391` remains the promoted evidence for the separate publication path. It produced four Create changes, no Modify/Delete/Replace, and no Azure mutation.

The report Storage account, Blob configuration, `$web` access, data role, managed-identity upload, Blob response, and live browser rendering are not deployed or verified.

The only durable authority grant remains the read-only publication planner. It does not authorize collector demo API planning, deployment, or cleanup.

## Collector replacement and recovery

Replacement and recovery contracts are implemented and CI-verified but inactive.

Promoted evidence records:

- deployed Ubuntu 22.04 versus desired Ubuntu 24.04 image drift;
- evidence-disk preservation requirements;
- collector NIC delete-on-VM-delete risk;
- system-assigned identity turnover;
- no visible publication role assignments at the recorded time;
- OS-disk public-network hardening required.

No current recovery point, isolated boot rehearsal, rollback execution, or disaster-recovery proof exists.

## Cost and quota boundary

Promoted evidence supports only bounded planning claims:

- Public IP quota was 1 of 3 at `2026-07-23T21:05:01Z`;
- an earlier two-backend-VM estimate was approximately CAD 19.42 for 730 hours;
- current invoice cost, remaining student credit, taxes, discounts, and complete allocation are not observable;
- backend VMs and partial resources may continue to incur cost.

## Security and identity boundary

The isolated design keeps the collector NIC private and exposes only load-balanced HTTP/HTTPS. The API binds to loopback behind Nginx, restricts CORS to the exact GitHub Pages origin, caps request bodies, rate-limits requests, and accepts no caller-controlled backend target.

Those are declared controls, not runtime proof.

Current Azure Policy, deny assignments, effective permissions, guest hardening, certificate issuance, NSG effectiveness, and endpoint behavior require fresh verification.

## Governed Persistence Loop

PR #58 adds deterministic support for:

- `proceed`;
- `fix`;
- `sync_with_reality`;
- `restrategize`;
- `verify`;
- `rollback`;
- `escalate`;
- `complete`.

The controller recommends typed messages while preserving objective, scope, and authority. It does not dispatch workflows or grant authority.

Current transition:

```text
isolated_plan_accepted
→ deploy_failed_name_collision
→ PR59 bounded fix merged
→ fresh reality sync and isolated What-If required
```

## Safe next bounded operation

After this repository-only reconciliation is reviewed and merged:

1. resolve the new live GitHub head and exact post-merge CI;
2. inspect local working-tree and Azure CLI context separately;
3. obtain explicit authorization for one read-only `what-if` dispatch;
4. use the exact reviewed commit containing PR #59 and the isolated root;
5. capture post-failure target-resource inventory, quota, locks, ARM validation, and full What-If;
6. reject any unexpected Create or any protected Modify/Delete/Replace;
7. stop for a separate deployment decision.

No deployment retry, cleanup, report publication, collector replacement, rollback, or recovery is part of this synchronization.
