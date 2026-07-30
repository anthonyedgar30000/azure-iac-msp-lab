# Lab Factory preflight run 1 handoff

## Objective

Advance the prepared `servicetracer-demo-api@1.0.0` request through one read-only Azure preflight and ARM What-If. This increment cannot deploy or delete Azure resources.

## Exact repository boundary

```text
base main: 0b6fa63d86ae52119b63ef6c9421c8d13215cb59
latest merged PR: #223
open PRs before branch: none observed
branch: agent/lab-factory-preflight-run1
local working tree: not observed / connector-backed
source instruction: Proceed
```

## Intended architecture and scope

```text
GitHub merge to main introducing the workflow
  -> exact-commit validation
  -> Azure OIDC login through azure-lab
  -> read-only context, provider, dependency, resource-group, DNS, SKU, quota, and price observations
  -> deterministic Lab Factory request preparation
  -> subscription-scope ARM validation
  -> FullResourcePayloads What-If
  -> fail-closed assessment
  -> protected evidence and SHA-256 manifest
```

```text
profile: servicetracer-demo-api@1.0.0
environment: test
location: westus2
resource group: rg-st-demo-api-test-westus2
VM size: Standard_F1als_v7
TTL planning horizon: 8 hours
accepted cost ceiling: CAD $5.00
```

## Dependencies and network paths

The preflight depends on the existing ServiceTracer transaction service. It reads the existing remote-access public IP to form the future backend URL and independently requires HTTP 200 from the existing public health endpoint.

The only planned outbound paths from the runner are:

- Azure Resource Manager and supported Azure CLI endpoints;
- Azure Retail Prices API for a CAD estimate;
- the existing ServiceTracer HTTPS health endpoint;
- GitHub/raw GitHub for exact-source checkout and immutable installer reference.

No inbound Azure path is created. The proposed future lab would have a dedicated Standard public IP and Internet-facing HTTP/HTTPS NSG rules; those are reviewable What-If changes, not deployed reality.

## Identity and permissions

The workflow uses the existing `azure-lab` GitHub OIDC identity. Required effective access is limited to reading subscription/provider/quota/resource state and executing ARM validation and What-If. The workflow contains no provider-registration, deployment-create, role-assignment, delete, rollback, or cleanup command.

```text
OIDC login authorized: true
Azure read-only observations authorized: true
ARM validation and What-If authorized: true
provider registration authorized: false
Azure resource change authorized: false
deployment authorized: false
RBAC change authorized: false
```

## Security controls

- one merge-triggered attempt only;
- no `workflow_dispatch` trigger;
- `GITHUB_RUN_ATTEMPT` must equal `1`;
- exact merge commit must be checked out;
- target resource group must be absent;
- DNS label must be available;
- unsupported SKU, quota, price, provider, dependency, template, or What-If state fails closed;
- an ephemeral SSH key is generated only for ARM validation and What-If, and the private key is removed before evidence upload;
- raw subscription ID, tenant ID, and dependency public IP are redacted from preserved ARM evidence;
- supplied Lab Factory parameter values are not returned in the prepared plan;
- evidence receives an SHA-256 manifest and 30-day protected artifact retention.

## Cost boundary

The accepted planning ceiling is **CAD $5.00**. The assessor uses the current CAD hourly retail price for `Standard_F1als_v7`, multiplied by eight hours, plus a conservative **CAD $1.50** allowance for the OS disk, Standard public IP, and incidental lab resources.

```text
retail estimate != invoice
preflight quota != reserved capacity
accepted ceiling != deployment spend authority
```

Actual cost remains unknown because the preflight creates nothing.

## Validation commands

Exact-head CI runs:

```bash
python -m unittest \
  infra.tests.test_lab_factory_lite \
  infra.tests.test_lab_factory_preflight_run1 \
  -v

python -m py_compile \
  scripts/assess_lab_factory_preflight.py \
  scripts/assert_lab_factory_preflight_what_if.py

bash -n scripts/lab_factory_preflight_run1.sh

az bicep lint --file workloads/servicetracer-demo-api/infra/main.bicep
az bicep build --file workloads/servicetracer-demo-api/infra/main.bicep
```

The live preflight additionally validates the template and runs:

```text
az deployment sub what-if
  --result-format FullResourcePayloads
```

## Expected outputs

A successful protected artifact includes redacted context and provider evidence, dependency health, the deterministic prepared plan, target group and DNS observations, SKU/quota/cost assessment, ARM validation, ARM What-If, a fail-closed What-If assessment, a terminal decision, and an SHA-256 manifest.

Success means only:

```text
preflight_passed = true
deployment_authorized = false
azure_mutation_performed = false
```

## Failure, rollback, and cleanup

Any failure consumes this one-attempt authority, writes the terminal stopping stage, and uploads available evidence. It does not authorize a GitHub rerun or a second preflight.

Repository rollback is an exact revert of the merged preflight increment. Azure rollback and cleanup are not applicable because no Azure mutation path exists in this workflow.

## Next gate

Review and reconcile the exact workflow artifact. A successful preflight may support a later deployment request, but deployment requires a new explicit instruction, one exact reviewed commit, validation behavior, failure handling, service checks, cost acceptance, and a separately reviewed cleanup procedure.
