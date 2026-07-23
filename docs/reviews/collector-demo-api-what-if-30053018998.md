# Collector demo API What-If run 30053018998

## Evidence identity

- Workflow: `Collector-hosted demo API`
- Operation: `what-if`
- Run: `30053018998`, attempt `1`
- Reviewed commit: `46821092a6d196cc08279d3d79b09ae613a09b2a`
- Resource group: `rg-servicetracer-dev-westus2`
- Region: `westus2`
- Artifact: `collector-demo-api-30053018998-1`
- Artifact ID: `8581736555`
- Artifact digest: `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`
- Evidence manifest generated: `2026-07-23T23:24:05Z`

The artifact hash manifest covers the exact request, Azure context, resource-group state, collector dependencies, partial ingress inventory, quota, locks, readiness, ARM validation, and ARM What-If result.

## Proven sequence

```text
exact reviewed commit checked out
→ bounded request and authority validated
→ repository tests passed
→ Azure OIDC login passed
→ collector and dependency inventory captured
→ readiness passed
→ ARM validation passed
→ What-If completed
→ classifier failed closed on one unapproved Modify
→ no Azure mutation occurred
→ evidence artifact uploaded
```

## Synchronized Azure findings

The read-only observation established:

- Azure for Students subscription context authenticated through the expected service principal;
- resource group `rg-servicetracer-dev-westus2` exists in `westus2` with the expected workload tag;
- collector `vm-stcollector-mst-dev` remains at private IP `10.20.40.10`;
- no resource-group locks are present;
- Public IP Addresses usage is `2/3`;
- Load Balancers usage is `1/1000`;
- the failed deployment left the dedicated public IP and both HTTP/HTTPS NSG rules;
- the dedicated load balancer and VM extension are not present;
- no legacy demo frontend, backend pool, probe, or rules exist under `lb-remote-access-mst-dev`.

```text
failed_deploy != zero_partial_mutation
partial_resource_exists != unsafe_to_reconcile
readiness_passed != WhatIf_accepted
WhatIf_failed_closed != architecture_failed
```

## Exact rejected plan

The What-If proposed:

- `Create`: `lb-st-demo-api-mst-dev`;
- `Create`: collector VM extension `servicetracer-demo-api`;
- `NoChange`: the two existing demo API NSG rules;
- `Modify`: existing public IP `pip-st-demo-api-mst-dev`.

The public-IP `Modify` contained exactly three deltas:

1. delete implicit `sku.tier = Regional`;
2. delete implicit `ddosSettings.protectionMode = VirtualNetworkInherited`;
3. change `tags.exposure` from `load-balanced-public-https` to `dedicated-load-balanced-public-https`.

The classifier correctly rejected the plan because every `Modify` was forbidden at the time.

## Bounded reconciliation

The repository repair must:

- explicitly preserve `sku.tier = Regional` on the Standard public IP;
- explicitly preserve `ddosSettings.protectionMode = VirtualNetworkInherited`;
- permit only the exact exposure-tag transition on the exact dedicated public IP;
- continue rejecting every other public-IP delta and every unrelated `Modify`, `Delete`, or `Replace`;
- continue requiring the dedicated load balancer, both NSG rules, and VM extension as exact target resources;
- keep `deployment_authorized = false` in What-If output.

The expected post-repair plan is therefore:

```text
Create   dedicated Standard Load Balancer
Create   collector VM extension
NoChange existing HTTP NSG rule
NoChange existing HTTPS NSG rule
Modify   exact public-IP exposure tag only
```

## Cost, rollback, and authority

The partial public IP already exists, so this reconciliation requires no additional public-IP quota. The dedicated Standard Load Balancer still adds recurring load-balancer and data-processing cost; actual CAD cost, remaining student credit, and current billing meters remain deployment-gate evidence.

Repository rollback is a revert of the bounded repair. The What-If operation performed no Azure mutation, so no Azure rollback or cleanup is required for run `30053018998`.

This review authorizes no deployment, cleanup, endpoint promotion, guest command, or automatic retry. After the repair is merged, the next operation is one fresh exact-commit read-only What-If followed by a separate deployment decision.
