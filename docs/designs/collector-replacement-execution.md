# Collector replacement execution design

## Status

**Design-only, fail-closed, and pending independent re-review.**

The candidate workflow remains at `infra/workflow-designs/collector-replacement-execution.yml`, outside `.github/workflows`. GitHub cannot dispatch it. It exits before Azure authentication and contains no Azure mutation commands.

The governing contract is `infra/replacement/collector-replacement-contract.json`. CI validates it with `infra/replacement/validate_execution_design.py` and `infra/tests/test_collector_replacement_execution_design.py`.

The selected strategy remains **OS-disk snapshot plus deterministic recreation under the canonical OS-disk name**. The first independent operations-and-recovery review requested four changes. This revision encodes those changes as contract invariants and tests; it does not claim independent approval or operational proof.

No `REPLACE:` phrase, Azure login, snapshot, deallocation, delete-option change, VM deletion, resource creation, role assignment, or cleanup is authorized by this design.

## Evidence anchor

- Planner run: `29856203054`
- Repository commit: `93fcdaf6c1d99f88f3ae8c34f86533a020e1a29a`
- Artifact: `collector-replacement-plan-29856203054-1`
- Artifact SHA-256: `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`
- Planner Azure mutations authorized: `false`
- Planner Azure mutations performed: `false`

The artifact is control-plane evidence. It does not prove current guest health, snapshot consistency, Trusted Launch bootability, rollback, or current subscription pricing.

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

A future implementation must refuse any target that does not exactly match the reviewed authorization package and fresh Azure evidence.

## Authority and cost boundary

A future execution requires a reviewed implementation commit, promoted planner evidence, fresh guest/control-plane evidence, recovery proof, explicit NIC handling, an RBAC allowlist, independent review decisions, protected-environment approval, and an unexpired exact confirmation.

The cost lens is conditionally approved for planning only:

- reviewed planning estimate: CAD 4;
- renewed approval required above CAD 4;
- unconditional stop above CAD 10;
- maximum two snapshots and 96 GiB total;
- maximum isolated rehearsal compute: four hours;
- maximum recovery-resource retention: 24 hours;
- old and rehearsal or replacement compute overlap: zero minutes.

A real run still requires authenticated subscription-specific meter pricing, SKU availability, quota, cleanup owner, and cleanup deadline. The estimate is not actual spend or Azure execution authority.

## Ordered state machine

### 1. Validate authority

Validate the exact target, reviewed commit, planner evidence, approval owner and expiry, cost controls, cleanup ownership, deadline, and confirmation phrase. Refuse stale or incomplete authorization.

### 2. Guest and control-plane preflight

Capture service and `/healthz` state, evidence mount and UUID, recent evidence readability, VM/NIC/disk configuration, identity and visible RBAC, and all OS-disk recreation metadata:

- resource ID and size;
- SKU and OS type;
- Hyper-V generation;
- Trusted Launch/security profile;
- encryption and Disk Encryption Set when present;
- availability zone when present;
- network and public-access policies;
- OS-disk delete option.

Also obtain fresh subscription-specific pricing, SKU availability, quota, cleanup owner, and cleanup deadline evidence.

### 3. Preserve source delete options

Before maintenance, update and re-read the source VM representation so that:

- production NIC: `deleteOption: Detach`;
- production evidence disk: `deleteOption: Detach`;
- OS disk remains disposable only after the exact-snapshot rehearsal succeeds.

### 4. Quiesce and deallocate the source

Before either snapshot:

1. stop accepting new collector writes;
2. drain in-flight writes;
3. flush pending evidence writes to the mounted evidence filesystem;
4. record a final evidence checkpoint identifier and SHA-256;
5. record a maintenance correlation identifier;
6. stop the collector service;
7. verify guest shutdown;
8. deallocate the source VM;
9. verify Azure `PowerState/deallocated`.

Snapshot capture before this boundary is prohibited.

### 5. Create consistency-bound recovery points

Create exactly two snapshots only after deallocation:

1. evidence-disk snapshot sourced from `disk-stcollector-evidence-mst-dev`;
2. OS-disk snapshot named with prefix `snap-stcollector-os-rollback-mst-dev-` and sourced from `disk-stcollector-os-mst-dev`.

Both snapshots must carry the same:

- maintenance correlation ID;
- final evidence checkpoint ID;
- final evidence checkpoint SHA-256.

Both require restrictive network access, public access disabled, owner/execution/deadline tags, and no more than 24 hours retention. Stop if the OS disk exceeds 64 GiB or total snapshot capacity would exceed 96 GiB.

### 6. Verify recovery points

Independently verify source identity, size, provisioning state, generation, OS type, access policies, shared consistency binding, ownership, and cleanup deadline. Snapshot creation success is not boot proof.

### 7. Isolated exact-snapshot Trusted Launch rehearsal

Before deleting old compute:

