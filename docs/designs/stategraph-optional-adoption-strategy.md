# Stategraph Optional Adoption Strategy

## Decision

Stategraph is accepted as an **optional working capability** for future Terraform or OpenTofu increments in the Azure IaC MSP Lab.

It is not the authoritative infrastructure definition, not a replacement for evidence, and not a dependency of the current ServiceTracer Lab v1 golden path.

The governing evaluation question is:

> Does Stategraph help push the MSP demo lab forward faster and with more confidence?

No synthetic benchmark or separate research project is required. Stategraph earns deeper use only through useful participation in ordinary infrastructure work.

## Architecture Review Gate

| Question | Resolution |
|---|---|
| Does it belong in this lab? | Yes, as optional IaC developer and operational tooling. |
| Which bucket owns it? | Azure resource plan and IaC tooling, with evidence captured under `.project/`. |
| Is a new architecture bucket required? | No. |
| Build priority now? | **Design For**. Execution is deferred until a real Terraform/OpenTofu increment satisfies the Lab v1 scope-admission rule. |

## Current repository and runtime boundary

The inspected active ServiceTracer workload is declared through Bicep, including the isolated independent demo API root. No active Terraform/OpenTofu root or Terraform state is declared by the inspected repository authority.

Stategraph's documented adoption path operates on Terraform/OpenTofu HCL and state. Therefore this increment must not:

- translate the current Bicep workload into duplicate Terraform solely to exercise Stategraph;
- create an artificial benchmark lab;
- place Stategraph in the current deployment path;
- import, replace, or mutate any live state;
- authenticate to Azure or dispatch a workflow;
- delay the Lab v1 P0 through P2 completion program.

```text
Bicep_current_path != Terraform_state_available
interesting_capability != Build_Now
optional_tool != deployment_dependency
Stategraph_record != Azure_reality
```

## Admission rule

A working Stategraph increment may enter **Build Now** only when all of the following are true:

1. a genuine Terraform/OpenTofu root is being added or changed for real lab work;
2. the increment directly closes a Lab v1 criterion, removes a material credibility defect, produces required demonstration evidence, or Lab v1 P0 through P2 is complete;
3. standard Terraform/OpenTofu init, validate, plan, and state handling work independently first;
4. the exact Stategraph version and current compatibility documentation are reviewed at execution time;
5. state sensitivity, secret handling, deployment model, identity, cost, and data residency are explicitly assessed;
6. the Stategraph experiment is bounded, reversible, and separately authorized.

## Lean adoption sequence

### Phase 0 — Capability check

- Confirm a real Terraform/OpenTofu root exists.
- Record Terraform/OpenTofu, provider, and Stategraph versions.
- Run standard validation first.
- Run Stategraph diagnostics only against the exact candidate root.
- Preserve sanitized diagnostics and limitations.

No import, plan, apply, cloud authentication, or state mutation is authorized by this phase definition.

### Phase 1 — Reversible state round trip

- Back up the exact standard state using the existing approved backend process.
- Import a controlled copy into an isolated Stategraph environment.
- Export it immediately back to standard Terraform state.
- Compare resource addresses, serial/lineage semantics, sensitive-value handling, and dependency relationships.
- Prove that standard Terraform can resume without Stategraph.

Failure of the round trip terminates the experiment.

### Phase 2 — Shadow planning

For a real infrastructure change:

- produce the normal Terraform/OpenTofu plan;
- produce a Stategraph plan in non-authoritative shadow mode;
- compare proposed actions, dependency interpretation, blast radius, timing, and operator clarity;
- preserve disagreements instead of selecting the more convenient result.

```text
Stategraph_plan != accepted_plan
plan_agreement != deployment_authority
plan_disagreement != Terraform_failure
```

Standard Terraform/OpenTofu remains the fallback and decision baseline until explicit promotion.

### Phase 3 — Optional bounded execution

Stategraph execution is eligible only after successful diagnostics, round-trip export, repeated shadow-plan usefulness, exact-head review, and a separate identity-bound and scope-bound authorization.

The first execution must be low-risk, independently verifiable, reversible, and limited to one real increment. Normal What-If or plan review, Azure validation, runtime verification, evidence capture, rollback, cleanup, and cost controls remain required.

## Evaluation model

Evaluate Stategraph during ordinary work using a short observation record for each participating increment:

- change objective and exact source;
- standard Terraform/OpenTofu path duration and friction;
- Stategraph path duration and friction;
- dependencies or blast radius found earlier;
- missed or misleading relationships;
- plan disagreements and their resolution;
- confidence gained or lost;
- fallback or export effort;
- whether the lab advanced faster without weakening evidence or control.

The final judgment is practical:

```text
useful_in_real_changes
and reversible
and confidence_increased
and governance_not_weakened
```

If those conditions are not observed, keep Stategraph optional or remove it.

## Success signals

- less repeated dependency investigation;
- earlier discovery of affected resources;
- clearer change and incident lineage;
- faster safe planning for real increments;
- fewer missed dependencies or avoidable retries;
- easy return to standard Terraform/OpenTofu;
- evidence remains at least as strong as before.

## Stop conditions

Stop and return to the standard Terraform/OpenTofu path when:

- diagnostics identify unsupported repository constructs;
- import/export equivalence cannot be established;
- sensitive state handling is unclear or unacceptable;
- plans disagree materially without a deterministic resolution;
- Stategraph adds more workflow friction than useful context;
- fallback is not immediately usable;
- cost or deployment requirements are disproportionate to the lab;
- the experiment competes with a higher-priority Lab v1 criterion.

## Authority boundary for this increment

Authorized:

- record this strategy and machine-readable decision;
- add deterministic repository tests;
- create a bounded branch and draft pull request.

Not authorized:

- merge;
- workflow dispatch or rerun;
- Stategraph account creation, installation, authentication, import, export, plan, or apply;
- Terraform/OpenTofu state access or migration;
- Azure authentication, query, mutation, deployment, RBAC, network, policy, monitoring, or cleanup action;
- conversion of the current Bicep workload into Terraform.

```text
strategy_accepted != execution_authorized
Design_For != Build_Now
optional_capability != operational_authority
```

## Next gate

The next Stategraph gate is not tool installation. It is the first genuine Terraform/OpenTofu lab increment that satisfies the admission rule. At that point, begin with standard Terraform success and Stategraph diagnostics in shadow mode.
