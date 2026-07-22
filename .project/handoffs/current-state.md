# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Trusted repository baseline

- Default branch: `main`.
- Exact baseline commit: `bb1351da492548242382a86db5293f44dabfb1f7`.
- Latest completed increment: PR #30, **Reconcile PR29 merge and close legacy PR1 state**.
- PR #30 was coordination-only and its exact head `a2b3d7032a1557f9b050b5c282b0e87b70bd2259` passed CI run `29943299617` (run 92).

Canonical boundary:

`repository_baseline_current != Azure_state_current`

## Active bounded increment

- Branch: `feature/collector-recovery-evidence-schema`.
- Pull request: #31, draft.
- Workstream: `collector-recovery-evidence-schema-design`.
- Status: exact-head CI pending.
- Authority: repository design only.
- Azure authentication authorized: no.
- Azure mutation authorized: no.
- Active execution workflow present: no.

Permitted paths:

- `infra/recovery-evidence/**`;
- `infra/tests/test_collector_recovery_evidence_design.py`;
- `docs/designs/collector-recovery-evidence-schema.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Protected paths:

- `.github/workflows/**`;
- `infra/modules/**`;
- the existing collector replacement execution contract and candidate workflow;
- application source;
- credentials and secrets;
- Azure mutation scripts;
- budgets, alerts, and live Azure resources.

## Intended evidence architecture

The increment defines a contract and five closed JSON Schema draft 2020-12 documents:

1. guest preflight evidence;
2. Azure control-plane preflight evidence;
3. phase-failure evidence;
4. rollback-outcome evidence;
5. a correlated recovery evidence bundle.

A standard-library Python validator generates a sanitized design fixture and enforces cross-record invariants that JSON Schema alone cannot prove:

- exact observation coverage;
- unique evidence IDs;
- shared maintenance correlation and target binding;
- RFC3339 UTC timestamps and bounded freshness;
- command/result exit-code consistency;
- read-only preflight state;
- SHA-256 provenance bindings;
- raw-versus-sanitized evidence separation;
- secret-marker rejection;
- failure records when a preflight fails;
- separate authorized runtime evidence before rollback success can be claimed.

Canonical boundary:

`schema_valid != evidence_captured != execution_authorized != recovery_succeeded`

## Exact target and region scope

The design is pinned to:

- resource group: `rg-servicetracer-dev-westus2`;
- region: `westus2`;
- collector VM: `vm-stcollector-mst-dev`;
- collector NIC: `nic-stcollector-mst-dev`;
- evidence disk: `disk-stcollector-evidence-mst-dev`;
- OS disk: `disk-stcollector-os-mst-dev`;
- evidence mount: `/var/lib/servicetracer`.

These are intended evidence bindings, not current Azure observations.

## Required guest evidence

A complete guest preflight requires exactly eight fresh records:

- collector service active;
- local health endpoint success;
- evidence mount source;
- filesystem UUID;
- recent evidence readable;
- evidence checkpoint digest;
- guest OS identity;
- collector write-quiescence capability.

## Required Azure evidence

A complete Azure control-plane preflight requires exactly sixteen fresh records covering subscription context, exact resources, VM state and security profile, NIC and address binding, evidence- and OS-disk identity and access policy, recreation metadata, managed identity, visible RBAC, regional SKU availability, quota, temporary cost, and cleanup ownership/deadline.

`no_visible_role_assignments != effective_least_privilege_verified`

## Identity, security, and network boundary

- No identity or role is created by this increment.
- Future guest collection requires a bounded read-only identity.
- Future Azure collection requires separately approved minimum read-only access.
- Sanitized repository evidence stores hashes and placeholders instead of raw tenant, subscription, principal, and resource identifiers.
- Raw command output and raw private records are prohibited from repository promotion.
- No network path, NSG rule, endpoint, proxy, or DNS configuration changes.

## Cost and retention

- Azure cost of this repository increment: CAD 0.
- Raw future runtime evidence maximum retention: 24 hours unless separately approved.
- Existing future-operation planning boundary remains CAD 4, renewed approval above CAD 4, and unconditional stop above CAD 10.
- Fresh subscription-specific pricing, SKU availability, quota, cleanup owner, and cleanup deadline remain required before any temporary recovery resource.

## Validation performed before pull request

The design was exercised locally with:

```bash
python infra/recovery-evidence/validate_recovery_evidence.py --root .
python -m unittest discover -s infra/tests -v
```

The focused suite contains 23 tests, including negative cases for missing observations, duplicate identities, correlation and target drift, stale evidence, exit-code inconsistency, state mutation, Azure mutation authority, unredacted secrets, missing failure records, and unsupported rollback-success claims.

This local result is preparatory evidence only. Exact-head GitHub CI for the live PR #31 head remains the authority.

## Latest promoted Azure evidence

The latest promoted Azure control-plane evidence remains read-only planner run `29856203054`, captured July 21, 2026.

It does not prove current guest health, present resource state, current pricing, SKU availability, quota, actual cost, snapshot recoverability, Trusted Launch restore bootability, rollback, or effective RBAC. No Azure command was run for this increment.

## Failure and rollback behavior

If validation or CI fails:

1. keep PR #31 draft;
2. inspect the exact failing invariant and job;
3. patch only the declared paths;
4. run fresh exact-head CI;
5. do not weaken correlation, freshness, redaction, provenance, failure, or authority controls merely to pass.

Repository rollback is closing PR #31 without merge or reverting a later merge commit. No Azure rollback applies because no Azure authentication or mutation occurs.

## Cleanup and evidence capture

No temporary Azure resource exists to clean up. Preserve:

- exact branch and commit;
- changed-file list;
- validator output;
- focused test results;
- exact-head CI jobs and steps;
- evidence-quality review disposition;
- final merge or closure decision.

Do not call any of those artifacts guest health, Azure preflight, recovery, rollback, or current cost evidence.

## Next gate

1. Wait for exact-head PR #31 CI.
2. Inspect every job and step.
3. Perform an evidence-quality review against the exact passing head.
4. Preserve owner-account reviewer-independence limitations.
5. Keep PR #31 draft until the repository design gate is explicitly satisfied.
6. Keep Azure authentication, workflow activation, resource mutation, RBAC restoration, budget or alert changes, and operational recovery claims prohibited.
