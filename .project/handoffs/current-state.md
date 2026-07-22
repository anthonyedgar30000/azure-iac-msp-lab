# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Live repository baseline

- Default branch: `main`.
- Current baseline: `777ec83b8a447f01904d5f891795ebcb6ab7abaf`.
- PR #32 merged exact head `f640f6664ab72deece24b770fe95cba51b0ac6ea` despite a blocking evidence-quality review on that same head.
- PR #32 run `29946271140` (run 102) passed, but it verifies the reviewed-defective version only.

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
- Authority: repository design only.

Permitted files:

- `infra/recovery/collector-recovery-evidence-contract.json`;
- `infra/recovery/recovery_evidence_core.py`;
- `infra/recovery/validate_recovery_evidence.py`;
- `infra/tests/test_collector_recovery_evidence.py`;
- `docs/designs/collector-recovery-evidence-schemas.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Protected boundaries include workflows, replacement execution, Bicep modules, application source, credentials, live evidence, Azure mutation scripts, budgets, alerts, and deployed resources.

No other conversation should edit this branch or these seven paths unless ownership is explicitly transferred.

## Repair verification chronology

### Code-bearing repair head

- Exact head: `018f4769f67972bf61f947dcd29380015f116ac4`.
- Exact-head CI: run `29947999922` (run 107), completed successfully.
- ServiceTracer tests job: passed, including `.project` validation, unit tests, evidence spool and CLI smoke paths, and replay compatibility.
- Bicep lint and build job: passed, including collector contract validation.
- Changed-file boundary: exactly the seven permitted files.

### Evidence-quality re-review

The evidence-quality lens reviewed exact head `018f4769f67972bf61f947dcd29380015f116ac4` with run 107 and recorded:

**TECHNICAL PASS — NO BLOCKING FINDINGS ON THE REVIEWED REPAIR HEAD**

The repair resolves:

1. contract self-protection against weakening;
2. evidence-bearing detail enforcement for all record types;
3. exact recursive redaction provenance;
4. one subscription boundary across target resource IDs;
5. canonical finite JSON enforcement;
6. supersession provenance and verified-claim invalidation.

Producer tool, version, identity, and source commit are also required. The validator continues to return `authority_granted = false` and `azure_mutations_authorized = false`.

Reviewer-independence boundary:

- the review was submitted through the pull-request owner's authenticated account;
- the repository may claim a recorded evidence-quality technical pass;
- it may not claim independent organizational approval.

### Final coordination head

This handoff and `.project/active-work.json` are coordination-only records written after the code-bearing CI and review.

- Run 107 remains the exact code-bearing-head verification.
- Live GitHub determines the final coordination head after this update.
- Fresh exact-head CI is required for that final coordination head.
- Do not create a self-referential claim that run 107 verifies later coordination commits.

## Repair contents

PR #33 now:

- pins all package-validator-driving contract values;
- enforces typed minimum details for all nine record types;
- recursively derives redaction marker paths and requires exact metadata coverage;
- requires one declared subscription across every target Azure resource ID;
- rejects non-finite JSON numbers;
- records producer tool, version, identity, and source commit;
- requires bounded supersession provenance;
- prevents superseded packages from retaining verified operational claims;
- preserves design-only and no-authority boundaries.

The local remediation suite contains 31 tests. Synthetic fixtures prove validator behaviour only and are not operational evidence.

## Azure and runtime boundary

The latest promoted Azure control-plane evidence remains read-only planner run `29856203054`, observed July 21, 2026. The last guest-level record remains ServiceTracer `0.4.0` after manual repairs on July 20, 2026.

PR #33 does not query Azure, refresh guest evidence, implement collection commands, authenticate, deploy, mutate resources, restore RBAC, modify budgets or alerts, or prove snapshot recoverability, Trusted Launch bootability, rollback, or recovery.

## Remaining gates

1. obtain fresh exact-head CI for the final coordination head;
2. inspect both CI jobs and every material step;
3. reverify the final diff still contains exactly seven governed files;
4. record final read-only scope/diff confirmation;
5. keep PR #33 draft unless an explicit merge decision is made separately.

## Prohibited next step

Do not merge PR #33 based only on run 107. Do not activate workflows, add live collection commands, authenticate to Azure, deallocate the collector, create snapshots or rehearsal resources, alter delete options, remove or deploy compute, restore RBAC, modify budgets or alerts, or claim operational recovery.
