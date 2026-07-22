# Collector replacement rollback decision

## Decision state

**Snapshot-and-recreate remains the selected repository design. A blocking operations-and-recovery finding remained open when PR #28 was merged. This contract-amendment increment addresses that finding; nothing is deployed or operationally tested.**

This record does not activate a workflow, authenticate to Azure, create snapshots, deallocate or delete a VM, change delete options, restore RBAC, modify budgets, or authorize replacement execution.

## Selected strategy

Strategy: `os_disk_snapshot_recreate_canonical_name`

The canonical OS-disk name remains `disk-stcollector-os-mst-dev`. The design uses an exact verified OS snapshot rather than retaining the old OS disk directly.

## Evidence reviewed

- merged fail-closed execution design from PR #25;
- promoted read-only planner run `29856203054`;
- artifact `collector-replacement-plan-29856203054-1` with SHA-256 `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`;
- PR #27 recovery-contract changes and partial merge;
- PR #28 exact head `e98c6039d4a896bea49f48af0eb0c733ee491f5b`;
- exact-head CI run `29899440550` (run 84), which passed;
- operations-and-recovery review of that exact head, which recorded **CHANGES REQUIRED**;
- merge commit `cb5b38f3d6ab861f54f72897e6cf625a04c275e8`, which brought PR #28 into `main` after that blocking review;
- conditional Azure-cost planning decision approved by Anthony Edgar.

CI proves repository execution only. The planner evidence does not prove current guest health, crash consistency, snapshot recoverability, Trusted Launch bootability, rollback, current price, quota, actual cost, or execution authority.

## Merge-reality reconciliation

The exact-head review found that two earlier issues were resolved:

1. quiesce actions were validated in exact order and explicitly included collector-service stop;
2. `.project` distinguished code-bearing CI from coordination-only CI.

The remaining blocker was not cosmetic. The design documents described rehearsal teardown, but the authoritative contract contained only generic eventual cleanup. The validator then returned successful teardown booleans without reading corresponding contract fields. Tests asserted those synthesized values, so a contract that allowed rehearsal compute to survive until final cleanup still passed.

PR #28 merged despite that review outcome. Therefore:

- `merged_into_main != operations_and_recovery_approved`;
- the PR #28 merge is repository history, not proof that the recovery contract was complete;
- the next bounded increment must amend the authoritative contract and then obtain fresh exact-head CI and re-review.

## Exact quiescence retained

The contract continues to validate this exact sequence:

1. stop accepting new writes;
2. drain in-flight writes;
3. flush evidence writes;
4. record final checkpoint ID and SHA-256;
5. record maintenance correlation ID;
6. stop the collector service;
7. verify guest shutdown;
8. deallocate the source VM;
9. verify Azure `PowerState/deallocated`.

Negative tests reject reordering and service-stop omission.

## Contract-backed rehearsal teardown amendment

The schema is advanced to `servicetracer.collector-replacement-execution-design.v2` and gains an authoritative `rehearsal_teardown` object plus a distinct `teardown_isolated_rehearsal` phase.

The contract now requires, before `remove_old_compute`:

- rehearsal VM power state `PowerState/deallocated`;
- source VM still `PowerState/deallocated`;
- removal of the temporary rehearsal VM;
- removal of the temporary isolated NIC;
- zero minutes of running-compute overlap;
- an explicit retained-artifact allowlist containing only the verified OS snapshot, verified evidence snapshot, and an approved temporary recovery disk;
- rejection of every unapproved retained artifact;
- phase evidence proving deallocation, resource absence, source-state preservation, retained-artifact compliance, and zero overlap.

The validator reads and validates those contract fields. It no longer synthesizes teardown success from phase ordering and generic cleanup controls.

Negative tests now reject:

- missing or altered rehearsal deallocation requirements;
- missing temporary VM or NIC removal requirements;
- a teardown boundary moved after replacement deployment;
- an unapproved retained artifact;
- a missing teardown phase;
- non-zero running-compute overlap.

## Candidate workflow drift repaired

The non-dispatchable workflow design previously omitted multiple authoritative phases, including quiescence and rehearsal. Its phase markers now match the complete contract order, and a regression test compares the two lists exactly.

This alignment still does not activate the workflow or add Azure mutation commands.

## Deterministic rollback contract

If replacement verification fails after old-compute removal:

1. preserve both verified snapshots, the production NIC, and the evidence disk;
2. re-read production attachment `Detach` semantics;
3. delete only failed replacement compute and its disposable OS disk;
4. recreate the canonical OS disk from the exact verified snapshot using `Copy`;
5. validate all recorded recreation metadata;
6. recreate the collector VM by attaching the specialized OS disk using `Attach`;
7. attach the preserved NIC and evidence disk using `Detach`;
8. restore only approved RBAC to the new system-assigned identity;
9. prove boot, evidence UUID/readability, service health, durable write, restart persistence, identity, RBAC, network behavior, disk policy, and attachment semantics.

The evidence disk is never deleted, formatted, replaced, restored over, or attached to the isolated rehearsal VM.

## Cost boundary

- reviewed planning estimate: CAD 4;
- renewed approval required above CAD 4;
- unconditional stop above CAD 10;
- maximum two snapshots and 96 GiB total;
- maximum isolated rehearsal compute: four hours;
- maximum temporary-resource retention: 24 hours;
- maximum running-compute overlap: zero minutes.

This remains planning feasibility, not a current subscription-specific quote or actual-cost observation. Fresh authenticated pricing, SKU availability, quota, cleanup owner, and deadline are still required.

## Why promotion remains blocked

- rollback is `strategy_selected_design_only`;
- `operationally_tested` remains `false`;
- Azure mutations remain unauthorized;
- the contract-amendment head needs fresh CI and operations-and-recovery re-review;
- execution commands are not yet fake-Azure-CLI tested;
- guest/control-plane evidence schemas are incomplete;
- RBAC restoration allowlist is unresolved;
- current pricing, SKU availability, quota, cleanup owner, and deadline are unverified;
- evidence-quality and security/identity reviews remain required.

## Conclusion

Snapshot-and-recreate remains preferred because it preserves canonical IaC naming and provides a bounded recovery route. The contract now makes rehearsal teardown an explicit, fail-closed transition rather than a documentation claim. Approval is still withheld until CI and review validate the exact amendment head, and operational proof remains a later, separately authorized lifecycle increment.
