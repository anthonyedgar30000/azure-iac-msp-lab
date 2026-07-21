# Collector replacement plan evidence review

## Evidence identity

- Workflow: **Collector replacement plan**
- Run ID: `29856203054`
- Repository commit: `93fcdaf6c1d99f88f3ae8c34f86533a020e1a29a`
- Artifact: `collector-replacement-plan-29856203054-1`
- Artifact SHA-256: `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`
- Observed on: `2026-07-21`
- Result: successful read-only plan
- Azure mutations authorized: **false**
- Azure mutations performed: **false**

The raw artifact contains sensitive environment identifiers and is intentionally not committed to the repository. This document preserves only the bounded findings needed for current-state retrieval and future review.

## Verified control-plane findings

- The current collector VM exists and is provisioned successfully.
- Current VM size: `Standard_B2ats_v2`.
- Current image line: Canonical Ubuntu 22.04 Jammy.
- Desired image line: Canonical Ubuntu 24.04.
- The image-line difference is immutable for the existing VM and requires replacement rather than an ordinary in-place deployment.
- The evidence disk is a 32 GiB Standard SSD, is currently attached, uses `deleteOption: Detach`, disables public network access, and uses `DenyAll` network access policy.
- The collector NIC uses static private addressing on the operations subnet and is currently configured with VM `deleteOption: Delete`.
- The collector uses a system-assigned managed identity.
- No visible role assignments were returned for the current collector principal.
- The current disposable OS disk allows public network access and uses `AllowAll` network access policy.
- The workflow uploaded its planning evidence and statically checked that the workflow and planner script contain no supported Azure mutation commands.

## Review lenses

### Evidence quality

**Decision: accepted for bounded control-plane inventory.**

The run is correlated to a repository commit, run ID, artifact name, and artifact digest. It proves the observed Azure control-plane configuration and the absence of authorized or performed Azure mutations.

It does not prove guest service health, the currently running ServiceTracer version, filesystem mount state, evidence readability, backup recoverability, or post-replacement behavior.

### Operations and recovery

**Decision: replacement authorization withheld.**

Required before execution:

1. Verify the collector service and health endpoint immediately before maintenance.
2. Verify that the evidence filesystem is mounted from the managed evidence disk and that recent evidence is readable.
3. Record filesystem identity and mount configuration.
4. Create and independently verify an evidence-disk recovery point.
5. Explicitly preserve the NIC or define and test deterministic recreation of its subnet, static addressing, and security relationships.
6. Define rollback criteria and post-change evidence checks.

### Security and identity

**Decision: conditional design acceptance only.**

- A replacement VM will receive a new system-assigned principal identity.
- Required report-publication permissions must be explicitly recreated and verified.
- The replacement OS disk should disable public network access unless an approved requirement and compensating controls are documented.
- Raw workflow artifacts must remain protected because they include environment identifiers and other operationally sensitive metadata.

### Azure cost

**Decision: no cost change from this run; future temporary cost must be bounded.**

The planning run created no Azure resources and modified no budgets, alerts, or billing configuration.

A future replacement design must declare:

- temporary snapshot or backup cost;
- any overlap period for old and replacement compute or disks;
- a maximum temporary-cost ceiling;
- cleanup ownership and deadline;
- evidence that temporary resources were deleted after recovery acceptance.

## Governed outcome

| Question | Decision |
|---|---|
| Is immutable image drift verified? | Yes |
| Is the read-only planner accepted? | Yes |
| Did this run mutate Azure? | No |
| Is the evidence disk ready to be discarded? | No |
| Is replacement execution authorized? | No |
| May an execution workflow be designed and tested in Git? | Yes, without dispatching it |
| What unlocks execution? | Verified guest preflight, verified recovery point, NIC handling, identity/RBAC restoration, cost controls, rollback, independent review, and explicit human authorization |

The generated future `REPLACE:` phrase remains reference data only. Its existence is not authorization to execute replacement.
