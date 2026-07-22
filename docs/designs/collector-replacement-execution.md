# Collector replacement execution design

## Status

**Design-only and fail-closed.**

The candidate workflow is stored at `infra/workflow-designs/collector-replacement-execution.yml`, outside `.github/workflows`. GitHub therefore cannot dispatch it. The candidate also exits before Azure authentication and contains no Azure mutation commands.

The governing machine-readable contract is `infra/replacement/collector-replacement-contract.json`. CI validates it with `infra/replacement/validate_execution_design.py` and `infra/tests/test_collector_replacement_execution_design.py`.

The rollback strategy is now selected as **OS-disk snapshot plus deterministic recreation under the canonical OS-disk name**. Selection is a repository design decision only. Rollback remains operationally untested, independently unapproved, and a blocker to workflow promotion.

This design does not authorize the generated `REPLACE:` phrase, Azure login, snapshot creation, delete-option changes, VM deletion, resource creation, role assignment, or cleanup.

## Evidence anchor

The design is pinned to the promoted read-only planning evidence:

- workflow run `29856203054`;
- repository commit `93fcdaf6c1d99f88f3ae8c34f86533a020e1a29a`;
- artifact `collector-replacement-plan-29856203054-1`;
- artifact SHA-256 `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`;
- Azure mutations authorized: `false`;
- Azure mutations performed: `false`.

The sanitized four-lens review remains `docs/reviews/collector-replacement-plan-2026-07-21.md`. The selected rollback decision is documented in `docs/reviews/collector-replacement-rollback-decision-2026-07-21.md`.

## Target boundary

| Item | Required value |
|---|---|
| Resource group | `rg-servicetracer-dev-westus2` |
| Region | `westus2` |
| Collector VM | `vm-stcollector-mst-dev` |
| Collector NIC | `nic-stcollector-mst-dev` |
| Evidence disk | `disk-stcollector-evidence-mst-dev` |
| Canonical OS disk | `disk-stcollector-os-mst-dev` |
| Evidence mount | `/var/lib/servicetracer` |
| Desired image | Canonical Ubuntu 24.04 |
| Future confirmation | `REPLACE:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev` |

A promoted implementation must refuse any target that does not exactly match the reviewed authorization package and current control-plane evidence.

## Authority model

The future execution path requires all of the following as separate evidence:

1. a reviewed implementation commit;
2. the promoted planner run and artifact digest;
3. a fresh guest and control-plane preflight package;
4. independently verified evidence-disk and OS-disk recovery points;
5. explicit NIC handling;
6. an approved identity/RBAC restoration allowlist;
7. a temporary-cost ceiling, cleanup owner, and deadline;
8. four independent review decisions;
9. protected-environment approval;
10. exact typed confirmation that has not expired.

A confirmation phrase is only one field in the authority package. It is never sufficient by itself.

## Ordered state machine

### 1. Validate authority

Validate the exact target, reviewed commit, planner evidence identity, approval owner, approval time, expiry, cost ceiling, cleanup owner, cleanup deadline, and confirmation phrase. Refuse stale or incomplete authorization.

### 2. Guest and control-plane preflight

Immediately before maintenance, capture:

- `systemctl is-active servicetracer-collector.service`;
- local `/healthz` success;
- `findmnt` evidence proving `/var/lib/servicetracer` is mounted from the managed evidence disk;
- filesystem UUID and block-device identity;
- recent evidence readability without printing evidence contents or credentials;
- current VM image, size, NIC, static address, subnet, OS disk, evidence disk, identity, and visible role assignments;
- current delete options and disk network-access policies;
- current OS-disk resource ID, size, OS type, Hyper-V generation, security type, Trusted Launch compatibility, encryption configuration, network access policy, and public network access state.

Azure VM Run Command is suitable for bounded guest checks, but its returned output must be sanitized and treated as operationally sensitive evidence.

### 3. Preserve delete options

Before deleting the VM, a future implementation must update and then re-read the VM resource so that:

- the evidence disk remains `Detach`;
- the NIC is changed from `Delete` to `Detach`;
- the old OS disk remains disposable only after its OS-disk snapshot is independently verified.

Microsoft documents changing VM delete behavior through the resource update path. The implementation must verify the resulting resource representation before continuing.

### 4. Create recovery points

Create exactly two bounded recovery snapshots:

1. an evidence-disk snapshot whose source identity matches `disk-stcollector-evidence-mst-dev`;
2. an OS-disk rollback snapshot whose name begins with `snap-stcollector-os-rollback-mst-dev-` and whose source identity matches `disk-stcollector-os-mst-dev`.

Both snapshots require restrictive network access, public network access disabled, and workload, execution, owner, and cleanup-deadline tags.

The total snapshot ceiling is 96 GiB. Because the evidence disk is 32 GiB, the design blocks if the current OS disk exceeds 64 GiB. The size must be freshly observed; the repository does not currently claim it as a runtime fact.

### 5. Independently verify recovery points

A separate verification step must prove for both snapshots:

- provisioning state is successful;
- source disk identity matches;
- size is expected;
- network access is restricted;
- cleanup deadline is present and no more than 24 hours away.

The OS-disk snapshot verification must additionally preserve OS type and Hyper-V generation and reconcile the Trusted Launch/security and encryption metadata required to recreate the prior bootable VM under the reviewed security profile.

