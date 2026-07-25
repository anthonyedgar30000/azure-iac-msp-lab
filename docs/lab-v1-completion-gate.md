# Azure IaC MSP Lab v1 Completion Gate

## Governing objective

> Complete and evidence-lock one production-shaped ServiceTracer workload from infrastructure-as-code declaration through deployment, security, runtime validation, monitoring, cost observation, and portfolio demonstration.

This is the Lab v1 priority. The lab does not need another architecture branch, workload, agent, dashboard, or governance abstraction before this vertical slice is complete.

The machine-readable authority is [`.project/lab-v1-completion-gate.json`](../.project/lab-v1-completion-gate.json).

## Why this gate exists

The repository already contains substantial IaC, workflow, evidence, governance, recovery-design, and ServiceTracer capability. The unresolved gap is the connection between those declarations and one finished, independently demonstrable operational outcome.

The gate therefore converts the project from an expanding idea inventory into an ordered completion program:

```text
P0: make one workload work and prove it
P1: make that workload credibly operable
P2: package the evidence into a portfolio demonstration
```

No lower-priority feature may bypass an unmet higher-priority exit criterion.

## Scope-admission rule

A new **Build Now** item is admitted only when it does at least one of the following:

1. directly closes a Lab v1 completion criterion;
2. removes a material security or operational credibility defect;
3. produces evidence required by the final demonstration.

Everything else is classified as **Design For** or **Future Vision** until P0 through P2 are complete.

```text
interesting != priority
architecturally_valid != build_now
repository_implemented != operationally_complete
```

## P0 — Complete the golden path

P0 terminates only when the following are evidenced or explicitly classified as blocked for human decision.

### 1. Resolve protected verification evidence

Recover and inspect the exact existing PR #92 protected verify-only run and sanitized artifact.

If the existing result cannot be durably recovered, a new attempt requires a separate, explicit, exact-commit verify-only authorization. The old grant is not renewed by this gate.

Required outcome:

- exact run identity;
- exact source SHA;
- exact-head CI linkage;
- ARM validation result;
- extension-only What-If result;
- before/after resource inventory;
- public health evidence;
- sanitized artifact provenance.

### 2. Establish effective extension-write permission

The dedicated target identity must prove effective:

```text
Microsoft.Compute/virtualMachines/extensions/write
```

An observed role definition or assignment is supporting evidence, not the completion condition. Completion requires accepted extension-only ARM validation and What-If evidence against the intended VM extension scope.

```text
RBAC_assignment != effective_least_privilege
```

### 3. Deploy the corrected runtime

Deploy the already-merged timeout correction from an exact reviewed commit through the governed deployment path.

This requires:

- fresh reality synchronization for the exact Azure scope;
- accepted fail-closed What-If;
- explicit deployment authority;
- immutable source binding;
- deployment evidence;
- stop and rollback behaviour.

This repository-only gate does not grant that authority.

### 4. Verify the corrected service contract

After deployment, independently verify:

- TLS;
- HTTP 200 health;
- corrected timeout fields;
- CORS;
- stable public endpoint behaviour;
- deployed source provenance.

The currently promoted healthy endpoint evidence describes the pre-timeout-fix contract and therefore does not close this criterion.

### 5. Run the bounded ServiceTracer demonstration

Execute and preserve 20 correlated transactions with:

- VPN-01 as the healthy comparison backend;
- VPN-02 as the intended failing backend;
- the failure concentrated at the intended service boundary;
- deterministic localization;
- no unsupported exact-device root-cause claim.

The demonstration must preserve:

```text
fault_boundary_localized != exact_root_cause_proven
```

### 6. Verify the live browser path

Prove the operator console renders the live corrected API through explicit endpoint activation while retaining the committed fixture as the safe default.

```text
fixture_demo != live_demo
```

### 7. Lock the evidence chain

Capture and retain:

```text
exact commit
→ exact-head CI
→ authorization
→ What-If
→ deployment
→ Azure inventory
→ corrected runtime health
→ transaction evidence
→ ServiceTracer finding
→ browser rendering
→ sanitized portfolio evidence
```

