# ServiceTracer Lab Factory read-only preflight run 1

## Purpose

This run proves whether the currently prepared `servicetracer-demo-api@1.0.0`
request is safe and supportable enough to reach a later deployment-authorization
gate.

```text
profile: servicetracer-demo-api@1.0.0
environment: dev
location: westus2
TTL: 8 hours
target resource group: rg-st-demo-api-dev-westus2
VM SKU: Standard_F1als_v7
planning ceiling: CAD 5.00
```

The run performs authenticated Azure reads, ARM template validation, and ARM
What-If. It cannot deploy, register a provider, assign a role, modify a resource,
run a VM command, call a model, expose MCP remotely, or clean anything up.

```text
preflight_passed != deployment_authorized
What-If_output != Azure_mutation
estimated_cost != actual_cost
```

## Architecture under review

The subscription-scope Bicep root proposes one dedicated resource group containing:

- a network security group allowing Internet TCP/80 and TCP/443;
- a `10.30.0.0/24` VNet and `10.30.0.0/27` subnet;
- a Standard Regional static IPv4 public IP with a DNS label;
- one NIC;
- one Ubuntu 24.04 LTS VM using `Standard_F1als_v7`;
- a system-assigned VM identity;
- one Custom Script extension.

No inbound SSH rule is declared. This is source review, not proof that those
resources exist or that the network and application are secure at runtime.

## One-attempt authority

The source authorization is:

```text
.project/observation-requests/servicetracer-lab-factory-preflight-run1.json
```

The exact execution commit is the merge commit that lands this implementation.
The runtime subscription UUID remains only in the Cloud Shell environment and is
never written to repository evidence.

The one-attempt marker is:

```text
~/.servicetracer-lab-factory-preflight-run1.consumed
```

It is created immediately before the first authenticated Azure observation. Any
failure after that point consumes the attempt. Do not delete the marker and do not
rerun the script without new human authorization.

## Preflight checks

The script records:

1. exact commit and clean working tree;
2. exact `Azure for Students` subscription and enabled state;
3. registration state for `Microsoft.Resources`, `Microsoft.Compute`,
   `Microsoft.Network`, and `Microsoft.ManagedIdentity`;
4. location and subscription restrictions for `Standard_F1als_v7` in `westus2`;
5. regional and VM-family vCPU quota;
6. exact target resource-group existence and bounded resource inventory;
7. CAD retail VM price context from the unauthenticated Azure Retail Prices API;
8. an optional month-to-date Cost Management query, preserving permission failure
   as `not_observed` rather than zero;
9. Bicep compilation;
10. subscription-scope ARM validation;
11. subscription-scope ARM What-If using `ResourceIdOnly` output;
12. a sanitized receipt and SHA-256 evidence manifest.

The planning estimate is deliberately conservative and incomplete:

```text
8 × observed CAD hourly VM retail rate
+ CAD 2.00 storage/network contingency
```

It must remain at or below CAD 5.00 to pass this planning gate. This estimate is
not an invoice, negotiated rate, Azure for Students credit projection, or actual
cost measurement.

## Runtime-only parameters

The preflight uses non-production placeholder application values because the gate
is evaluating Azure infrastructure shape, permissions, quota, conflicts, and
What-If—not service correctness. The exact source repository, reviewed commit,
and installer URI are pinned to the reviewed repository state. An ephemeral SSH
key is generated locally and destroyed on exit. Parameter values are not promoted
into evidence.

A future deployment request must separately supply and review production-appropriate
values for CORS origin, backend transaction URL, DNS label, and all other required
parameters.

## Execution after merge

Open Azure Cloud Shell **Bash**, update the repository, and check out the exact
merge commit reported for this pull request.

```bash
cd ~/azure-iac-msp-lab
git fetch origin
git checkout --detach '<exact-merge-commit>'

export AZURE_LAB_FACTORY_RUN1_SUBSCRIPTION_ID="$(az account show --query id --output tsv)"
export AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT='<exact-merge-commit>'
export AZURE_LAB_FACTORY_RUN1_CONFIRMATION="PREFLIGHT-SERVICETRACER-RUN1:Azure for Students:rg-st-demo-api-dev-westus2:westus2:8h:CAD5.00:${AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT}"

bash scripts/azure_lab_factory_servicetracer_preflight_run1.sh
```

Before execution, confirm that `az account show --query '{name:name,state:state}'`
returns `Azure for Students` and `Enabled`. Do not paste or screenshot the raw
subscription or tenant UUID.

## Evidence

The script writes:

```text
~/clouddrive/servicetracer-lab-factory-preflight-run1/evidence/
```

Important files include:

```text
preflight-summary.json
account-context.json
provider-states.json
vm-sku.json
quota-summary.json
target-resource-group.json
existing-resource-summary.json
retail-price-summary.json
cost-management-context.json
template-validation-summary.json
what-if-summary.json
artifact-manifest.sha256
```

No private SSH key, access token, API key, raw subscription UUID, raw tenant UUID,
or full ARM validation payload is retained.

## Result classification

```text
passed
```

All mandatory checks succeeded. This permits review only. Deployment authority is
still absent.

```text
blocked
```

The observations completed but at least one policy, provider, quota, conflict,
price, validation, or What-If gate failed. Do not deploy.

```text
observation_failed
```

One or more required observations could not be completed. Missing evidence is a
limitation, not proof that the condition is false.

## Failure and rollback

The script never has Azure mutation authority, so Azure rollback and cleanup do
not apply. Repository rollback is an exact revert of the implementing pull
request. A consumed or failed attempt requires new authorization before any new
Azure query or What-If.

## Next gate

After the evidence is reviewed and reconciled, a **new** explicit authority would
be required for deployment. That later authority must bind the exact template and
parameter digests, accepted What-If, cost ceiling, identity, subscription,
location, validation commands, failure behavior, and verified resource-group
cleanup plan.
