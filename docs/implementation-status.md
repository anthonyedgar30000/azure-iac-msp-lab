# Implementation status

## State model

This document is a durable status summary, not a live GitHub or Azure dashboard.

```text
implemented != CI_verified != deployed != operationally_verified
deployment_failed != no_Azure_mutation
resource_exists != service_healthy
```

Live repository, CI, and Azure state must be queried when consequential decisions are made.

## Repository implementation and CI

Implemented on `main` and exact-head CI verified:

- repository-native workflow observability and six canonical ServiceTracer workstreams;
- HELIX retrieval and archive governance;
- segmented Azure network, Standard Load Balancer, Log Analytics, collector VM, evidence-disk, identity, and lifecycle IaC;
- deterministic ServiceTracer collector, evidence spool, adapters, transaction assembly, localization, containment, technician handoff, public-report sanitizer, and operator console;
- fail-closed collector replacement and recovery designs, schemas, validation, and tests;
- read-only existing-collector report-publication planning and readiness workflows;
- bounded publication execution workflow, not dispatched;
- synthetic VPN backend infrastructure and deterministic transaction contracts;
- retired legacy Azure Function/App Service demo path;
- active collector-hosted demo API workflow;
- isolated collector-hosted API Bicep root;
- typed collector readiness and What-If classifiers;
- hardened Nginx/systemd installer and loopback-only API;
- Governed Persistence Loop controller supporting `proceed`, `fix`, `sync_with_reality`, `restrategize`, `verify`, `rollback`, `escalate`, and `complete`.

The latest substantive repository capability is PR #58. PR #57 then corrected the durable backend deployment fact. Their exact PR-head CI runs passed.

The final merge commit may not have a separate attached CI observation; exact PR-head CI and post-merge CI are distinct evidence.

## Azure resources observed

### Operations collector

Time-bounded authenticated evidence has observed:

- resource group `rg-servicetracer-dev-westus2` in `westus2`;
- collector `vm-stcollector-mst-dev`;
- running power state;
- `Standard_B2ats_v2`;
- private IP `10.20.40.10`;
- no collector public IP;
- separately managed 32 GiB evidence disk;
- system-assigned identity;
- deployed Ubuntu 22.04 image line while the desired contract uses Ubuntu 24.04.

The newest authenticated control-plane observation is deploy run `30044644501` at `2026-07-23T21:05:01Z`.

Current guest service health, ServiceTracer version, evidence readability, publisher availability, and effective permissions were not reverified.

### Synthetic backend VMs

Two private VPN backend VMs were observed after the failed legacy deployment.

Their existence is proven only at the Azure control-plane boundary. These remain unverified:

- listener services;
- backend-pool behavior;
- `/healthz`;
- correlated `/transaction` outcomes;
- VPN-01 success behavior;
- VPN-02 bounded simulated timeout behavior;
- comparative failure rate.

### Legacy partial App Service resources

The retired deployment attempt in run `30029515018` partially mutated Azure before failing on Microsoft.Web quota.

Observed partial resources:

- Application Insights `appi-demo-api-mst-dev`;
- storage account `storfxczr3fewce`.

Not established:

- App Service or Function plan;
- Function App;
- live Function API;
- service verification.

Cleanup is pending a separate explicit authority decision.

## Collector-hosted demo API

### Intended architecture

```text
GitHub Pages
→ dedicated Azure public IP and DNS
→ second frontend on existing Standard Load Balancer
→ IP-based backend pool for collector 10.20.40.10
→ Nginx TLS and rate limiting
→ loopback Python API
→ existing remote-access transaction endpoint
→ synthetic VPN backends
```

### Latest Azure planning and deployment result

Run `30040676542` first proved that the broad base template was unsafe: it predicted protected collector, disk, NIC, load-balancer, public-IP, VNet, subnet, and NSG modifications. PR #56 then introduced the isolated root.

Deploy run `30044644501` used the isolated root and established:

- Azure authentication and dependency inventory succeeded;
- readiness passed;
- Public IP quota was 1 of 3;
- no resource-group read-only lock was observed;
- ARM validation passed;
- nine isolated Create changes were accepted;
- no protected base-infrastructure modifications were classified;
- deployment was explicitly authorized for that run.

