# Stategraph Adoption Strategy

## Decision

Stategraph is accepted as an optional future working capability for the Azure IaC MSP Lab.

The governing question is:

> Does Stategraph help push the MSP demo lab forward faster and with more confidence?

The machine-readable decision is [`.project/stategraph-capability.json`](../../.project/stategraph-capability.json). The bounded pre-adoption reconciliation is [`.project/reconciliations/pre-stategraph-adoption-20260725.json`](../../.project/reconciliations/pre-stategraph-adoption-20260725.json).

## Current classification

```text
architecture decision = accepted
current priority = Design For
Build Now = false
Stategraph runtime available = false
Terraform root present = false
Azure change performed = false
```

The Lab v1 completion gate remains controlling. Stategraph may move into Build Now only when it directly closes a Lab v1 completion criterion, removes a material security or operational credibility defect, produces evidence required by the final demonstration, or a later explicit human priority decision changes the ordering.

This record does not bypass the current requirement to complete and evidence-lock the production-shaped ServiceTracer vertical slice.

## Existing infrastructure boundary

The existing ServiceTracer infrastructure path is Bicep-led.

```text
existing ServiceTracer IaC owner = Bicep
existing Bicep resources = not Terraform-owned
existing Bicep resources = not Stategraph-managed
```

Stategraph is not inserted beneath `infra/main.bicep`, and this adoption decision does not convert or import existing Azure resources into Terraform state.

## Future pilot architecture

The first eligible Stategraph working pilot must use a separate, isolated Terraform root with no ownership overlap with existing Bicep resources.

```text
standard Terraform
→ canonical pilot declaration and initial execution path

Stategraph
→ optional advisory shadow
→ diagnostics, inventory, dependency queries, and change analysis

Azure
→ independently observed operational reality
```

The initial pilot must preserve these boundaries:

- standard Terraform works without Stategraph;
- the standard Terraform backend remains the initial canonical pilot state;
- Stategraph failure is visible but nonblocking;
- Stategraph apply is disabled initially;
- no existing Bicep-managed resource is imported;
- no secret, raw state, token, or protected evidence is committed;
- destructive changes remain on the standard Terraform path until fallback and compatibility are explicitly tested.

## Planned phases

### Phase 0 — Adoption and reconciliation

This repository-only increment:

- records the accepted strategy;
- resolves the current repository and CI baseline needed for the decision;
- preserves the Lab v1 priority gate;
- adds deterministic validation;
- performs no workflow dispatch and no Azure or Stategraph operation.

### Phase 1 — Isolated standard Terraform foundation

This phase is not currently admitted as Build Now.

Before implementation it must define:

- intended architecture and isolated resource scope;
- subscription, tenant, region, resource group, cost, quota, and policy evidence;
- Azure identity and least-privilege permissions;
- network paths and security controls;
- standard backend and locking;
- validation, plan, apply, rollback, cleanup, and evidence procedures;
- zero dependence on Stategraph for normal Terraform operation.

### Phase 2 — Advisory Stategraph shadow

After the standard Terraform boundary is proven:

- run Stategraph diagnostics against the exact Terraform root;
- use read-only or plan-only Stategraph access;
- create a shadow representation without changing canonical state ownership;
- capture sanitized inventory, dependency, and blast-radius evidence;
- keep the Stategraph job nonblocking.

### Phase 3 — Real-work evaluation

Use Stategraph during ordinary Terraform changes. Do not create a separate artificial benchmarking project.

Record whether it:

- exposes dependencies that would otherwise be missed;
- reduces change-analysis time;
- makes plan review clearer;
- increases deployment confidence;
- reduces repeated investigation;
- introduces acceptable or unacceptable tooling overhead.

### Phase 4 — Optional execution pilot

Stategraph execution remains separately gated and is not authorized by this decision.

It requires:

- demonstrated value in advisory use;
- explained plan equivalence;
- tested state export and standard Terraform fallback;
- exact source and target scope;
- separate human authorization;
- a non-destructive first operation.

## Fallback rule

```text
Stategraph unavailable
→ standard Terraform continues

Stategraph unclear or divergent
→ stop Stategraph path
→ preserve evidence
→ use standard Terraform
```

Stategraph must earn deeper integration through usefulness. It must never become an accidental prerequisite for the lab.

## Evaluation outcome

Continue or expand Stategraph when real work shows faster impact analysis, clearer dependency understanding, fewer missed relationships, and increased confidence without obscuring state ownership.

Keep it advisory when graph and query value is useful but execution compatibility remains uncertain.

Remove it when its operational and reconciliation overhead exceeds its practical value, when plan differences cannot be explained, when state ownership becomes ambiguous, or when the fallback path cannot be trusted.

## Authority boundary

Authorized by the instruction to execute this first repository increment:

- bounded repository reconciliation;
- Stategraph adoption record;
- architecture documentation;
- deterministic tests;
- branch creation;
- draft pull request creation.

Not authorized:

- pull-request merge;
- workflow dispatch or rerun;
- Azure authentication, query, mutation, deployment, RBAC, policy, identity, network, cost, or quota operation;
- Terraform backend creation, initialization against Azure, plan, or apply;
- Stategraph account, tenant, state, token, import, plan, or apply operation.

```text
repository_adoption != working_capability
working_capability != deployment_authorized
plan_created != apply_authorized
```

## Next gate

Review and merge this repository-only adoption record.

After merge, continue the existing Lab v1 completion program. Re-evaluate Stategraph implementation only when the Lab v1 admission rule permits it or an explicit human priority decision changes that ordering.
