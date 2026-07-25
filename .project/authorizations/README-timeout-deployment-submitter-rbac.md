# Timeout deployment submitter authorization boundary

This repository increment prepares two future operations but authorizes neither one.

## Gate 1: RBAC mutation

A separate explicit human grant is required before running:

```text
scripts/bootstrap_servicetracer_deployment_submitter_rbac.sh --principal-object-id <object-id> --apply
```

That grant may authorize only the custom role and assignment defined by:

```text
infra/rbac/servicetracer-demo-api-deployment-submitter-rbac.bicep
```

The role grants only `Microsoft.Resources/deployments/write` at `rg-st-demo-api-dev-westus2`. It does not renew the consumed workload deployment authorization.

## Gate 2: workload deployment

After RBAC deployment and propagation, a fresh OIDC session must capture effective permissions. Another separate exact-source grant is then required at:

```text
.project/authorizations/servicetracer-demo-api-timeout-fix-deployment-after-deployment-submitter-rbac-20260725.json
```

The prepared workflow requires that marker to bind one exact commit on `fix/timeout-deployment-submitter-rbac`, identify run `30178082566` as the consumed submission-permission failure, keep RBAC mutation and transaction replay unauthorized, and require effective permission reobservation before any deployment submission.

```text
repository repair merged != RBAC mutation authorized
RBAC mutation succeeded != workload deployment authorized
role assignment exists != effective permission observed
```
