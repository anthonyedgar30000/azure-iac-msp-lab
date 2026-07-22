# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Trusted repository baseline

- Default branch: `main`.
- Branch-creation baseline: `bb1351da492548242382a86db5293f44dabfb1f7`.
- Baseline increment: PR #30, **Reconcile PR29 merge and close legacy PR1 state**.
- PR #30 exact head `a2b3d7032a1557f9b050b5c282b0e87b70bd2259` passed CI run `29943299617` (run 92).
- PR #30 was coordination-only. It recorded PR #29 as completed, closed legacy PR #1 as superseded, and released previous write ownership.

Canonical interpretation:

```text
repository reconciled
!= Azure state refreshed
!= recovery executed
!= rollback operationally verified
```

## Active bounded increment

- Workstream: `collector-recovery-evidence-schema-design`.
- Branch: `feature/collector-recovery-evidence-schemas`.
- Write owner: this explicitly authorized bounded implementation conversation.
- Status: evidence-quality remediation; exact-head CI pending.
- Pull request: #32, draft.
- Authority: repository design only.

Permitted files:

- `infra/recovery/collector-recovery-evidence-contract.json`;
- `infra/recovery/recovery_evidence_core.py`;
- `infra/recovery/validate_recovery_evidence.py`;
- `infra/tests/test_collector_recovery_evidence.py`;
- `docs/designs/collector-recovery-evidence-schemas.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Protected boundaries:

- `.github/workflows/**`;
- `infra/replacement/**`;
- `infra/modules/**`;
- application source;
- credentials and secrets;
- live evidence packages;
- Azure authentication or mutation scripts;
- budgets and alerts;
- deployed resources.

No other conversation should edit this branch or these seven paths unless ownership is explicitly transferred.

## Pull request state

- Pull request: #32, **Add fail-closed collector recovery evidence schemas**.
- State: open draft.
- Base: `main` at `bb1351da492548242382a86db5293f44dabfb1f7`.
- Final authoritative head: resolve from live GitHub after this remediation handoff update.
- CI state: exact-head CI pending.
- Changed-file boundary: exactly the seven permitted files before this update; reverify against live GitHub after publication.

The branch history contains transient creation-and-deletion commits for an accidental temporary path. The path is absent from the final tree and PR diff. The exact changed-file comparison, not commit-message appearance alone, is the scope authority.

## Evidence-quality review chronology

The predecessor exact head `f640f6664ab72deece24b770fe95cba51b0ac6ea` passed CI run `29946271140` (run 102), including both ServiceTracer and Bicep jobs.

Evidence-quality review of that same exact head recorded **CHANGES REQUIRED**. The blocking findings were:

1. contract fields used by package validation were not all pinned against weakening;
2. record-type detail requirements were documented but not enforced;
3. redaction metadata was not bound to exact recursive marker paths;
4. target resource IDs could cross subscriptions;
5. non-finite JSON numbers were accepted;
6. superseded packages lacked mandatory provenance.

The remediation now:

- pins package statuses, record statuses, claim statuses, record types, limits, patterns, phase requirements, claim requirements, detail requirements, redaction policy, failure prohibitions, and cleanup boundaries;
- enforces minimum evidence-bearing details for every record type;
- derives redaction marker paths recursively and requires an exact metadata match;
- requires one declared subscription across all target Azure resource IDs;
- rejects non-finite JSON values;
- requires bounded supersession package IDs and prevents superseded packages from retaining verified operational claims;
- records producer tool, version, identity, and source commit.

Local remediation verification contains 31 tests and passed. Run 102 does not verify the remediation commits. Fresh exact-head CI and evidence-quality re-review are required.

## Objective

Define a fail-closed evidence package for future collector recovery work without implementing collection or execution.

The increment covers:

1. guest preflight evidence;
2. Azure control-plane preflight evidence;
3. exact correlation and UTC timestamp requirements;
4. logical command identity and exit status;
5. exact target resource IDs and one subscription boundary;
6. before/after state;
7. evidence digests;
8. recursive secret and redaction controls;
9. cleanup ownership, deadline, retention, and cost evidence;
10. failure, abort, supersession, rollback, and recovery claim requirements;
11. deterministic positive and negative validation.

## Contract boundary

The authoritative contract is:

- `infra/recovery/collector-recovery-evidence-contract.json`.

It remains `design_only` and explicitly records:

- active workflow absent;
- dispatch unauthorized;
- Azure authentication unauthorized;
- Azure mutation unauthorized;
- collection commands not implemented;
- promotion requiring a separate pull request.

The validator must never turn a structurally valid package into execution authority.

## Evidence package model

A future package uses:

- `servicetracer.collector-recovery-evidence.v1`.

Every package must preserve:

- package identity and producer provenance;
- record identity, type, and phase;
- observation timestamp;
- logical command identity;
- exit status;
- target resource ID;
- before and after state;
- evidence SHA-256;
- bounded typed details;
- redaction provenance;
- explicit supersession provenance when applicable.

Unknown top-level and record fields are rejected.

## Completeness rule

Completeness is evaluated against explicitly declared phases.

```text
complete package
requires
every required record type for every declared phase
and
no failed or aborted record
```

An incomplete package may remain valid evidence, but its missing record types must be reported. It cannot silently claim completeness.

## Secret and redaction rule

The validator recursively rejects:

- secret-like field names;
- credential-like value prefixes;
- non-finite JSON numbers;
- excessive nesting;
- excessive collection sizes;
- oversized text;
- raw command lines;
- unknown output fields.

A `[REDACTED]` value requires a structured field path and SHA-256 digest of the removed value. The validator derives marker paths recursively and requires the metadata path set to match exactly.

Complete Azure resource IDs are preserved as provenance inside the protected internal package. They are not credentials and cannot be replaced by untraceable redaction markers.

## Failure, supersession, and rollback rule

A failed or aborted package requires:

- a failed or aborted operation attempt;
- a matching terminal decision;
- reason;
- authority;
- safest next step;
- explicit rollback requirement.

A superseded package must identify at least one package ID that supersedes it. Other package states must not carry supersession IDs, and superseded packages cannot retain verified operational claims.

A verified rollback or recovery claim requires complete phase evidence and an accepted human recovery decision. Schema validation remains evidence for review, not permission for a new operation.

## Local verification

The bounded test suite now contains 31 tests covering:

- valid complete and incomplete packages;
- false-completeness rejection;
- contract drift for patterns, claims, detail requirements, and redaction policy;
- evidence-bearing detail-field enforcement;
- recursive secret leakage;
- credential prefixes;
- non-finite JSON;
- raw command identities;
- target drift and mixed subscriptions;
- non-UTC timestamps;
- exact redaction path and digest requirements;
- bounded nested data;
- duplicate records;
- failed-package decision evidence;
- verified-claim gates;
- supersession provenance;
- producer commit provenance;
- unknown record fields.

Local result:

```text
python -m unittest discover -s infra/tests -v
31 tests passed in the isolated increment fixture
```

This is local deterministic validation only. Exact-head GitHub CI for the remediation head is pending.

## Latest Azure evidence boundary

The latest promoted Azure control-plane evidence remains read-only planner run `29856203054`, observed July 21, 2026.

At that time:

- collector VM: `vm-stcollector-mst-dev`;
- size: `Standard_B2ats_v2`;
- deployed image: Ubuntu 22.04;
- desired image: Ubuntu 24.04;
- evidence disk: attached with `deleteOption: Detach`;
- production NIC: static address and VM `deleteOption: Delete`;
- system-assigned identity present;
- no visible role assignments in the planner result;
- no Azure mutations authorized or performed.

The last guest-level record remains ServiceTracer `0.4.0` after manual repairs on July 20, 2026.

This increment does not refresh either observation.

## Cost boundary

- Reviewed planning estimate: CAD 4.
- Renewed approval required above CAD 4.
- Hard stop: CAD 10.
- Maximum snapshot capacity: 96 GiB.
- Maximum isolated rehearsal compute: four hours.
- Maximum temporary-resource retention: 24 hours.
- Maximum running-compute overlap: zero minutes.

These are planning constraints, not current pricing or execution approval.

## Required gates

Before merge:

1. preserve exactly the seven declared files in the final diff;
2. obtain exact-head CI for the live PR #32 remediation head;
3. inspect every CI job;
4. route the exact passing remediation head for evidence-quality re-review;
5. preserve the owner-account reviewer-independence limitation;
6. keep the PR draft until those gates are satisfied.

## Failure behavior

If CI fails:

1. keep the pull request draft;
2. inspect the exact job and logs;
3. patch only the declared files;
4. run fresh exact-head CI;
5. do not weaken evidence or redaction requirements merely to make tests pass.

If re-review finds a defect:

1. record the exact reviewed head and CI run;
2. keep the pull request draft;
3. patch inside scope or explicitly amend the scope;
4. obtain fresh CI and re-review.

Repository rollback is closing the pull request without merge or reverting its commits. No Azure rollback applies because this increment performs no Azure mutation.

## Prohibited next step

Do not add live guest or Azure collection commands, activate a workflow, authenticate to Azure, deallocate the collector, create snapshots, create rehearsal resources, alter delete options, remove or deploy compute, restore RBAC, modify budgets or alerts, or claim snapshot recoverability, Trusted Launch bootability, rollback, or recovery as operationally verified.
