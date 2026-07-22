# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Trusted baseline

- Branch: `main`
- Current reconciled baseline: `4b181c644c48fde0c5d33f3cfabc24321977161a`
- Latest completed increment: PR #27, `Select snapshot-based collector rollback strategy`
- PR #27 merged while remediation was in progress. Its merge contains the recovery contract but not the matching validator, tests, and synchronized records.

## Active repair increment

- Branch: `fix/collector-rollback-review-remediation`
- Pull request: #28, draft
- Objective: repair the partial PR #27 merge and address the second operations-and-recovery review without changing the already-merged contract.
- Permitted files: validator, focused tests, execution design, rollback review, active-work state, and this handoff.
- Protected files: the replacement contract, active workflows, Bicep modules, application source, credentials, and Azure mutation scripts.

## CI and review chronology

The repository must distinguish code-bearing CI from coordination-only CI:

1. Commit `623647cad4d83083a416f4250ae8688e58a5fc57` was the last code-bearing remediation head before the coordination handoff update. CI run `29894210458` (run 76) passed.
2. Commit `7162506e5abad60f49c191309b85192d6d885a45` was the reviewed coordination-only head. Exact-head CI run `29894321483` (run 78) passed.
3. The operations-and-recovery re-review of `7162506e...` recorded **CHANGES REQUIRED** on July 22, 2026.

Live GitHub checks and review evidence are authoritative for the final coordination-only head. The predecessor CI run must not be described as final-head evidence.

## Second-review findings

### 1. Exact quiesce ordering

The validator converted `consistency_boundary.ordered_actions` to a set. That proved membership but discarded order and omitted the explicit requirement to stop the collector service.

The remediation validates this exact sequence:

1. stop accepting new collector writes;
2. drain in-flight collector writes;
3. flush pending evidence writes to the mounted evidence filesystem;
4. record the final evidence checkpoint identifier and SHA-256;
5. record the maintenance correlation identifier;
6. stop the collector service;
7. verify guest shutdown;
8. deallocate the source VM;
9. verify Azure `PowerState/deallocated`.

Negative tests reject reordering and omission of the service-stop action.

### 2. Rehearsal teardown before replacement compute

A four-hour cap and final cleanup phase do not prevent the isolated rehearsal VM from remaining allocated while replacement compute starts.

The fail-closed transition invariant is now:

- source compute remains deallocated throughout the rehearsal;
- after rehearsal proof is captured, the rehearsal VM is deallocated;
- the temporary rehearsal VM and isolated NIC are removed before `deploy_replacement_compute`;
- the verified OS-disk snapshot, verified evidence-disk snapshot, and an explicitly approved temporary recovery disk may remain until final acceptance;
- running-compute overlap remains zero minutes.

Negative tests reject cleanup omission and non-zero compute overlap.

### 3. Non-self-referential project state

`.project` records both the last code-bearing-head CI and the reviewed coordination-head CI, while treating live GitHub checks and review evidence as authority for the final head. A new code-bearing remediation commit requires fresh CI rather than editing `.project` into an endless final-head loop.

## Runtime and deployment state

The latest promoted Azure control-plane evidence remains dated July 21, 2026:

- resource group: `rg-servicetracer-dev-westus2`;
- collector size: `Standard_B2ats_v2`;
- deployed image: Ubuntu 22.04 Jammy;
- desired image: Ubuntu 24.04;
- evidence disk must be preserved;
- deployed NIC delete behavior remains an execution blocker;
- system-assigned identity replacement and approved RBAC restoration remain unresolved;
- last guest-level record: ServiceTracer `0.4.0` after manual repairs.

No Azure replacement, rehearsal, rollback, budget mutation, or RBAC restoration has been authorized or performed.

## Cost boundary

- Reviewed planning estimate: CAD 4.
- Renewed approval required above CAD 4.
- Hard stop: CAD 10.
- Maximum snapshot capacity: 96 GiB.
- Maximum isolated rehearsal compute: four hours.
- Maximum temporary-resource retention: 24 hours.
- Maximum running-compute overlap: zero minutes.
- Fresh authenticated subscription-specific pricing, SKU availability, quota, cleanup owner, and cleanup deadline remain required.

## Remaining blockers

- fresh CI on the new code-bearing remediation head;
- another operations-and-recovery review;
- guest/control-plane evidence schemas;
- fake-Azure-CLI-tested recovery and rehearsal implementation;
- identity/RBAC allowlist;
- fresh cost/quota preflight and cleanup ownership;
- final evidence-quality and security/identity reviews;
- protected-environment approval and explicit human authorization.

## Next bounded gate

1. Modify only the six declared PR #28 files.
2. Run `.project` validation, the complete Python suite, operational evidence smoke tests, collector VM validation, and Bicep lint/build on the new exact head.
3. Keep PR #28 draft.
4. Route the passing exact head for another operations-and-recovery review.
5. Keep all Azure authentication and mutations prohibited.

## Prohibited next step

Do not merge PR #28, activate the candidate workflow, authenticate to Azure for execution, deallocate the collector, create snapshots or rehearsal resources, change delete options, delete or deploy compute, restore RBAC, modify budgets or alerts, or claim rollback is operationally verified.
