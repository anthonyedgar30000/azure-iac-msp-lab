# Current project handoff

## Interpretation boundary

This handoff reflects GitHub state observed at **2026-07-27T09:22:25-04:00**, the PR #138 merge, and the independently verified artifact from collector provenance deployment run `30224770178`. It is not a continuously refreshed Azure dashboard.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
files_replaced != running_process_restarted
network_reconciliation_succeeded != deployment_succeeded
failed_attempt != authorization_to_retry
PR_head_CI != merge_commit_CI
not_observed != false
```

## Canonical state selection

```text
state index: .project/state-index.json
current reality: .project/current-reality-v2.json
completion gate: .project/lab-v1-completion-gate-v2.json
latest verified preflight: .project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json
latest deployment reconciliation: .project/reconciliations/collector-provenance-deployment-run19-20260726.json
consumed grant: .project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json
prior expiry resolution: .project/reconciliations/post-pr137-provenance-authority-expiry-20260727.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: bd1ef50451c85d9f0e9e77c9ac54882d44940933
latest completed merge: PR #138
PR #138 exact source: db2c95d279f06f379c13b4cd8664518eda417843
PR #138 exact-head CI: 30267618707 / success
PR #138 merge-commit CI: not observed
open pull request: PR #139 / restart repair and run-19 reconciliation
local working tree: not observed
```

PR #138 merged the repository-only record that the earlier grant was temporally expired while its consumption was not observable through the available connector. The subsequently inspected run-19 artifact supplies stronger evidence: the grant was consumed by an actual deployment attempt. The earlier record remains historical evidence of the observation boundary at that time; it does not override the later artifact.

```text
earlier_not_observed != later_false
later_evidence_may_resolve_prior_uncertainty
```

## Run 19 deployment reality

```text
dispatcher: 30224765833 / failure
deployment: 30224770178 / run 19 / attempt 1 / failure
job: 89853061733
exact source: 1677606ded960c951fa37f0fdbfae50ba4b3cc34
artifact: 8638260753
artifact digest: sha256:3cd4993461de1545bc52885bbf8118d74f861d651f5aac692e4e06e4b3f16fab
manifest: 44 of 44 payloads verified
grant: consumed / non-renewing / non-transferable
retry: unauthorized
rollback: unauthorized
```

Azure login, readiness, ARM validation and the accepted `24 Ignore / 3 Modify / 3 NoChange / 0 Create/Delete/Replace` What-If passed. The dedicated load balancer and `collector / 10.20.40.10` backend pool reconciled successfully. The commit-bound VM extension reached terminal `Failed`, so public runtime verification and browser execution were skipped.

## Deterministic failure classification

The installer copied source `1677606ded960c951fa37f0fdbfae50ba4b3cc34`, rewrote the environment file and systemd unit, then called `systemctl enable --now`. On an already-running unit that enables the service but does not restart the existing Python process. The subsequent health request therefore reached the older process, which did not return the new `azure_host` object:

```text
Azure host identity was not verified: {}
```

PR #139 carries the repository repair:

```bash
systemctl daemon-reload
systemctl enable servicetracer-demo-api.service
systemctl restart servicetracer-demo-api.service
systemctl is-active --quiet servicetracer-demo-api.service
```

The repair is repository-only until separately merged, reviewed through a fresh preflight and deployed under new authority.

## Current Lab v1 gate

```text
fresh provenance preflight: complete
current cost observation: CAD 4.03203831168191 month-to-date
remaining Azure for Students credit: not observed
run 19 deployment attempt: failed closed
run 19 evidence lock: complete
systemd restart repair: under PR #139 review
provenance runtime verified: false
browser correlated transaction: false
monitoring and alert delivery: unverified
```

## Historical compatibility anchors

These markers remain durable for bounded historical validators. They do not supersede the current canonical v2 records.

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

## Current authority

```text
repository restart repair: authorized
repository truth reconciliation: authorized
ordinary PR CI: authorized
PR #139 merge: unauthorized
Azure query or mutation: unauthorized
workflow retry or dispatch: unauthorized
rollback: unauthorized
browser transaction: unauthorized
RBAC or cleanup: unauthorized
```

## Next gate

Review exact-head CI for the rebased PR #139 and make a separate merge decision. After a merge, capture fresh Azure state and a fresh `FullResourcePayloads` What-If for the repaired exact source. A new explicit, non-renewing deployment and rollback decision is required before another Azure attempt.
