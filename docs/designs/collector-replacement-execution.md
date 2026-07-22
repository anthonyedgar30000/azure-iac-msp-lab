# Collector replacement execution design

## State and authority

**Design-only, fail-closed, not deployed, not operationally tested, and not authorized for Azure execution.**

The candidate workflow remains outside `.github/workflows/`. Promotion requires a separate authority-changing pull request, protected-environment approval, explicit human authorization, and all required independent reviews.

## Target

- Resource group: `rg-servicetracer-dev-westus2`
- Region: `westus2`
- Collector VM: `vm-stcollector-mst-dev`
- Production NIC: `nic-stcollector-mst-dev`
- Evidence disk: `disk-stcollector-evidence-mst-dev`
- Canonical OS disk: `disk-stcollector-os-mst-dev`
- Evidence mount: `/var/lib/servicetracer`

The deployed Ubuntu 22.04 image line differs from the desired Ubuntu 24.04 image line. Replacement, rather than an ordinary in-place image update, remains required.

## Authority and cost gates

Before any future execution, all of the following must be current and approved:

- exact repository commit and target identity;
- unexpired human authorization using the separately governed confirmation mechanism;
- current guest and Azure control-plane preflight;
- subscription-specific pricing, SKU availability, and quota;
- cleanup owner and cleanup deadline;
- reviewed planning estimate of CAD 4;
- renewed approval above CAD 4;
- unconditional stop above CAD 10;
- maximum two snapshots and 96 GiB total;
- maximum isolated rehearsal compute of four hours;
- maximum temporary-resource retention of 24 hours;
- zero minutes of running-compute overlap.

## Exact quiesce and consistency boundary

Snapshot creation is prohibited until the source reaches the following exact ordered boundary:

1. stop accepting new collector writes;
2. drain in-flight collector writes;
3. flush pending evidence writes to the mounted evidence filesystem;
4. record the final evidence checkpoint identifier and SHA-256;
5. record the maintenance correlation identifier;
6. stop the collector service;
7. verify guest shutdown;
8. deallocate the source VM;
9. verify Azure `PowerState/deallocated`.

Membership is insufficient. Reordering is invalid because deallocation before write drain, flush, checkpoint, service stop, and guest shutdown could produce an unusable or internally inconsistent recovery point.

Both the OS-disk and evidence-disk snapshots must carry the same maintenance correlation, final checkpoint identifier, and checkpoint SHA-256.

## Recovery-point verification

Each snapshot must prove:

- successful provisioning;
- exact source resource identity;
- expected capacity and generation metadata;
- public network access disabled;
- network access policy `DenyAll`;
- shared maintenance-correlation and checkpoint binding;
- owner, execution, and cleanup-deadline tags;
- cleanup deadline no more than 24 hours after creation.

Metadata verification does not prove bootability or rollback.

## Isolated exact-snapshot rehearsal

Before old compute may be removed:

1. create a temporary managed OS disk from the exact verified OS snapshot using `Copy`;
2. create an isolated temporary VM by attaching that specialized disk using `Attach`;
3. apply the recorded source Trusted Launch profile;
4. attach neither the production NIC nor the production evidence disk;
5. keep the source VM deallocated;
6. prove prior OS boot, VM Guest State/vTPM viability, and bounded guest health;
7. capture rehearsal evidence.

The rehearsal is recovery evidence, not operational rollback proof.

## Mandatory rehearsal teardown transition

After rehearsal evidence is captured and before `deploy_replacement_compute`:

- deallocate the isolated rehearsal VM and record its final power state;
- remove the temporary rehearsal VM;
- remove the isolated temporary NIC and any other rehearsal-only compute boundary;
- verify that no rehearsal compute remains allocated;
- retain only explicitly approved recovery artifacts: the verified OS snapshot, verified evidence snapshot, and an approved temporary recovery disk when required;
- preserve zero minutes of running-compute overlap.

The final cleanup phase handles retained recovery artifacts after human acceptance. It must not be used to justify leaving rehearsal compute allocated during replacement deployment.

## Old-compute removal and preservation boundary

Old compute may be removed only after:

- exact ordered quiescence and Azure deallocation;
- both consistency-bound snapshots are verified;
- exact-snapshot Trusted Launch rehearsal succeeds;
- rehearsal compute teardown succeeds;
- the production NIC and evidence disk are confirmed preserved.

Deletion is VM-only. The production NIC and evidence disk must not be deleted.

## Replacement deployment

The replacement VM must:

- use Ubuntu 24.04;
- use the canonical OS-disk name;
- attach the preserved production NIC with `deleteOption: Detach`;
- attach the preserved evidence disk with `deleteOption: Detach`;
- re-read both attachment delete options after creation;
- disable public access on the OS disk and use network access policy `DenyAll`;
- receive a new system-assigned identity;
- receive only RBAC assignments from an approved allowlist.

## Post-change verification

A successful deployment is not a validated service. Acceptance requires evidence for:

- cloud-init completion;
- evidence filesystem UUID and mount path;
- recent evidence readability;
- collector service health;
- authenticated local health endpoint;
- durable write and restart persistence;
- expected network path and static private addressing;
- identity and approved RBAC;
- OS-disk access policy;
- re-read `Detach` semantics for the production NIC and evidence disk.

## Rollback strategy

Selected strategy: `os_disk_snapshot_recreate_canonical_name`.

If replacement validation fails after old-compute removal:

1. re-read production NIC and evidence-disk `Detach` semantics;
2. remove only failed replacement compute and its disposable OS disk;
3. recreate `disk-stcollector-os-mst-dev` from the exact verified OS snapshot using `Copy`;
4. validate SKU, OS type, Hyper-V generation, Trusted Launch profile, encryption/DES, zone, access policy, public-access state, and OS-disk delete option;
5. recreate `vm-stcollector-mst-dev` using `Attach` for the specialized OS disk;
6. attach the preserved NIC and evidence disk with `Detach`;
7. restore only approved RBAC to the new system-assigned principal;
8. repeat complete guest, service, durability, identity, network, and attachment verification.

The evidence disk is never deleted, formatted, replaced, restored over, or attached to the isolated rehearsal VM.

## Evidence and rollback behavior

Every mutation must capture command, exit code, timestamp, correlation ID, target resource IDs, before/after state, and cleanup ownership. Failures stop forward progress. The design does not permit infinite retries or automatic authority expansion.

## Current blockers

- fresh CI on the latest code-bearing remediation head;
- another operations-and-recovery review;
- fake-Azure-CLI-tested execution and recovery commands;
- guest and control-plane evidence schemas;
- identity/RBAC allowlist;
- fresh authenticated cost and quota preflight;
- cleanup ownership and deadline;
- evidence-quality and security/identity approval;
- protected-environment approval and explicit human authorization.
