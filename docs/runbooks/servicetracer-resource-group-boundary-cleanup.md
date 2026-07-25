# ServiceTracer resource-group boundary cleanup

## Decision

The two Azure resource groups are peer operational boundaries, not nested layers:

```text
rg-servicetracer-dev-westus2
  core ServiceTracer lab platform

rg-st-demo-api-dev-westus2
  independent public demo API workload
```

The independent workload remains in its dedicated resource group. This cleanup does not merge resource groups or move resources.

## Why cleanup is needed

Historical deployment evidence records two separate partial-mutation families in the core resource group:

1. a failed Microsoft.Web demo deployment left `appi-demo-api-mst-dev` and `storfxczr3fewce`;
2. failed collector-hosted demo API attempts left `pip-st-demo-api-mst-dev` and the HTTP/HTTPS rules on `nsg-operations-mst-dev`.

The older collector-hosted strategy was superseded by the independently deployed VM-based API in `rg-st-demo-api-dev-westus2`.

```text
historical residue candidate != orphaned resource
name similarity != dependency
not_observed != absent
```

## Exact review candidates

- `appi-demo-api-mst-dev`
- `storfxczr3fewce`
- `pip-st-demo-api-mst-dev`
- `lb-st-demo-api-mst-dev`
- `nsg-operations-mst-dev/Allow-Demo-API-HTTP-From-Internet`
- `nsg-operations-mst-dev/Allow-Demo-API-HTTPS-From-Internet`
- `vm-stcollector-mst-dev/extensions/servicetracer-demo-api`

Only these exact resources may enter the cleanup assessment. Every resource in `rg-st-demo-api-dev-westus2` is protected.

## Current repository boundary

```text
base commit: 24b04906d0936af856eb03a68ab87b4c7a3d65c3
repository plan: implemented
Azure authentication: not performed
ARG query: not executed
cleanup: not authorized
IaC declaration removal: not authorized
```

The historical collector-hosted Bicep module remains unchanged until live dependency evidence is reviewed. This prevents an evidence-free deletion or declaration removal.

## Read-only collection method

After a separate exact authorization, run from authenticated Azure Cloud Shell Bash against the subscription containing both resource groups:

```bash
PINNED_COMMIT="<exact reviewed commit>"
SUBSCRIPTION_ID="<explicit subscription ID>"
WORKDIR="$HOME/clouddrive/servicetracer-cleanup-dependencies-$(date -u +%Y%m%dT%H%M%SZ)"

python3 scripts/servicetracer_resource_group_cleanup.py \
  --collect \
  --subscription-id "$SUBSCRIPTION_ID" \
  --source-commit "$PINNED_COMMIT" \
  --workdir "$WORKDIR"
```

The collector requires the Azure Resource Graph CLI extension to already exist. It does not install an extension or register a provider.

It writes sanitized evidence under:

```text
<workdir>/evidence/
```

## Evidence interpretation

A candidate can resolve to:

- `observed`;
- `not_observed`;
- `blocked`;
- `no_bounded_dependency_observed`;
- `requires_what_if_and_human_authorization`.

`no_bounded_dependency_observed` is deliberately weaker than `orphaned`.

Application Insights and Storage Account usage may exist outside ARG-visible relationships, including application configuration, guest configuration, scripts, or external consumers. They always require deployment-history and runtime review.

## Cleanup gate

After evidence review:

1. remove superseded declarations from IaC on a dedicated branch;
2. run Bicep build and tests;
3. execute ARM validation and What-If;
4. require an exact allowlist containing only reviewed deletions;
5. capture rollback evidence;
6. obtain separate destructive authorization;
7. delete through IaC rather than portal-only changes;
8. verify the core lab and independent API afterward.

Azure Backup and Recovery Services remain intentionally out of scope for Lab v1 and are unrelated to this cleanup.

No Azure move, update, delete, deployment, guest command, or cleanup is authorized by this package.