1. create a temporary managed OS disk from the **exact verified OS snapshot** using `Copy`;
2. create a temporary isolated VM using the recorded Trusted Launch profile;
3. attach the specialized temporary OS disk using `Attach`;
4. use only a temporary isolated NIC;
5. do not attach the production NIC;
6. do not attach the production evidence disk;
7. keep the source VM deallocated;
8. prove OS boot, VM Guest State/vTPM viability, and bounded guest health;
9. clean up within the reviewed cost and 24-hour deadline.

This rehearsal proves the exact snapshot can boot under the recorded security profile. It does not prove the full production rollback because the production NIC, evidence disk, identity, RBAC, and service path remain excluded.

### 8. Remove only old compute

Remove old compute only after:

- both consistency-bound snapshots pass verification;
- the exact OS snapshot passes the isolated Trusted Launch rehearsal;
- production NIC and evidence disk remain `Detach`;
- all cost and cleanup gates remain valid.

Remove only the old VM boundary and disposable old OS disk. Preserve the production NIC and evidence disk.

### 9. Verify preservation boundary

Re-read and compare the production NIC, static IP, subnet, security relationships, evidence-disk identity and policy, both snapshots, rehearsal evidence, old-VM absence, and canonical OS-disk-name availability.

### 10. Deploy replacement compute

Create Ubuntu 24.04 with a pinned source commit, the canonical OS-disk name, production NIC, and existing evidence disk. Cloud-init must not format or replace the evidence filesystem.

The replacement VM contract requires:

- production NIC: `deleteOption: Detach`;
- production evidence disk: `deleteOption: Detach`;
- both settings re-read after creation;
- both settings re-read before any failed-replacement deletion.

### 11. Harden the replacement OS disk

Set and re-read:

- public network access: `Disabled`;
- network access policy: `DenyAll`.

### 12. Restore identity and RBAC

Capture the new system-assigned principal and recreate only the approved RBAC allowlist. Do not infer permissions from architectural intent.

### 13. Post-change verification

Prove Ubuntu 24.04, pinned source, cloud-init without manual repair, the same evidence UUID, readable pre-change evidence, service and health, durable write, restart persistence, identity/RBAC, network state, disk hardening, and re-read `Detach` semantics.

### 14. Human recovery acceptance

Evidence-quality, operations/recovery, security/identity, and Azure-cost reviewers issue separate decisions. No single decision implies universal approval.

### 15. Cleanup temporary recovery resources

Cleanup requires separate exact confirmation, deletion evidence before the deadline, and actual temporary-cost evidence. Budget and billing-alert resources remain out of scope.

## Deterministic rollback semantics

If replacement verification fails after old-compute removal:

1. stop before cleanup and preserve both snapshots, the production NIC, and evidence disk;
2. re-read NIC and evidence-disk `Detach` semantics;
3. remove only failed replacement compute and its disposable OS disk;
4. create `disk-stcollector-os-mst-dev` from the exact verified snapshot using managed-disk create option `Copy`;
5. validate SKU, OS type, Hyper-V generation, Trusted Launch/security profile, encryption/DES, zone when present, network policy, public-access state, and OS-disk delete option;
6. recreate `vm-stcollector-mst-dev` by attaching the specialized OS disk using VM OS-disk create option `Attach`;
7. attach the production NIC and evidence disk with `deleteOption: Detach`;
8. re-read both attachment settings after creation and before any later failed-compute deletion;
9. restore only approved RBAC to the new principal;
10. verify boot, evidence UUID and readability, service, health, durable write, restart persistence, identity, RBAC, network, and disk policies.

`FromImage` is prohibited for snapshot restoration. Missing `Attach`, metadata drift, or `Delete` on either preserved production attachment is a hard failure.

The production evidence disk must never be deleted, formatted, replaced, restored over, or attached to the isolated rehearsal VM.

## Promotion gate

A later PR may promote an implementation into `.github/workflows/collector-replacement-execution.yml` only after:

- independent re-review approves this remediation;
- guest/control-plane evidence schemas exist;
- recovery and rehearsal commands are fake-Azure-CLI tested;
- identity/RBAC restoration uses an explicit allowlist;
- subscription-specific cost and quota checks are implemented;
- cleanup owner/deadline controls are implemented;
- all independent lenses approve their scopes;
- execution remains unauthorized until a separate human-authorized run.

## Primary references

- Azure VM delete behavior: `https://learn.microsoft.com/azure/virtual-machines/delete`
- Azure Linux Run Command: `https://learn.microsoft.com/azure/virtual-machines/linux/run-command`
- Azure snapshot CLI: `https://learn.microsoft.com/cli/azure/snapshot`
- Azure managed disk CLI: `https://learn.microsoft.com/cli/azure/disk`
- Azure VM ARM/Bicep reference: `https://learn.microsoft.com/azure/templates/microsoft.compute/2024-07-01/virtualmachines`
