# Current project handoff

## Interpretation boundary

This handoff reflects GitHub state observed after PR #132 and durable Azure evidence from collector deployment run `30196388398`. It is not a continuously refreshed Azure dashboard. No fresh Azure authentication, query, or mutation was performed during this reconciliation.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
workflow_failed != deployment_failed
PR_merged != exact_head_CI_passed
API_health_verified != downstream_transaction_success_verified
independent_API_ready != collector_golden_path_verified
frontend_bound != browser_verified
repository_implemented != deployed_to_collector_VM
monitor_rendered != provenance_contract_deployed
expected_resource_group != observed_resource_group
request_sent != response_correlation_verified
human_or_external_merge_observed != assistant_merge_action
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
latest reconciliation: .project/reconciliations/provenance-monitor-post-merge-pr132-20260726.json
legacy reality snapshot: .project/current-reality.json
legacy completion gate: .project/lab-v1-completion-gate.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 2f5b60c1d8328d13823e2cc1def09e6be384ecb5
latest merge: PR #132
PR #132 merge commit: 2f5b60c1d8328d13823e2cc1def09e6be384ecb5
PR #132 exact source: 6b7bd5362b17c9edfc0b41da65d5b798e5d00b45
PR #132 exact-head CI: 30204497860 / success
PR #132 source-vs-merge file-content difference observed: false
PR #132 merge-commit CI: not observed
open pull requests observed: none
local working tree: not observed
```

Recent merge chain:

```text
PR #129 merge: 50195397944909918d2b2adcdd58019a425686e8
PR #130 merge: ede8b7b32fe4dfe0e817d224a3cf9a9c1c6b9489
PR #130 exact source: 07e7056b3d66e88055f93d7f3c27d31f8281c316
PR #130 exact-head CI: 30204308669 / failure
PR #131 merge: 1accc46f2c4b585510f3b0919a15467a4e5d5769
PR #131 exact source: bec88217096dce5ac205b93bb5f019f0f801fe62
PR #131 exact-head CI: 30204440155 / failure
PR #132 merge: 2f5b60c1d8328d13823e2cc1def09e6be384ecb5
PR #132 exact source: 6b7bd5362b17c9edfc0b41da65d5b798e5d00b45
PR #132 exact-head CI: 30204497860 / success
```

PR #130 and PR #131 were merged despite failing exact-head CI. Their failures were bounded to the deterministic frontend proof wording contract. PR #132 supplied the exact required phrase, passed both CI jobs, and merged with no file-content difference from its validated source head.

The merges were observed as performed by `anthonyedgar30000`. This assistant did not invoke those merge actions, and prior merge authority was not independently established from the observed evidence.

## Collector golden path — durable deployed reality

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

The deployment workflow concluded red because its shell verifier mishandled normal CRLF headers after deployment and runtime requests succeeded. The finite grant was consumed; no deployment retry is authorized.

## Provenance monitor repository state

PR #130 added repository support for a frontend provenance panel, Azure Instance Metadata Service host identity, exact deployed-source binding, and a UUID request-correlation contract. PR #132 repaired the deterministic proof wording and is the latest green source lineage.

```text
repository implementation merged: true
expected collector endpoint committed: true
expected resource group: rg-servicetracer-dev-westus2
expected collector VM: vm-stcollector-mst-dev
expected region: westus2
expected hosting model: collector_vm_systemd
identity source: Azure Instance Metadata Service
request correlation: UUID echoed in header and payload
provenance runtime contract deployed: false
GitHub Pages publication of PR #132 content verified: false
browser Azure host identity verified: false
browser request correlation verified: false
downstream service success verified: false
```

Repository binding and a rendered monitor do not by themselves prove GitHub Pages publication, exact-source runtime deployment, browser-path completion, or downstream service success.

## Lab v1 gate

```text
exact What-If evidence: complete
collector deployment: complete
run-18 deployed source decision: complete
provenance monitor repository implementation: complete
provenance proof wording contract: complete / PR #132 green
exact source selected for provenance deployment: false
fresh Azure preflight and What-If for provenance source: not performed
provenance runtime contract deployed: false
API health, HTTPS request, CORS and one 20-attempt API request: observed for run 18
downstream successful transaction evidence: not established
supported stable localization: not established
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

No fresh subscription, tenant, resource-group, region, quota, or cost query was performed during this repository-only reconciliation.

## Historical compatibility anchors

Historical evidence remains bounded to its original context and must not overwrite collector run-18 reality:

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

These historical strings do not supersede the versioned canonical v2 state selected by `.project/state-index.json`.

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

1. Select one exact reviewed source for deploying the provenance runtime contract.
2. Capture fresh subscription, tenant, resource-group, region, quota, and actual cost or remaining Azure for Students credit evidence in CAD.
3. Capture a fresh FullResourcePayloads What-If against the existing collector deployment.
4. Obtain one-shot, non-renewing deployment and rollback authority.
5. After deployment, verify health identity, CORS, GitHub Pages rendering, and one request-ID correlation path with no automatic retry.
6. Preserve downstream failure as inconclusive unless stable supported localization is independently established.
