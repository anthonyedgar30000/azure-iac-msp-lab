# Collector provenance preflight run 1 — artifact promotion

Recorded: 2026-07-26 19:02:36 EDT

## Decision

The evidence artifact from workflow run `30206242759` is accepted as the durable, point-in-time predeployment record for exact source `1677606ded960c951fa37f0fdbfae50ba4b3cc34`.

This promotion does not claim that the source is deployed. It establishes that the bounded Azure state capture, ARM validation, `FullResourcePayloads` What-If, quota observation and month-to-date cost query completed successfully without Azure mutation.

## Artifact identity and integrity

- artifact ID: `8633143093`
- artifact name: `collector-provenance-preflight-30206242759`
- GitHub digest: `sha256:2f8a63d18d6c2e07e86cc607c49d111e6b788d40637b2adcd30b1d5ce05de902`
- independently calculated ZIP digest: exact match
- manifest schema: `servicetracer.provenance-preflight-evidence.v1`
- manifest payloads: 26 verified, 0 failed
- raw subscription and tenant identifiers: not promoted

## Exact source boundary

The preflight reviewed `1677606ded960c951fa37f0fdbfae50ba4b3cc34` while the repository later advanced to `main@16a589adfce0816c759f6ea0e8d3a2ed9a0781aa`.

The only file differences are the merged read-only preflight workflow, plan, operating document, cost normalizer and tests. No Bicep, installer, API, frontend or deployment payload difference was observed.

```text
current_main != deployment_source
repository_ahead != deployment_payload_changed
```

## Azure observation

The preflight observed:

- `rg-servicetracer-dev-westus2` in `westus2`, provisioning `Succeeded`;
- `vm-stcollector-mst-dev`, `Standard_B2ats_v2`, running at `10.20.40.10`;
- `lb-st-demo-api-mst-dev`, provisioning `Succeeded`;
- backend pool `be-st-demo-api` containing one `collector` address;
- VM extension `servicetracer-demo-api`, provisioning `Succeeded`;
- deployed runtime source still `98b092201053fd3592be157a24de6e623e6b74a6`;
- no resource locks or readiness blockers.

The observation is time-bounded. It is not a continuous health assertion.

## Cost and quota

Month-to-date `PreTaxCost` was observed as `4.03203831168191 CAD`. The remaining Azure for Students credit was not observed.

The accepted plan requires no additional public IP. Observed quota included public IP usage `2/3`, network interfaces `3/65536`, and load balancers `2/1000`.

```text
month_to_date_cost != remaining_credit
not_observed != zero
```

## ARM validation and What-If

ARM validation succeeded. The deterministic classifier accepted exactly:

```text
30 total entries
24 Ignore
 3 Modify
 3 NoChange
 0 Create
 0 Delete
 0 Replace
```

The only approved modifications are:

1. update the commit-bound CustomScript extension source to `1677606...`;
2. reconcile the existing Standard/Regional load-balancer parent payload;
3. reconcile the existing backend-pool address while preserving `collector / 10.20.40.10`.

No base infrastructure, collector VM, collector NIC, Microsoft.Web, RBAC, cleanup, create, delete or replace operation is allowed.

## Deployment authority

A separate finite grant is recorded in:

`.project/reconciliations/collector-provenance-deployment-authorization-1677606-20260726.json`

It allows one deployment attempt through `.github/workflows/collector-demo-api.yml`, exact operation `deploy`, exact source `1677606...`, exact resource group, region, DNS label and origin. The grant is consumed when the dispatch is accepted or execution begins. No retry or rollback authority carries forward.

## Known verifier limitation

The merged deployment workflow still uses a grep expression that can reject a correct CRLF CORS response header. A red workflow conclusion after successful deployment and runtime requests must therefore be reconciled against the uploaded deployment artifact.

```text
workflow_failed != deployment_failed
verifier_false_negative != service_failure
```

No automatic retry is permitted.
