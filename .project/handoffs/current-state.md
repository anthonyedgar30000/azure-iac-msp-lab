# Current project handoff

## Interpretation boundary

This handoff reflects GitHub state observed after PR #125 and durable Azure evidence from collector deployment run `30196388398`. It is not a continuously refreshed Azure dashboard.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
workflow_failed != deployment_failed
API_health_verified != downstream_transaction_success_verified
independent_API_ready != collector_golden_path_verified
frontend_bound != browser_verified
RBAC_assignment != effective_least_privilege
monitoring_enabled != alerts_verified
estimated_cost != actual_cost
not_observed != false
source_silence != contradiction
verification_status != truth_value
```

## Canonical state selection

```text
state index: .project/state-index.json
current reality: .project/current-reality-v2.json
current completion gate: .project/lab-v1-completion-gate-v2.json
legacy reality snapshot: .project/current-reality.json
legacy completion gate: .project/lab-v1-completion-gate.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 855ef85f898cbf34db2931abc8344d05cb05c6f7
latest merge: PR #125
PR #125 exact source: 315a310ae4ff3db7d5d100ea0320911043b77564
PR #125 exact-head CI: 30203314001 / success
PR #123: closed without merge after consumed failed one-shot verification
open pull requests observed before this remediation PR: none
local working tree: not observed
merge-commit CI: not observed
```

## Collector golden path — deployed reality

```text
subscription: Azure for Students
resource group: rg-servicetracer-dev-westus2
region: westus2
deployed source: 98b092201053fd3592be157a24de6e623e6b74a6
deployment workflow run: 30196388398 / run 18
workflow job: 89778570106
artifact: 8630260279
artifact digest: sha256:1f97be3c519d547871cc990e010013259dfd3c2e263f263653c2c4035340eb9e
manifest: 48 / 48 verified
collector VM: vm-stcollector-mst-dev / running
collector private IP: 10.20.40.10
load balancer: lb-st-demo-api-mst-dev / Succeeded
backend pool: be-st-demo-api / collector / 10.20.40.10
VM extension: servicetracer-demo-api / Succeeded
collector API: https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run
health: healthy
CORS preflight: 204 / GitHub Pages origin allowed / POST allowed
transaction request: HTTP 200 / 20 attempts
downstream results: 0 successful / 20 failed
stable backend localization: false
exact root cause claimed: false
```

The run concluded red because a shell verifier mishandled normal CRLF headers after deployment and runtime requests succeeded. The grant was consumed; no deployment retry is authorized.

## Frontend binding

The committed frontend is now bound to the collector-hosted endpoint above. The previous `st-demo-api-vm-aeg30000...` hostname belongs to the independent demo API lineage and is not the Lab v1 golden path.

PR #123 failed while waiting for its expected published configuration. Browser setup and the 20-attempt browser action never executed. The PR was closed without merge, and a future browser run requires new explicit one-shot authority.

## Lab v1 gate

```text
exact What-If evidence: complete
collector deployment: complete
deployed source decision: complete
API health, HTTPS request, CORS and one 20-attempt API request: observed
downstream successful transaction evidence: not established
supported stable localization: not established
GitHub Pages collector binding publication: pending
browser live-path verification: pending new authority
monitoring and alert delivery: not verified
actual cost in CAD and remaining student credit: not observed
full evidence lock: incomplete
```

## Quota and cost boundary

Last time-bounded quota evidence remains:

```text
Standard IPv4 public IPs: 2 / 3
load balancers: 2 / 1000
additional public IP required by run 18: 0
current billing cost: not observed
remaining Azure for Students credit: not observed
```

No fresh Azure authentication or query was performed during this repository reconciliation.

## Historical compatibility anchors

Historical evidence remains bounded to its original context and must not overwrite collector run-18 reality:

```text
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

These strings remain only because historical validators require their original evidence anchors. They do not supersede the versioned canonical v2 state selected by `.project/state-index.json`.

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

1. Merge and publish the corrected collector endpoint only after exact-head CI and human review.
2. Observe the exact GitHub Pages configuration.
3. Obtain a new finite browser-verification grant.
4. Perform one browser health/CORS/20-attempt verification with no automatic retry.
5. Capture actual Azure cost or remaining student credit in CAD.
