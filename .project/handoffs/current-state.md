# Current project handoff

## Interpretation boundary

This handoff reflects GitHub state observed after PR #132 and durable Azure evidence from collector deployment run `30196388398`. It is not a continuously refreshed Azure dashboard.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
workflow_failed != deployment_failed
PR_merged != exact_head_CI_passed
repository_implemented != deployed_to_collector_VM
API_health_verified != Azure_host_identity_verified
frontend_bound != browser_verified
human_or_external_merge_observed != assistant_merge_action
monitoring_enabled != alerts_verified
estimated_cost != actual_cost
not_observed != false
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
observed main: 2f5b60c1d8328d13823e2cc1def09e6be384ecb5
latest merge: PR #132
PR #132 merge commit: 2f5b60c1d8328d13823e2cc1def09e6be384ecb5
PR #132 exact source: 6b7bd5362b17c9edfc0b41da65d5b798e5d00b45
PR #132 exact-head CI: 30204497860 / success
PR #132 merge-commit CI: not observed
open pull requests observed before this truth lock: none
local working tree: not observed
```

The PR #132 merge was observed externally. This assistant did not invoke the merge action; merge actor and prior merge authority were not resolved from the observed evidence.

## Collector golden path — deployed reality

```text
subscription: Azure for Students
resource group: rg-servicetracer-dev-westus2
region: westus2
deployed source: 98b092201053fd3592be157a24de6e623e6b74a6
deployment workflow run: 30196388398 / run 18
artifact: 8630260279 / 48 of 48 manifest payloads verified
collector VM: vm-stcollector-mst-dev / running
collector private IP: 10.20.40.10
load balancer backend: collector / 10.20.40.10
VM extension: servicetracer-demo-api / Succeeded
collector API: https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run
health: healthy
CORS: GitHub Pages origin allowed / POST allowed
transaction request: HTTP 200 / 20 attempts
downstream results: 0 successful / 20 failed
stable backend localization: false
exact root cause claimed: false
```

## Provenance-monitor repository increment

PR #130 merged the frontend/API provenance monitor and expected Azure host contract. Its exact-head CI run `30204308669` failed on a deterministic proof-wording contract. PR #131 attempted the wording repair but exact-head CI `30204440155` still failed. PR #132 restored the exact canonical proof phrase and exact-head CI `30204497860` passed.

```text
PR #130 merge: ede8b7b32fe4dfe0e817d224a3cf9a9c1c6b9489
PR #130 source / CI: 07e7056b3d66e88055f93d7f3c27d31f8281c316 / failure
PR #131 merge: 1accc46f2c4b585510f3b0919a15467a4e5d5769
PR #131 source / CI: bec88217096dce5ac205b93bb5f019f0f801fe62 / failure
PR #132 merge: 2f5b60c1d8328d13823e2cc1def09e6be384ecb5
PR #132 source / CI: 6b7bd5362b17c9edfc0b41da65d5b798e5d00b45 / success
```

The repository now requires the exact collector resource group, VM name, region, hosting model, deployed source ref, and request-ID correlation. **Those new fields are not deployed to the collector VM.** The VM still runs run-18 source `98b092201053fd3592be157a24de6e623e6b74a6`.

```text
repository_provenance_contract != deployed_provenance_contract
expected_azure_host != observed_azure_host
monitor_rendered != browser_path_verified
```

## Lab v1 gate

```text
collector deployment: complete
collector endpoint binding: merged
base API health and CORS: observed
provenance monitor repository implementation: merged
provenance monitor exact-head CI after repair: success
provenance runtime deployment: not performed
live Azure host identity and source ref verification: not performed
browser live-path verification: not performed
monitoring and alert delivery: not verified
actual cost in CAD and remaining student credit: not observed
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

1. Select one exact source containing the provenance monitor and repaired proof contract.
2. Capture fresh Azure collector state, dependencies, locks, quota, and current cost or student credit.
3. Capture a fresh FullResourcePayloads What-If for the existing collector API update.
4. Obtain one-shot non-renewing deployment, rollback, and post-deployment verification authority.
5. Verify live Azure host identity, deployed source ref, CORS, GitHub Pages rendering, and one request-ID-correlated 20-attempt transaction with no automatic retry.