Creation success alone is not recovery proof. Repository validation proves only that these requirements are present; it does not prove Azure recoverability.

### 6. Remove only old compute

The design prohibits overlapping old and replacement VM compute. After both recovery snapshots and delete-option changes are independently verified, remove only the old VM boundary. The NIC and evidence disk must survive. The disposable old OS disk may be deleted so that the canonical name becomes available.

### 7. Verify preservation boundary

Before any replacement deployment, re-read and compare:

- NIC resource ID, subnet, static private address, and security relationships;
- evidence-disk resource ID, size, attachment state, and access policy;
- both recovery-snapshot identities and states;
- absence of the old VM boundary;
- availability of the canonical OS-disk name `disk-stcollector-os-mst-dev`.

Any mismatch stops the workflow and enters rollback or human intervention.

### 8. Deploy replacement compute

Create the Ubuntu 24.04 collector using the preserved NIC and evidence disk. The source commit must be pinned. Cloud-init must preserve the existing filesystem and must not format the evidence disk. The replacement OS disk must use the canonical name `disk-stcollector-os-mst-dev`.

### 9. Harden the replacement OS disk

After the replacement OS disk exists, explicitly set:

- public network access: `Disabled`;
- network access policy: `DenyAll`.

The implementation must re-read the disk and prove both settings.

### 10. Restore identity and RBAC

A system-assigned identity receives a new principal ID. Capture the new principal, compare it with the old identity, and recreate only role assignments present in the approved allowlist. Do not infer permissions from architecture intent.

The current promoted plan returned no visible role assignments, so an empty restoration set is valid only if a fresh preflight independently confirms it.

### 11. Post-change verification

Reuse and extend `infra/scripts/verify_collector_deployment.sh` to prove:

- Ubuntu 24.04 and the reviewed ServiceTracer source commit;
- cloud-init completion without manual repair;
- the same evidence filesystem UUID is mounted at `/var/lib/servicetracer`;
- recent pre-change evidence remains readable;
- service and health endpoint are successful;
- an authenticated durable record can be written;
- restart persistence succeeds;
- NIC, address, disk, identity, RBAC, and OS-disk hardening match the approved contract.

### 12. Human recovery acceptance

Evidence-quality, operations/recovery, security/identity, and Azure-cost reviewers issue separate typed decisions. One lens cannot imply universal approval.

### 13. Cleanup temporary recovery resources

Cleanup requires a separate exact confirmation after recovery acceptance. It must occur before the approved deadline and produce deletion evidence. Budget and billing-alert resources remain out of scope and must not be modified.

## Cost policy

The repository contract currently sets these policy ceilings:

- currency: CAD;
- maximum declared temporary cost: CAD 10;
- maximum snapshots: 2;
- maximum snapshot capacity: 96 GiB;
- maximum OS-disk snapshot size: 64 GiB;
- maximum overlapping compute: 0 minutes;
- maximum recovery-resource retention: 24 hours.

These are governance ceilings, not price quotations. Promotion requires a current reviewed estimate. The implementation may create only named recovery resources and must not create or edit Azure budgets, action groups, cost alerts, or billing configuration.

## Selected rollback strategy

The selected strategy is `os_disk_snapshot_recreate_canonical_name`.

If replacement verification fails after old compute removal:

1. stop before cleanup and preserve the NIC, evidence disk, and both recovery snapshots;
2. remove only the failed replacement compute boundary and its disposable replacement OS disk;
3. recreate `disk-stcollector-os-mst-dev` from the independently verified OS-disk snapshot using managed-disk create option `Copy`;
4. recreate `vm-stcollector-mst-dev` under the recorded prior security profile with the preserved NIC and evidence disk;
5. record the new system-assigned principal and restore only the approved RBAC allowlist;
6. prove the prior OS boots, the same evidence filesystem UUID mounts at `/var/lib/servicetracer`, recent evidence is readable, service and health checks succeed, durable write and restart persistence succeed, and network/disk/identity state matches the rollback contract.

The evidence disk is never a disposable rollback component. It must not be deleted, formatted, replaced, or restored over.

This strategy was selected because it preserves the canonical IaC disk name and avoids a second naming migration. It remains operationally untested. Independent operations-and-recovery approval and an executable fake-Azure-CLI-tested recreation implementation are still required.

## Promotion gate

A later PR may promote an implementation into `.github/workflows/collector-replacement-execution.yml` only after:

- the selected rollback strategy receives independent operations-and-recovery approval and operational proof;
- a preflight evidence schema exists;
- recovery verification is independently testable;
- mutation commands are bounded and unit-tested with a fake Azure CLI;
- RBAC restoration uses an explicit allowlist;
- cost and cleanup inputs are validated;
- reviewers approve their separate scopes;
- repository state records execution as still unauthorized until a human explicitly authorizes one run.

## Primary references

- Azure VM delete behavior: `https://learn.microsoft.com/azure/virtual-machines/delete`
- Azure Linux Run Command: `https://learn.microsoft.com/azure/virtual-machines/linux/run-command`
- Azure snapshot CLI: `https://learn.microsoft.com/cli/azure/snapshot`
- Azure managed disk CLI: `https://learn.microsoft.com/cli/azure/disk`
- Azure VM ARM/Bicep reference: `https://learn.microsoft.com/azure/templates/microsoft.compute/2024-07-01/virtualmachines`
