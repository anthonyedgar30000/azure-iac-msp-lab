# Collector replacement rollback decision

## Decision state

**Selected as a repository design; not independently approved, deployed, or operationally tested.**

This review selects the rollback architecture for the collector replacement candidate. It does not activate a workflow, authenticate to Azure, create snapshots, change delete options, delete a VM, create a disk or VM, restore RBAC, or authorize use of the `REPLACE:` confirmation phrase.

## Evidence reviewed

- merged fail-closed execution design from PR #25;
- current replacement contract and deterministic validator;
- promoted read-only planner run `29856203054`;
- planner artifact `collector-replacement-plan-29856203054-1` with SHA-256 `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`;
- current Bicep collector module, which declares the canonical OS-disk name `disk-stcollector-os-mst-dev` and currently uses delete-on-VM-delete semantics;
- current environment facts for the preserved evidence disk, static-address NIC, system-assigned identity, and disposable OS disk.

The planner evidence proves bounded Azure control-plane configuration only. It does not prove the current OS-disk size, guest service state, snapshot recoverability, bootability from a recreated disk, or successful rollback.

## Options considered

### Option A: preserve the old OS disk directly

The old OS disk would be detached and retained while a replacement VM used a different OS-disk name.

Advantages:

- the prior boot disk remains directly available;
- rollback does not depend on recreating a managed disk from a snapshot.

Costs and defects:

- the replacement cannot use the canonical OS-disk name while the old disk exists;
- the current Bicep module would no longer converge without a second naming change;
- the design would introduce a temporary or permanent alternate naming convention;
- later cleanup and IaC reconciliation would require another authority-bearing change.

### Option B: snapshot the old OS disk and recreate it if rollback is required

The old OS disk receives a bounded, independently verified snapshot. After both the evidence-disk and OS-disk recovery points are verified, the old VM and disposable OS disk may be removed. The replacement keeps the canonical OS-disk name. If replacement verification fails, the prior boot disk is recreated from the verified snapshot under the same canonical name and the prior VM boundary is rebuilt with the preserved NIC and evidence disk.

Advantages:

- preserves the canonical OS-disk name expected by the current IaC model;
- avoids a second naming migration merely to restore convergence;
- creates a deterministic recovery object with explicit source identity, size, generation, access-policy, ownership, and expiry checks;
- fits the existing maximum of two snapshots and 96 GiB total only when the current OS disk is no larger than 64 GiB.

Risks:

- snapshot creation success is not proof that the prior VM can boot after recreation;
- the old system-assigned principal cannot be recovered and must be treated as a new identity;
- Trusted Launch, Hyper-V generation, OS type, encryption, and disk security metadata must be captured and preserved;
- the strategy must fail closed if the OS disk exceeds the 64 GiB snapshot allocation or if any required metadata is missing.

## Selected strategy

**Option B: `os_disk_snapshot_recreate_canonical_name`.**

The canonical OS-disk name remains:

`disk-stcollector-os-mst-dev`

The future OS-disk snapshot must use a deterministic execution-scoped name beginning with:

`snap-stcollector-os-rollback-mst-dev-`

The selected design does not preserve the old OS disk directly. It requires:

1. fresh preflight capture of the old OS-disk resource ID, size, OS type, Hyper-V generation, Trusted Launch/security type, encryption configuration, network access policy, and public access state;
2. a verified evidence-disk snapshot;
3. a separately verified OS-disk snapshot;
4. a hard stop if the OS disk exceeds 64 GiB or the combined snapshot ceiling would exceed 96 GiB;
5. restrictive snapshot network access, required ownership/cleanup tags, and retention of no more than 24 hours;
6. removal of old compute only after both recovery points are independently verified;
7. rollback recreation of the canonical OS disk from the verified snapshot using create option `Copy`;
8. recreation of `vm-stcollector-mst-dev` with the preserved NIC and evidence disk;
9. capture of the new system-assigned principal and restoration of only an approved RBAC allowlist;
10. boot, mount UUID, evidence readability, service, health, durable-write, restart-persistence, identity, RBAC, NIC, address, and disk-policy acceptance checks.

## Why the design remains blocked

Repository tests can prove that required fields and phase ordering exist. They cannot prove Azure snapshot recoverability or that the prior collector will boot from a recreated disk.

The contract therefore records:

- rollback status: `strategy_selected_design_only`;
- operationally tested: `false`;
- independent review status: `pending`;
- promotion blocked: `true`;
- dispatch authorized: `false`;
- Azure mutations authorized: `false`.

## Required next evidence

Before workflow promotion, a separate bounded increment must define a fake-Azure-CLI-tested recreation implementation and an independently testable recovery-verification package. Any real recovery drill or replacement execution requires a separate authority-changing PR, protected-environment approval, current cost review, and explicit human authorization.

## Review conclusion

The snapshot-and-recreation strategy is the preferred deterministic design because it preserves canonical IaC naming and avoids a second disk-name migration. This conclusion is a design decision only. Independent operations-and-recovery review is still required, and no claim of actual recoverability is made.
