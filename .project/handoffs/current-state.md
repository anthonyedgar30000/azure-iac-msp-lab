# Current project handoff

## Interpretation boundary

This handoff records the synchronized repository architecture and the newest promoted Azure evidence available on `2026-07-24`. It is not a live GitHub or Azure dashboard.

```text
durable_handoff != live_status
declared_in_code != deployed_in_Azure
not_observed != false
resource_exists != service_healthy
failed_deploy != proof_of_zero_partial_mutation
```

Resolve the live default-branch head, open pull requests, exact-head CI, Azure subscription context, quotas, costs, target resources, and local working tree whenever this document is used for a consequential decision.

## Repository synchronization watermark

The independent ServiceTracer demo API workload was merged through PR #65.

Repository evidence:

- source head `1be38682bf382bb70a585522d9e8c193beb89937`;
- exact-head CI run `30055579796`: success;
- merge commit `e3364b9cb918bf5aef23eab011d2a168183b3442`;
- no file-content differences between the tested source head and merge commit;
- no Azure mutation authorized by that merge.

A separate post-merge CI run was not observed. That is an observation limitation, not evidence of failure.

## Current declared architecture

The active repository strategy is now an independent workload inside the Azure IaC MSP Lab:

```text
GitHub Pages
→ dedicated Standard public IP and DNS
→ dedicated NSG allowing TCP 80/443 only
→ dedicated Linux VM in its own VNet and subnet
→ Nginx TLS and rate limiting
→ loopback-only Python API
→ read-only HTTPS dependency on existing ServiceTracer transaction endpoint
```

Default scope:

```text
rg-st-demo-api-dev-westus2
├── vnet-st-demo-api-mst-dev
├── nsg-st-demo-api-mst-dev
├── pip-st-demo-api-vm-mst-dev
├── nic-st-demo-api-mst-dev
└── vm-st-demo-api-mst-dev
```

The independent workload must not mutate:

- `vm-stcollector-mst-dev`;
- `nsg-operations-mst-dev`;
- `vnet-onprem-sim-mst-dev`;
- `lb-remote-access-mst-dev`;
- collector NIC, disks, extensions, identity, or guest configuration.

## Correct VM sizing contract

The independent API planning and IaC default is:

```text
Standard_B2ats_v2
```

The earlier `Standard_B1s` default came from the synthetic backend workload and was not the approved API-host default.

```text
observed_working_size != current_SKU_availability
configured_default != quota_reserved
```

A fresh planner run must still verify regional availability, compute quota, public-IP quota, cost, and remaining Azure for Students credit.

## Planner authority

The active workflow is:

```text
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

It:

- runs only from `refs/heads/main`;
- checks out immutable `github.sha`;
- accepts no manually entered commit SHA;
- authenticates to Azure for read-only inventory, validation, and What-If;
- captures provider registration, VM SKU availability, compute usage, network usage, dependency state, and target resource-group state;
- rejects any Modify, Delete, Replace, dependency mutation, scope escape, or unrelated resource type;
- always reports `deployment_authorized: false`.

No deployment workflow exists for the independent workload.

## New workload Azure reality

The independent target resource group, VM, VNet, NSG, NIC, public IP, DNS, TLS, API health, transaction behavior, CORS, and browser integration are currently:

```text
not_observed
```

This must not be restated as absent or failed until a fresh scoped Azure observation is performed.

## Newest authenticated Azure evidence

The newest authenticated Azure evidence inspected during this sync remains collector-hosted What-If run `30053018998`, generated on `2026-07-23`.

It established that Azure login, dependency inventory, readiness, ARM validation, evidence capture, and artifact upload succeeded. The What-If classifier failed closed, and deployment and service verification were skipped.

Observed at that time:

- Azure for Students subscription and expected tenant;
- `rg-servicetracer-dev-westus2` in `westus2`;
- collector VM running at private IP `10.20.40.10`;
- collector had no public IP;
- partial collector-hosted residue included `pip-st-demo-api-mst-dev` and HTTP/HTTPS operations-NSG rules;
- no resource-group read-only lock;
- Standard public-IP usage was 2 of 3, leaving one observed slot.

Those facts are time-bounded. The later stale-commit workflow failure did not reach Azure and added no newer Azure evidence.

## Quota and cost consequence

The independent workload requires one Standard public IP. If the 2-of-3 observation remains current, the workload would consume the last available slot.

```text
quota_observed != quota_reserved
estimated_cost != actual_cost
student_credit_present != zero_cost
```

Deployment authorization must explicitly evaluate zero remaining public-IP headroom, current VM-family quota, exact SKU availability, actual subscription cost context, and rollback implications.

## Historical collector-hosted path

The collector-hosted design is retained as history and evidence, not the active deployment strategy.

Required historical anchors:

- PR #56 isolated the collector API deployment root;
- PR #58 added the governed persistence controller;
- PR #59 repaired the parent/nested deployment-name collision;
- run `30044644501` accepted an isolated What-If and then failed deployment;
- post-failure mutation was not proven;
- a fresh Azure inventory and isolated What-If were required before any retry.

Later PRs #63 and #64 repaired the dedicated-load-balancer and public-IP reconciliation path, but that strategy was superseded by PR #65 before successful service deployment.

No legacy cleanup is authorized by this handoff.

## Other unresolved Azure reality

- Current collector guest health and ServiceTracer version remain unverified.
- Synthetic backend VM listeners and transaction behavior remain unverified.
- Legacy Application Insights and storage residue may still exist and may incur cost.
- Current Azure Policy, deny assignments, effective RBAC, actual cost, remaining student credit, and resource-level cost allocation remain unobserved.
- Backup configuration, recovery rehearsal, rollback execution, and disaster recovery remain unverified.

## Safe next bounded operation

After the VM-size correction is exact-head CI verified and merged:

1. resolve the new live `main` head and open PRs;
2. run the independent read-only planner from `main` with `Standard_B2ats_v2`;
3. capture exact Azure context, providers, target-resource-group state, SKU availability, compute quota, network quota, dependency public endpoint, validation, and full What-If;
4. reject any unexpected active change;
5. explicitly review the public-IP headroom and cost evidence;
6. stop for a separate deployment decision.

No Azure deployment, cleanup, collector mutation, report publication, replacement, rollback, or recovery is authorized by this synchronization.
