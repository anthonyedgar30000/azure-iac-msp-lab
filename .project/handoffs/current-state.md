# Current project handoff

## Interpretation boundary

This handoff reflects GitHub state observed after PR #137, the verified provenance preflight artifact from run `30206242759`, and the latest durable Azure observation generated on `2026-07-26`. It is not a continuously refreshed Azure or GitHub Actions dashboard.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
workflow_failed != deployment_failed
PR_merged != exact_head_CI_passed
repository_implemented != deployed_to_collector_VM
API_health_verified != Azure_host_identity_verified
frontend_bound != browser_verified
monitoring_enabled != alerts_verified
estimated_cost != actual_cost
authorization_expired != authorization_consumed
consumption_not_observed != unconsumed
CI_clean != Azure_runtime_updated
not_observed != false
```

## Canonical state selection

```text
state index: .project/state-index.json
current reality: .project/current-reality-v2.json
current completion gate: .project/lab-v1-completion-gate-v2.json
latest verified preflight: .project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json
latest authorization resolution: .project/reconciliations/post-pr137-provenance-authority-expiry-20260727.json
legacy reality snapshot: .project/current-reality.json
legacy completion gate: .project/lab-v1-completion-gate.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: f6e79818150d72b75d1e4f25be172e6dc577114d
latest merge: PR #137
PR #137 merge commit: f6e79818150d72b75d1e4f25be172e6dc577114d
PR #137 exact source: f6e79818150d72b75d1e4f25be172e6dc577114d
PR #137 exact-current-head CI: 30224641320 / success
open pull requests observed before this reconciliation: none
local working tree: not observed
```

The current `main` commit is also the PR #137 resulting commit. Exact-current-head CI passed workflow-observability validation, unit tests, evidence checks, infrastructure and workload contracts, and Bicep lint/build.

## Verified provenance preflight

```text
workflow run: 30206242759
job: 89804704663
artifact: 8633143093
artifact digest: sha256:2f8a63d18d6c2e07e86cc607c49d111e6b788d40637b2adcd30b1d5ce05de902
manifest verification: 26 / 26 payloads
reviewed source: 1677606ded960c951fa37f0fdbfae50ba4b3cc34
ARM validation: Succeeded
What-If: 24 Ignore / 3 Modify / 3 NoChange / 0 Create / 0 Delete / 0 Replace
Azure mutation performed: false
```

The reviewed source and current `main` differ only through preflight, evidence, authorization, documentation, and testing changes. No deployment-payload difference was observed.

## Latest durable Azure observation

```text
subscription: Azure for Students
resource group: rg-servicetracer-dev-westus2
region: westus2
collector VM: vm-stcollector-mst-dev / Standard_B2ats_v2 / VM running
collector private IP: 10.20.40.10
load balancer: lb-st-demo-api-mst-dev / Succeeded
backend pool: be-st-demo-api / collector address present
VM extension: servicetracer-demo-api / Succeeded
currently deployed source: 98b092201053fd3592be157a24de6e623e6b74a6
resource locks: none
readiness blockers: none
```

```text
month-to-date PreTaxCost: CAD 4.03203831168191
remaining Azure for Students credit: not observed
public IP addresses: 2 / 3
network interfaces: 3 / 65536
load balancers: 2 / 1000
additional public IP required: 0
quota sufficient for reviewed plan: true
```

The observation is point-in-time evidence from the verified preflight, not continuous Azure truth.

## Collector golden path — preserved deployed reality

Historical collector deployment run `30196388398` remains the latest deployment whose artifact has been promoted into repository evidence.

```text
deployed source: 98b092201053fd3592be157a24de6e623e6b74a6
collector API: https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run
health: healthy
CORS: GitHub Pages origin allowed / POST allowed
transaction request: HTTP 200 / 20 attempts
downstream results: 0 successful / 20 failed
stable backend localization: false
exact root cause claimed: false
```

```text
API_health_verified != downstream_transaction_success_verified
workflow_failed != deployment_failed
```

## Provenance deployment authorization resolution

PR #137 recorded one finite grant:

```text
grant: collector-provenance-deploy-1677606-20260726
reviewed source: 1677606ded960c951fa37f0fdbfae50ba4b3cc34
issued: 2026-07-26T19:02:36-04:00
valid until: 2026-07-26T21:02:36-04:00
attempt limit: 1
original recorded status: pending_consumption
current temporal status: expired
```

The available GitHub connector exposes PR-head and commit-associated checks but not the required manual `workflow_dispatch` history. No deployment artifact or repository reconciliation of an attempt was observed.

Canonical resolution:

```text
deployment dispatch observed: false
deployment artifact observed: false
consumption status: not_observed
expired unused claimed: false
consumed claimed: false
deployment succeeded claimed: false
deployment failed claimed: false
retry authorized: false
rollback authorized: false
```

The expired grant is not active authority. Whether it was consumed before expiry remains unresolved; either outcome requires new explicit authority for another attempt.

## Lab v1 gate

```text
exact-source preflight and What-If: complete
exact deployment source selected: complete
month-to-date actual-cost evidence in CAD: complete
historical collector deployment: complete
provenance source deployment: not observed
live Azure host identity and source-ref verification: not performed
browser live-path verification: not performed
stable ServiceTracer localization: not established
monitoring and alert delivery: not verified
full evidence lock: incomplete
```

## Historical compatibility anchors

Historical evidence remains bounded to its original context:

```text
PR #84 merge: c96d9cbb765a023921fa819cf7d99c957e8ad608
PR #84 source: 5c938a7e07da3a22b27bb5ac5aa52b7ccf22ba37
merged_into_main != deployed_to_VM
legacy canonical main: 665e051375594d11e58e434231bd06775dbdc560
PR #92 source: 5b5af74d57fb5fd87ece2a34239cc6f29d04b12b
PR #93 source: eecb5c872f76cb5e51df6f5451d5a61b79d87bba
PR #93 merge: 99dc79c7093fa4cd5655c2d5a65095dd796f9f75
independent demo deployed source: 8b3d55c616d8820edd523f77021a35fe24167bd0
checks_green != protected_Azure_artifact_inspected
human_operator_merge != prior_agent_merge_authority
deployment grant status: consumed_blocked
missing action: Microsoft.Compute/virtualMachines/extensions/write
effective extension write: unverified
authorization reconciliation merge: 92b0c3b1064158684a4b280348c77eeedba6dfc3
independent planner run: 30064289707
independent planner artifact: 8585693830
independent planner digest: 7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22
independent SKU restriction: NotAvailableForSubscription
independent VM family: standardBasv2Family
typed readiness control: PR #73
GitHub Pages publication authorized: false
```

## Current authority

```text
repository reconciliation authorized: true
draft pull request creation authorized: true
ordinary pull request CI authorized: true
pull request merge authorized: false
workflow dispatch authorized: false
Azure authentication authorized: false
Azure query authorized: false
Azure mutation authorized: false
deployment authorized: false
browser verification authorized: false
transaction replay authorized: false
rollback authorized: false
RBAC mutation authorized: false
cleanup authorized: false
```

## Next gate

1. Review this repository-only reconciliation and its exact-head CI.
2. Preserve the expired grant and unresolved consumption status.
3. Do not dispatch, retry, or verify under the expired grant.
4. If deployment remains desired, issue one new exact, non-renewing authority record from freshly reviewed evidence.
5. After a separately authorized deployment, verify Azure host identity, deployed source ref, CORS, GitHub Pages rendering, and one request-ID-correlated 20-attempt transaction with no automatic retry.
