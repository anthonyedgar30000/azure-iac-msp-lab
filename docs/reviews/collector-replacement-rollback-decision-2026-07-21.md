# Collector replacement rollback decision

## Decision state

**Selected as a repository design; review findings addressed in code and pending independent re-review. Not deployed or operationally tested.**

This record selects the rollback architecture and documents remediation of the first independent operations-and-recovery review. It does not activate a workflow, authenticate to Azure, create snapshots, deallocate or delete a VM, change delete options, create a disk or VM, restore RBAC, or authorize the `REPLACE:` phrase.

## Evidence reviewed

- merged fail-closed execution design from PR #25;
- promoted read-only planner run `29856203054`;
- artifact `collector-replacement-plan-29856203054-1` with SHA-256 `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`;
- current collector Bicep and promoted control-plane facts;
- PR #27 exact head `bad79ac2a8ba8fa9568737fc3c3635b93f2dbaca` and passing CI run `29867691197`;
- independent operations-and-recovery review that requested four changes;
- Azure-cost planning decision approved by Anthony Edgar on 2026-07-22.

The planner evidence does not prove current guest health, crash consistency, snapshot recoverability, Trusted Launch bootability, or rollback.

## Selected strategy

**`os_disk_snapshot_recreate_canonical_name`**

The canonical OS-disk name remains `disk-stcollector-os-mst-dev`. The design does not retain the old OS disk directly. It uses an exact verified snapshot to preserve canonical naming and deterministic rollback.

## Independent review findings and remediation

### 1. Consistency boundary before snapshots

**Finding:** Metadata-only snapshot verification could permit old-compute deletion without a consistent recovery point. Separately captured OS and evidence disks could represent different moments.

**Remediation encoded:**

- add `quiesce_and_deallocate_source` before snapshot creation;
- stop accepting writes and drain in-flight writes;
- flush pending evidence writes;
- record a final evidence checkpoint ID and SHA-256;
- record a maintenance correlation ID;
- stop the service and verify guest shutdown;
- deallocate the source and verify Azure `PowerState/deallocated`;
- prohibit snapshot capture before the boundary;
- bind both snapshots to the same correlation and checkpoint evidence.

Negative tests reject pre-boundary snapshot capture and missing checkpoint binding.

### 2. Exact-snapshot Trusted Launch boot proof

**Finding:** Snapshot provisioning metadata does not prove that the prior Trusted Launch VM can boot. VM Guest State or vTPM state could be unusable.

**Remediation encoded:**

- add `isolated_snapshot_boot_rehearsal` before `remove_old_compute`;
- use the exact verified OS snapshot;
- create a temporary managed disk with `Copy`;
- attach the specialized disk to an isolated temporary VM with `Attach`;
- use the recorded Trusted Launch profile;
- keep the source VM deallocated;
- use no production NIC and no production evidence disk;
- prove OS boot, VM Guest State/vTPM viability, and bounded health;
- constrain compute to four hours and recovery resources to 24 hours;
- retain `operationally_tested: false` because repository design is not an Azure drill.

Negative tests reject a non-exact snapshot and any production attachment during the rehearsal.

### 3. Deterministic `Copy` and `Attach` semantics

**Finding:** Snapshot-to-disk recreation and disk-to-VM attachment were not distinguished strongly enough.

**Remediation encoded:**

- snapshot to managed OS disk: `Copy`;
- specialized managed OS disk to VM: `Attach`;
- `FromImage` is prohibited;
- validate disk SKU, OS type, Hyper-V generation, Trusted Launch/security profile, encryption and DES when present, zone when present, network/public-access policy, and OS-disk delete option.

Negative tests reject `FromImage`, missing `Attach`, and metadata drift.

### 4. Preserve production NIC and evidence disk on every compute boundary

**Finding:** A failed replacement could again delete the preserved NIC if replacement attachment semantics remained `Delete`.

**Remediation encoded:**

- replacement NIC: `deleteOption: Detach`;
- replacement evidence disk: `deleteOption: Detach`;
- rollback NIC: `deleteOption: Detach`;
- rollback evidence disk: `deleteOption: Detach`;
- re-read both settings after VM creation;
- re-read both before any failed-compute deletion.

Negative tests reject `Delete` for any preserved production attachment.

## Cost boundary

The isolated rehearsal is included in the approved planning boundary:

- reviewed planning estimate: CAD 4;
- renewed approval required above CAD 4;
- unconditional stop above CAD 10;
- two snapshots, at most 96 GiB total;
- isolated rehearsal compute at most four hours;
- temporary resources retained at most 24 hours;
- zero overlap between old running compute and rehearsal or replacement compute.

This is planning feasibility, not a subscription-specific quote or actual-cost observation. A future run requires authenticated pricing, SKU availability, quota, cleanup owner, and deadline evidence.

## Deterministic rollback contract

If replacement verification fails after old-compute removal:

1. preserve both snapshots, the production NIC, and the evidence disk;
2. re-read NIC and evidence-disk `Detach` semantics;
3. delete only failed replacement compute and its disposable OS disk;
4. create `disk-stcollector-os-mst-dev` from the exact verified snapshot using `Copy`;
5. validate all recorded recreation metadata;
6. recreate `vm-stcollector-mst-dev` by attaching the specialized OS disk using `Attach`;
7. attach the production NIC and evidence disk with `Detach`;
8. re-read attachment semantics after creation and before any later failed-compute deletion;
9. restore only approved RBAC to the new system-assigned principal;
10. prove boot, evidence UUID/readability, service, health, durable write, restart persistence, identity, RBAC, network, and disk policies.

The evidence disk is never deleted, formatted, replaced, restored over, or attached to the isolated rehearsal VM.

## Why the design remains blocked

Repository tests prove contract structure and fail-closed ordering. They do not prove that Azure commands are correct, that snapshots are recoverable, or that the full production rollback works.

The contract therefore records:

- rollback status: `strategy_selected_design_only`;
- operationally tested: `false`;
- independent review status: `changes_addressed_re_review_pending`;
- promotion blocked: `true`;
- dispatch authorized: `false`;
- Azure mutations authorized: `false`.

## Required next evidence

Before promotion:

- fresh exact-head CI must pass;
- independent operations-and-recovery re-review must approve or request further changes;
- recovery and rehearsal commands must be fake-Azure-CLI tested;
- guest/control-plane evidence schemas must be defined;
- identity/RBAC restoration must use an allowlist;
- subscription-specific cost/quota and cleanup gates must be implemented;
- final evidence-quality and security/identity reviews must be completed.

Any Azure drill or collector replacement requires a separate authority-changing PR, protected-environment approval, and explicit human authorization.

## Conclusion

The snapshot/recreation strategy remains preferred because it preserves canonical IaC naming. The four first-review findings are now represented as machine-validated design invariants and negative tests. This is a remediation claim only, not independent approval or operational recoverability proof.