The deployment command failed because the parent CLI deployment and nested Bicep module shared the name `collector-demo-api-dev`. The deployment result file is empty and service verification was skipped.

PR #59 changed the nested deployment name to `collector-demo-api-resources-${environment}` and added a regression test.

### Current proof boundary

```text
isolated_deployment_root_implemented = true
isolated_WhatIf_observed             = true
isolated_WhatIf_accepted             = true
deployment_attempt_observed          = true
deployment_succeeded                 = false
post_failure_mutation_state          = not_proven
TLS_verified                         = false
API_health_verified                  = false
transactions_verified                = false
CORS_verified                        = false
frontend_live_verified               = false
```

The accepted plan applies to the pre-PR #59 commit. The name repair changes the template, and the failed deployment does not prove zero partial mutation. A fresh inventory and isolated What-If are required before any separately authorized retry.

The repository commits no live demo API URL. The controlled fixture remains the default. A query-string override is the bounded pre-promotion test path after deployment.

## Report-publication workstream

Read-only planner run `29979955391` remains the promoted publication evidence:

- four reviewed Create changes;
- zero Modify, Delete, or Replace;
- no Azure mutation.

Not established:

- dedicated report Storage deployment;
- Blob-service configuration;
- `$web` Blob-only access;
- collector data-role assignment;
- managed-identity publication;
- Blob response and exact CORS behavior;
- live report URL promotion;
- browser rendering.

The durable authority grant applies only to the read-only publication planner.

## Collector replacement and recovery

Implemented and tested as repository design:

- immutable image-drift guard;
- replacement planning;
- evidence and recovery schemas;
- snapshot-based rollback strategy;
- isolated restore rehearsal requirements;
- deterministic phase ordering;
- cleanup and cost ceilings.

Not implemented or proven as active execution:

- mutation-capable replacement workflow;
- fresh recovery point;
- evidence-disk recovery test;
- isolated boot rehearsal;
- canonical-name rollback execution;
- identity and RBAC restoration;
- operational disaster recovery.

## Security and identity

Declared controls include:

- private collector NIC;
- system-assigned managed identity;
- Trusted Launch, Secure Boot, and vTPM;
- SSH-key-only administration;
- detached evidence-disk boundary;
- loopback-only demo API;
- Nginx TLS termination;
- exact-origin CORS;
- request-size and rate limits;
- no caller-controlled backend target;
- exact-commit workflow checkout;
- protected GitHub environment and OIDC.

Declared controls are not proof of effective secure configuration. Current Azure Policy, deny assignments, effective permissions, guest configuration, certificate issuance, NSG effectiveness, and endpoint abuse resistance require runtime verification.

## Cost and quota

Promoted evidence supports:

- Public IP usage 1 of limit 3 at `2026-07-23T20:06:49Z`;
- two remaining Public IP units at that timestamp;
- a historical retail estimate of approximately CAD 19.42 for 730 hours of the two selected backend VMs.

Not observed:

- current invoice-level spend;
- remaining Azure for Students credit;
- taxes or discounts;
- complete resource-level allocation;
- current meter prices for every existing and proposed resource;
- actual cost of partial resources.

Historical retail estimates are planning evidence, not actual cost.

## Operational verification still required

- current collector guest health and evidence readability;
- backend listener and transaction behavior;
- post-failure Azure target-resource reconciliation;
- fresh isolated collector API What-If against the PR #59 repair;
- collector API deployment retry under separate authority;
- public DNS and TLS;
- API health;
- 20 correlated transactions observing both backends;
- bounded failure concentration;
- exact CORS behavior;
- live GitHub Pages rendering;
- report publication;
- recovery and rollback;
- partial-resource cleanup;
- current costs and credit.

## Safe next bounded increment

After the full reality-sync pull request is reviewed and merged:

1. re-resolve live GitHub and local working-tree state;
2. obtain explicit authority for one read-only collector API `what-if`;
3. use the exact reviewed commit containing PR #59 and the isolated Bicep root;
4. capture fresh Azure inventory, quota, locks, validation, and full What-If;
5. reject any protected-resource modification or unexpected resource;
6. stop for a separate human deployment decision.

No deployment, cleanup, report publication, collector replacement, or rollback is authorized by this status reconciliation.
