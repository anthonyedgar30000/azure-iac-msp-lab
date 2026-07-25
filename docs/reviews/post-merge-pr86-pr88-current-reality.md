# Post-merge PR #86 and PR #88 current-reality reconciliation

## Decision

Refresh the canonical repository watermark after PRs #86 and #88 merged, while preserving the latest Azure evidence as time-bounded and resolving the RBAC execution records without collapsing conflicting claims.

```text
main = 726c42ea1dddf402a42d8d0c591c660ebc50733f
latest merged PR = 88
open PRs observed = none
PR #86 exact-head CI = success
PR #88 exact-head CI = success
final combined-main CI = not_observed
```

`not_observed` is not a failed CI result.

## RBAC resolution

The repository now contains four materially different source claims:

1. PR #86 says an operator ran `--apply` and asked the project to assume success.
2. The bootstrap reconciliation says execution was false.
3. The authorization record remains `authorized_not_consumed`.
4. The verify-only execution record treats success as an assumption pending evidence.

The canonical resolution is:

```text
execution truth = conflicting
apply attempt asserted = true
apply success = assumed_not_evidenced
role definition observed = false
role assignment observed = false
effective extension-write permission = unverified
protected verify-only outcome = not_observed
deployment authorized = false
```

This preserves every source claim. It does not turn missing evidence into failure or an asserted attempt into successful Azure state.

## Cleanup resolution

PR #88 merged the resource-group ownership boundary and collector package:

```text
rg-servicetracer-dev-westus2 = core platform
rg-st-demo-api-dev-westus2 = independent public demo API
relationship = peer operational boundaries
```

The independent workload is protected. The seven candidates remain review candidates only.

```text
collector implemented != collector executed
candidate observed != orphaned
not_freshly_observed != absent
cleanup planned != cleanup authorized
```

## Azure evidence

No Azure authentication, Resource Graph query, role mutation, deployment, guest command, transaction replay, resource move, update, or deletion was performed by this reconciliation.

The latest durable Azure observation remains `2026-07-25T00:47:40Z`. It continues to establish the original VM deployment and public health at that time, not current health at the instant this document is read.

## Backup scope

Azure Backup and Recovery Services are intentionally out of scope for Lab v1. The prior zero-vault observation remains preserved as evidence, but it is not an unresolved requirement.

## Validation

The reconciliation includes deterministic validation and tests for:

- the exact GitHub watermark and exact-head CI anchors;
- source-versus-merge boundaries;
- the time-bounded Azure deployment evidence;
- conflicting RBAC claims;
- unverified role and effective-permission state;
- cleanup protection and non-execution;
- backup scope;
- historical PR #82 and PR #84 anchors;
- absence of execution authority.

## Authority and rollback

```text
Azure authentication = false
Azure mutation = false
Azure RBAC mutation = false
Resource Graph execution = false
deployment = false
cleanup = false
PR merge = false
```

Repository rollback is to close or revert this PR. No Azure rollback is required.

## Next gate

A later operation must choose and separately authorize exactly one read-only observation:

- protected verification of effective extension-write permission; or
- Resource Graph dependency collection for the cleanup candidates.
