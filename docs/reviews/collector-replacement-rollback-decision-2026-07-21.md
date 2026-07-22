# Collector replacement rollback decision

## Decision state

**Snapshot-and-recreate remains the selected repository design. The second operations-and-recovery review requested additional remediation. Nothing is deployed or operationally tested.**

This record does not activate a workflow, authenticate to Azure, create snapshots, deallocate or delete a VM, change delete options, restore RBAC, modify budgets, or authorize replacement execution.

## Selected strategy

Strategy: `os_disk_snapshot_recreate_canonical_name`

The canonical OS-disk name remains `disk-stcollector-os-mst-dev`. The design uses an exact verified OS snapshot rather than retaining the old OS disk directly.

## Evidence reviewed

- merged fail-closed execution design from PR #25;
- promoted read-only planner run `29856203054`;
- artifact `collector-replacement-plan-29856203054-1` with SHA-256 `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`;
- PR #27 recovery-contract changes and partial merge;
- draft PR #28 head `7162506e5abad60f49c191309b85192d6d885a45`;
- exact-head CI run `29894321483`, which passed;
- second operations-and-recovery review dated July 22, 2026, which recorded **CHANGES REQUIRED**;
- conditional Azure-cost planning decision approved by Anthony Edgar.

CI proves repository consistency only. The planner evidence does not prove current guest health, crash consistency, snapshot recoverability, Trusted Launch bootability, rollback, current price, quota, or execution authority.

## Second-review finding 1: order-sensitive quiescence

The prior validator converted `ordered_actions` to a set. That accepted unsafe reordering and did not explicitly require stopping the collector service.

The remediation validates this exact sequence:

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

## Second-review finding 2: rehearsal teardown

The earlier design capped rehearsal duration and required eventual cleanup, but it did not make teardown a mandatory transition before replacement compute.

The remediation establishes:

- source compute remains deallocated;
- rehearsal proof is captured from the exact verified OS snapshot under the recorded Trusted Launch profile;
- the rehearsal VM is deallocated after evidence capture;
- the rehearsal VM and isolated NIC are removed before replacement compute;
- no rehearsal compute remains allocated;
- only approved snapshots and temporary recovery disks may remain;
- running-compute overlap remains zero minutes.

Negative tests reject non-zero overlap and omission of the cleanup boundary.

## Second-review finding 3: CI and review chronology

The prior `.project` state identified predecessor commit `623647ca...` and CI run `29894210458` while calling it final-head evidence.

The corrected chronology distinguishes:

- last code-bearing head: `623647cad4d83083a416f4250ae8688e58a5fc57`, CI run `29894210458`;
- reviewed coordination-only head: `7162506e5abad60f49c191309b85192d6d885a45`, CI run `29894321483`;
- review outcome on the coordination head: **CHANGES REQUIRED**.

Live GitHub checks and review evidence are authoritative for the final coordination-only head. A new code-bearing remediation head requires fresh CI.

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

This is planning feasibility, not a current subscription-specific quote or actual-cost observation.

## Why promotion remains blocked

- rollback is `strategy_selected_design_only`;
- `operationally_tested` remains `false`;
- Azure mutations remain unauthorized;
- execution commands are not yet fake-Azure-CLI tested;
- guest/control-plane evidence schemas are incomplete;
- RBAC restoration allowlist is unresolved;
- current pricing, SKU availability, quota, cleanup owner, and deadline are unverified;
- another operations-and-recovery review is required;
- evidence-quality and security/identity reviews remain required.

## Conclusion

Snapshot-and-recreate remains preferred because it preserves canonical IaC naming and provides a bounded recovery route. The second-review changes strengthen order-sensitive quiescence, eliminate rehearsal/replacement compute overlap, and correct project-state chronology. They remain repository assertions until fresh CI and another independent review verify the new exact head.