Every artifact must preserve its observation time, provenance, limitations, and claim boundary.

## P1 — Make the workload credibly operable

P1 begins only after P0 is complete or a human explicitly accepts a remaining bounded limitation.

Required outcomes:

- enable the minimum useful supported diagnostic path;
- create one meaningful metric or availability alert;
- independently verify alert delivery through an action group;
- verify effective least privilege for the deployment and verification identities;
- capture a time-bounded actual-cost observation in CAD;
- document restart, redeployment, failure classification, rollback boundary, and cleanup or decommissioning procedure.

### Deliberate Lab v1 exclusion

Azure Backup, Recovery Services, backup execution, and disaster-recovery rehearsal are not Lab v1 completion requirements.

```text
backup_scope = intentionally_out_of_scope_for_lab_v1
backup_intentionally_out_of_scope != backup_verified
```

They remain eligible for a later revision after the primary workload is complete.

## P2 — Package the portfolio proof

The final story must follow one source lineage:

```text
GitHub commit
→ exact-head CI
→ reviewed ARM What-If
→ explicit human deployment authority
→ Azure deployment
→ healthy corrected API
→ bounded synthetic service failure
→ deterministic ServiceTracer localization
→ verified operational alert or evidence
→ bounded technician handoff
→ cost observation
→ cleanup or decommissioning procedure
```

The portfolio claim must show what was actually deployed and verified. Repository declarations and designs may be shown separately, but they cannot be presented as runtime proof.

## Frozen until P0–P2 complete

The following are legitimate ideas but are not Build Now:

- zoomable hyperscaler or infrastructure-universe dashboard;
- broader Azure Resource Graph visualization;
- multicloud control plane;
- additional workloads;
- full collector replacement;
- recovery rehearsal and disaster recovery;
- automated cleanup execution;
- MSP multi-customer tenancy;
- HELIX integration;
- new governance engines or authority abstractions;
- additional dashboards;
- additional AI agents.

A frozen item may move into Build Now only when the admission rule is satisfied and the change does not delay a higher-priority completion criterion.

## Completion definition

Lab v1 is complete only when the same exact source lineage is connected to:

- reviewed IaC;
- authorized deployment;
- deployed Azure resources;
- corrected runtime behaviour;
- bounded ServiceTracer transaction evidence;
- effective security evidence;
- verified monitoring delivery;
- time-bounded cost evidence;
- a reproducible portfolio demonstration.

Canonical boundaries remain:

```text
merged_into_main != deployed_to_Azure
deployment_succeeded != service_validated
resource_exists != securely_configured
RBAC_assignment != effective_least_privilege
monitoring_enabled != alerts_verified
estimated_cost != actual_cost
```

## Creation baseline and parallel work

This gate was created from `main@630bbd8c9c37a3985a70dbe6bffe10437672a59d`.

Draft PR #95 was observed as a separate constitutional increment affecting:

- `.project/README.md`;
- `.project/constitution.md`;
- `.project/decisions.md`;
- `tests/test_synchronization_termination_principle.py`.

This gate deliberately uses non-overlapping paths and does not modify or inherit PR #95's bounded write authority.

No local working tree was available for inspection. No merge-result CI was observed on the base merge commit. No fresh Azure authentication, Resource Graph query, ARM operation, cost query, quota query, or runtime transaction was performed for this increment.

## Authority boundary

Authorized by Anthony Edgar's instruction to proceed:

- create this bounded repository-only completion gate;
- create deterministic validation;
- create a draft pull request.

Not authorized:

- pull-request merge;
- workflow dispatch or rerun;
- Azure authentication or query;
- Azure mutation or deployment;
- RBAC, identity, policy, secret, or network mutation;
- VM guest command or restart;
- transaction replay;
- endpoint publication;
- cleanup or decommissioning execution.

```text
priority_decision != operational_authorization
completion_gate_merged != deployment_authorized
```

## Next gate

Review and merge this bounded scope decision.

After merge, the first operational gate is:

> Inspect and promote the exact existing PR #92 protected verify-only run and artifact.

If that result cannot be recovered, any replacement verification attempt requires new explicit authorization.
