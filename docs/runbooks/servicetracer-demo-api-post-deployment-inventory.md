# ServiceTracer demo API post-deployment inventory

## Purpose

Promote the authenticated Azure control-plane inventory captured for the independently deployed ServiceTracer demo API and provide a corrected, scoped read-only follow-up for the three incomplete observations:

- RBAC assignments;
- month-to-date cost;
- Azure Recovery Services backup metadata.

The original inventory evidence remains immutable. The follow-up does not repeat the full deployment inventory and does not change Azure.

## Canonical boundaries

```text
resource_exists != securely_configured
RBAC_assignment != effective_least_privilege
monitoring_object_exists != alert_delivery_verified
backup_item_observed != recovery_tested
month_to_date_cost != invoice
not_observed != absent
```

## Corrected follow-up

The operator capture completed at `2026-07-24T16:40:36Z` exposed three collector defects:

1. the scoped RBAC query combined `--scope` with `--all`;
2. the Cost Management query grouped by unsupported `Currency`;
3. backup discovery depended on an already-installed Resource Graph extension.

The repository follow-up corrects them by:

1. using `--scope` and `--include-inherited` without `--all`;
2. grouping cost by `ResourceId` only;
3. enumerating existing Recovery Services vaults and Azure IaaS VM protected items without installing an extension.

The correction does not retroactively alter the original evidence. Execution requires separate authorization.

## Execution

After separate authorization, run from authenticated Azure Cloud Shell Bash:

```bash
python3 scripts/servicetracer_demo_api_readonly_follow_up.py
```

Optional output location:

```bash
python3 scripts/servicetracer_demo_api_readonly_follow_up.py \
  --workdir "$HOME/clouddrive/servicetracer-readonly-follow-up-$(date -u +%Y%m%dT%H%M%SZ)"
```

The script writes sanitized JSON under:

```text
<workdir>/evidence/
```

Review the evidence before sharing it. Do not share access tokens or shell history containing raw identifiers.

## Mutation boundary

The script does not contain Azure resource create, update, delete, deployment, provider-registration, role-assignment mutation, VM run-command, guest command, transaction replay, or cleanup operations.

Azure CLI uses an HTTP `POST` to query Cost Management data. That request queries usage data and is not an Azure resource mutation.

## Failure behavior

Observation failures are written as typed evidence and do not become absence claims.

```text
query_failed != resource_absent
empty_vault_result != every_backup_method_absent
backup_item_observed != recovery_tested
```

No Azure rollback is required because the follow-up is read-only.
