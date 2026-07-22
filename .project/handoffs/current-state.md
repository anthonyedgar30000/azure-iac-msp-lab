# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Live repository baseline

- Default branch: `main`.
- Current baseline: `777ec83b8a447f01904d5f891795ebcb6ab7abaf`.
- PR #32, **Add fail-closed collector recovery evidence schemas**, merged at that commit.
- PR #32 merged exact head `f640f6664ab72deece24b770fe95cba51b0ac6ea`.
- That head passed CI run `29946271140` (run 102).
- Evidence-quality review of the same exact head recorded **CHANGES REQUIRED** before the merge.

Canonical interpretation:

```text
PR merged
!= blocking review resolved
!= evidence contract approved
!= recovery operationally verified
```

## Active repair increment

- Workstream: `collector-recovery-evidence-review-remediation`.
- Branch: `fix/recovery-evidence-review-remediation`.
- Pull request: #33, **Repair collector recovery evidence review findings**.
- PR state: open draft.
- Write owner: this explicitly authorized bounded repair conversation.
- Status: exact-head CI pending.
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

## Repair PR reality

- Base: current `main` at PR creation, `777ec83b8a447f01904d5f891795ebcb6ab7abaf`.
- Head after this coordination update: resolve from live GitHub.
- Final diff before PR-number binding: exactly the seven declared files.
- Local validation: 31 tests passed.
- Exact-head GitHub CI: pending.
- Evidence-quality re-review: pending.

PR #32 run 102 applies only to the predecessor version and must not be represented as verification of PR #33.

## Blocking findings repaired

The review of PR #32 head `f640f6664ab72deece24b770fe95cba51b0ac6ea` found:

1. contract values used by package validation were not all pinned against weakening;
2. record-type detail requirements were documented but not enforced;
3. redaction metadata was not bound to exact recursive marker paths;
4. target resource IDs could cross subscriptions;
5. non-finite JSON numbers were accepted;
6. superseded packages lacked mandatory provenance.

PR #33 now:

- pins all package-validator-driving contract values;
- enforces evidence-bearing detail fields for every record type;
- recursively derives redaction marker paths and requires exact metadata coverage;
- requires one declared subscription across every target Azure resource ID;
- rejects non-finite JSON numbers;
- records producer tool, version, identity, and source commit;
- requires bounded supersession provenance;
- prevents superseded packages from retaining verified operational claims;
- preserves `authority_granted = false` and `azure_mutations_authorized = false`.

## Evidence package boundaries

The package remains `servicetracer.collector-recovery-evidence.v1` and is design-only.

Every package preserves:

- package and producer provenance;
- maintenance correlation;
- exact target subscription and resource IDs;
- record identities, types, phases, timestamps, logical command identities, exit statuses, before/after states, and evidence SHA-256 values;
- typed details by record type;
- exact redaction provenance;
- explicit supersession provenance where applicable;
- explicit claim boundaries.

Completeness is evaluated only against declared phases. Missing evidence is reported and cannot silently become success.

## Verification state

- Contract-only local validation: passed.
- Local remediation suite: 31 tests passed.
- Changed-file boundary: exactly seven governed files before this final coordination commit; reverify against live GitHub.
- Exact-head CI for the live PR #33 head: pending.
- Evidence-quality re-review: pending.

The repair branch was reconstructed from the complete remediation tree after the concurrent PR #32 merge. Branch ancestry may show the prior feature history, but the final tree and exact PR diff—not commit-message appearance—determine scope.

## Azure and runtime evidence boundary

The latest promoted Azure control-plane evidence remains read-only planner run `29856203054`, observed July 21, 2026.

The last guest-level record remains ServiceTracer `0.4.0` after manual repairs on July 20, 2026.

PR #33 does not query Azure, refresh guest evidence, implement collection commands, authenticate, deploy, mutate resources, restore RBAC, modify budgets or alerts, or prove snapshot recoverability, Trusted Launch bootability, rollback, or recovery.

## Required gates

1. reverify the final PR #33 diff contains exactly the seven declared files;
2. obtain fresh exact-head CI on the live coordination head;
3. inspect every CI job;
4. route the exact passing head for evidence-quality re-review;
5. preserve the owner-account reviewer-independence limitation;
6. keep PR #33 draft until all gates are satisfied.

## Failure behavior

If CI fails, keep the PR draft, inspect the exact job and logs, patch only the declared files, and run fresh exact-head CI. Do not weaken evidence requirements merely to make tests pass.

If re-review finds another defect, record the exact reviewed head and CI run, patch within scope or explicitly amend scope, and repeat CI and review.

Repository rollback is closing PR #33 without merge or reverting its commits. No Azure rollback applies because this increment performs no Azure mutation.

## Prohibited next step

Do not merge PR #33 based only on local tests. Do not add live guest or Azure collection commands, activate a workflow, authenticate to Azure, deallocate the collector, create snapshots or rehearsal resources, alter delete options, remove or deploy compute, restore RBAC, modify budgets or alerts, or claim operational recovery.
