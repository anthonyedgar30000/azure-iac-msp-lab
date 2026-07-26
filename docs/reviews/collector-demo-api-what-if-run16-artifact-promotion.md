# Collector-hosted demo API What-If run 16 artifact promotion

## Evidence identity

- Workflow run ID: `30192970923`
- Run attempt: `1`
- Workflow run number: `16`
- Job ID: `89769401839`
- Operation: `what-if`
- Exact reviewed commit: `8de1f61f8a0ea06dcf94b94c798edde2aace357d`
- Resource group: `rg-servicetracer-dev-westus2`
- Region: `westus2`
- Artifact ID: `8629191915`
- Artifact name: `collector-demo-api-30192970923-1`
- Artifact digest: `sha256:57fe05c113d0fefc86437a4aa247b920dc6a02680a1c2bfe8e67873fe7612e6e`
- Manifest generated at: `2026-07-26T07:33:02Z`
- Artifact retention expiry: `2026-08-25T07:33:02Z`

This review supersedes the observation boundary in the earlier run-16 record. It does not rewrite that historical record.

## Integrity verification

The downloaded ZIP SHA-256 exactly matched GitHub's artifact digest.

```text
archive entries = 31
manifest-listed payloads = 29
verified payload hashes = 29
hash failures = 0
```

The artifact contains Azure resource and identity identifiers. It is evidence-controlled and must not be published publicly without redaction.

## Proven workflow sequence

All bounded pre-deployment steps completed successfully:

```text
exact reviewed checkout
→ authority validation
→ repository tests
→ Azure workload-identity login
→ live collector and dependency capture
→ readiness assessment
→ ARM validation
→ FullResourcePayloads What-If
→ deterministic classifier acceptance
→ manifest and artifact upload
```

The following steps were explicitly skipped:

```text
deployment
post-deployment capture
public runtime verification
transaction replay
```

Therefore:

```text
Azure mutation = false
service restoration = not verified
deployment authority = false
```

## Captured Azure state

At artifact generation:

- the resource group was `Succeeded`;
- `vm-stcollector-mst-dev` was running as `Standard_B2ats_v2`;
- the collector private IP was `10.20.40.10`;
- `lb-st-demo-api-mst-dev` existed and was `Succeeded`;
- `be-st-demo-api` existed with zero backend addresses;
- `servicetracer-demo-api` existed in `Failed`;
- no resource locks were observed;
- the readiness assessment reported no blockers;
- `deployment_decision_ready` was true;
- `deployment_authorized` was false.

The identity evidence is retained only as SHA-256 fingerprints in the promotion record.

## Exact accepted plan

The What-If contained 30 entries:

```text
24 Ignore
 3 Modify
 3 NoChange
 0 Create
 0 Delete
 0 Replace
```

The three approved modifications were:

1. `vm-stcollector-mst-dev/servicetracer-demo-api`
   - retain `Microsoft.Azure.Extensions / CustomScript / 2.1`;
   - add `forceUpdateTag` equal to exact commit `8de1f61f…`;
   - rerun the failed installer from immutable source.

2. `lb-st-demo-api-mst-dev`
   - retain Standard / Regional;
   - retain the exact public frontend, TCP/80 probe, and HTTP/HTTPS rules;
   - reconcile ARM-default fields omitted from the declaration;
   - do not broaden network architecture.

3. `lb-st-demo-api-mst-dev/be-st-demo-api`
   - add exactly one backend named `collector`;
   - bind private IP `10.20.40.10`;
   - bind VNet `vnet-onprem-sim-mst-dev`.

Explicit `NoChange` targets:

- `pip-st-demo-api-mst-dev`
- `Allow-Demo-API-HTTP-From-Internet`
- `Allow-Demo-API-HTTPS-From-Internet`

No collector VM, collector NIC, base infrastructure, or Microsoft.Web mutation was proposed. `appi-demo-api-mst-dev` remained an ignored managed leftover, not a silent deletion target.

## Quota and cost boundary

The artifact captured:

```text
Public IP addresses = 2 / 3
Standard IPv4 public IP addresses = 2 / 3
Load balancers = 2 / 1000
Additional public IP required = 0
```

No resource creation was proposed. However, no current Azure for Students credit balance or billing-cost snapshot was captured.

```text
no resource creation != zero cost
quota sufficient != budget verified
```

## Exact-source boundary

The accepted plan is bound to:

```text
8de1f61f8a0ea06dcf94b94c798edde2aace357d
```

Current `main` at promotion is:

```text
2251f9721d582e6f79f22cf8977e1dea55a5b786
```

The four intervening commits only add the earlier evidence record, review, test, and merge commit. Even so:

```text
deploying accepted source != deploying current main
```

A deployment grant must name one exact source and repeat live preflight and What-If for that source.

## Authority

This increment authorizes:

- artifact inspection;
- repository evidence promotion;
- a draft pull request;
- ordinary pull-request CI.

It authorizes no:

- pull-request merge;
- Azure query or workflow dispatch;
- deployment;
- runtime verification or transaction replay;
- rollback, cleanup, RBAC, or network mutation.

## Next gate

Before deployment:

1. Review and merge this evidence promotion under separate authority.
2. Refresh Azure for Students credit or billing evidence.
3. Select the exact deployment source.
4. Repeat live preflight and FullResourcePayloads What-If for that exact source.
5. Define one-shot deployment, rollback, and post-deployment verification authority.

```text
artifact_verified != deployment_authorized
deployment_decision_ready != deployment_authorized
WhatIf_accepted != service_restored
not_observed != false
```
