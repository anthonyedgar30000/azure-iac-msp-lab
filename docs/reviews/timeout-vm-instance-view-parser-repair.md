# Timeout deployment preflight parser repair

## Observed failure

Workflow run `30136642571`, attempt `3`, authenticated to Azure and captured the current VM instance view, then failed before ARM validation or deployment.

The workflow evaluated top-level `.statuses`. The captured Azure CLI document stored the VM power-state collection under `.instanceView.statuses`, including `PowerState/running`. `jq` therefore attempted to iterate over `null`.

```text
parser failure != VM stopped
preflight failed before What-If != Azure mutation
```

## Repair

The new deterministic parser accepts either Azure CLI status shape, requires an explicit `PowerState/running` value, and fails closed when status evidence is missing or malformed.

A sanitized fixture reproduces the observed nested structure, and regression tests cover:

- nested `.instanceView.statuses`;
- legacy top-level `.statuses`;
- missing status collections;
- the actual command-line exit contract;
- workflow inactivity until a fresh authorization marker exists.

## Execution boundary

The prepared workflow does not run from this repository change. The consumed deployment grant is not renewed. A later exact-commit authorization must be reviewed and added separately before Azure login, What-If, deployment, or rollback can occur.
