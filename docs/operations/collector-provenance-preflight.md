# Collector provenance preflight

## Purpose

Provide one exact-source, read-only Azure preflight for the collector-hosted provenance runtime before any deployment authority is considered.

```text
preflight_succeeded != deployment_authorized
WhatIf_accepted != Azure_mutation_performed
month_to_date_cost != remaining_credit
not_observed != zero_cost
```

## Intended architecture

The workflow runs from GitHub Actions with workload identity federation and evaluates the existing collector-hosted demo API in place. It does not create an alternate workload, public endpoint, or control plane.

The evaluated path is:

```text
GitHub Actions runner
  -> Azure Resource Manager control plane
  -> rg-servicetracer-dev-westus2
  -> existing vm-stcollector-mst-dev and collector demo API ingress
```

The future runtime path remains:

```text
GitHub Pages
  -> st-demo-api-aeg30000.westus2.cloudapp.azure.com
  -> dedicated Standard Load Balancer
  -> vm-stcollector-mst-dev
  -> loopback ServiceTracer demo API
```

## Region and resource scope

- Subscription: Azure for Students, resolved at runtime.
- Resource group: `rg-servicetracer-dev-westus2`.
- Region: `westus2`.
- Environment: `dev`.
- Existing collector VM: `vm-stcollector-mst-dev`.
- Existing collector private IP: `10.20.40.10`.
- Existing public DNS label: `st-demo-api-aeg30000`.
- New Azure resources: none.
- Azure mutations: none.

## Dependencies

- GitHub environment `azure-lab`.
- OIDC secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID`.
- Existing collector, NIC, operations NSG, remote-access load balancer, public IP, and collector module deployment.
- Existing `infra/collector-demo-api.bicep`.
- Existing readiness and What-If classifiers.
- Cost Management query access is optional evidence: failure is recorded as `not_observed` and does not become a false zero-cost claim.

## Identity and permissions

The workflow requires:

- GitHub `contents: read`;
- GitHub `id-token: write`;
- Azure read access for subscription, resource-group, VM, network, deployment, lock, quota, and budget observations;
- Azure deployment validation and What-If permission;
- Cost Management query permission when available.

It does not authorize:

- ARM deployment creation;
- VM extension writes;
- network mutations;
- RBAC mutation;
- browser transactions;
- retry, rollback, or cleanup.

Subscription and tenant identifiers are persisted only as SHA-256 fingerprints in the explicit context summary. Azure resource evidence can still contain normal ARM resource IDs inside the protected workflow artifact.

## Security controls

- Exact 40-character reviewed commit binding.
- Exact typed confirmation:
  `COLLECTOR-PROVENANCE-PREFLIGHT:<resource-group>:<dns-label>`.
- No operation selector and no deploy code path.
- Repository tests run before Azure login.
- Azure mutations and deployment authority are explicitly recorded as false.
- Evidence is uploaded to a scoped artifact with SHA-256 manifest entries.
- No credentials, tokens, raw OIDC assertions, or managed-identity tokens are persisted.
- Missing Cost Management or budget access remains visible as a limitation.

## Cost and quota evidence

The workflow captures:

- network usage and public-IP quota;
- regional compute usage;
- resource-group locks;
- resource-group budgets when observable;
- subscription month-to-date `PreTaxCost`;
- resource-group month-to-date `PreTaxCost`;
- returned billing currency.

Azure for Students remaining sponsorship credit is a separate billing fact. The workflow records it as not observed unless it is captured through a separately supported sponsorship or billing scope.

## Execution method

After this increment is merged:

1. Select the exact green pull-request source head as `reviewed_commit`.
2. Dispatch `Collector provenance preflight` from the default branch.
3. Use:
   - environment: `dev`
   - resource group: `rg-servicetracer-dev-westus2`
   - location: `westus2`
   - prefix: `mst`
   - DNS label: `st-demo-api-aeg30000`
   - allowed origin: `https://anthonyedgar30000.github.io`
4. Enter the exact confirmation string.
5. Review the artifact before requesting any deployment authority.

## Validation commands

Repository validation:

```bash
python -m unittest \
  infra.tests.test_collector_demo_api \
  infra.tests.test_frontend_azure_provenance_monitor \
  infra.tests.test_collector_provenance_preflight \
  -v
```

The workflow also executes:

```text
az deployment group validate
az deployment group what-if --result-format FullResourcePayloads
python infra/scripts/assert_collector_demo_api_what_if.py
```

## Expected outputs

The evidence artifact is expected to include:

- bounded request and authority record;
- sanitized Azure context and identity fingerprints;
- resource-group and resource inventory;
- collector VM, NIC, NSG, load-balancer, public-IP, extension, and module-deployment evidence;
- network and compute quota evidence;
- locks and budget observation;
- subscription and resource-group cost observations;
- remaining-credit limitation record;
- readiness assessment;
- ARM validation and FullResourcePayloads What-If;
- deterministic What-If assessment;
- preflight decision record;
- SHA-256 evidence manifest.

## Failure behaviour

- Invalid commit, scope, or confirmation fails before Azure login.
- Missing or contradictory Azure state fails closed.
- Readiness blockers fail the workflow before any deployment.
- Rejected What-If fails the workflow.
- Cost or budget query failure is preserved as `not_observed`; it does not fabricate zero cost or no budget.
- Evidence manifest and artifact upload run even after failure.
- No automatic retry occurs.

## Rollback and cleanup

No Azure rollback is required because the workflow is read-only and performs no mutation.

Repository rollback is to close the pull request or revert the workflow, summarizer, tests, and plan record.

Workflow artifacts retain for 30 days and then expire. No Azure resource cleanup is created or authorized by this increment.

## Evidence to capture

- Exact PR source head and exact-head CI run.
- Source-versus-merge file-content comparison after any merge.
- Workflow run ID, job ID, artifact ID, artifact digest, and manifest verification count.
- Azure context fingerprints, resource scope, region, quota, lock, cost, readiness, and What-If outputs.
- Explicit statement that deployment authority remains false.
