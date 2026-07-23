# Collector demo API deploy run 30050103888

## Evidence identity

- Workflow: `Collector-hosted demo API`
- Operation: `deploy`
- Run: `30050103888`, attempt `1`
- Reviewed commit: `0465a525d2fd5c02b3ce0c41202f7a42c8678850`
- Resource group: `rg-servicetracer-dev-westus2`
- Region: `westus2`
- Artifact: `collector-demo-api-30050103888-1`
- Artifact ID: `8580705301`
- Artifact digest: `sha256:178af7ce60202663ac1d60db31a901dcdcb1641a8dbffc656e8068f91fa2b760`
- Evidence manifest generated: `2026-07-23T22:32:15Z`

The artifact hash manifest validates the captured pre-deployment inventory, readiness, ARM validation, What-If, request authority, and empty deployment-result file. The workflow did not capture post-failure target inventory or deployment-operation detail; the repair adds that evidence path for later runs.

## Proven sequence

```text
bounded deploy request validated
→ repository tests passed
→ Azure OIDC login passed
→ collector and dependency inventory captured
→ readiness passed
→ ARM validation passed
→ isolated What-If accepted
→ deployment authorized and attempted
→ Network resource writes failed
→ service verification skipped
→ evidence artifact uploaded
```

The accepted What-If contained nine Create changes and no classified collector VM, collector NIC, or protected base-infrastructure modification. Before the deploy attempt, the dedicated public IP was not present, Public IP usage was `1/3`, and no readiness blocker was recorded.

## Deployment failure

The parent deployment `collector-demo-api-dev` reached the nested deployment `collector-demo-api-resources-dev`, but Azure Network rejected the resource shape.

Observed errors:

- `OperationNotSupported`: standalone `PUT` was not supported for the new frontend IP configuration on the existing `lb-remote-access-mst-dev` load balancer;
- `OperationNotSupported`: standalone `PUT` was not supported for the new TCP/80 probe on the existing load balancer;
- `IpBasedLbShouldHaveVnetPropertyEitherOnPoolOrBackendAddressLevel`: the IP-based backend pool set the virtual network at both pool and backend-address level;
- parent and nested deployments ended in `DeploymentFailed` / `ResourceDeploymentFailure`.

The workflow wrote an empty `deployment-result.json`, and TLS, health, transaction, CORS, and browser verification did not run.

## Reality boundaries

```text
ARM_validation_passed != Network_resource_provider_execution_succeeded
WhatIf_accepted != resource_shape_supported_at_runtime
deployment_attempted != deployment_succeeded
deployment_failed != zero_partial_mutation
empty_deployment_result != empty_Azure_change_set
service_verification_skipped != service_failed
```

The artifact proves the public IP was absent before deployment, not after deployment. It does not prove whether the public IP, NSG rules, old load-balancer child resources, or VM extension were partially created. No cleanup is authorized by this record.

## Bounded repair strategy

Replace modifications to the existing remote-access load balancer with a dedicated Standard Load Balancer:

```text
pip-st-demo-api-mst-dev
→ lb-st-demo-api-mst-dev
→ IP-based pool be-st-demo-api
→ collector private IP 10.20.40.10
```

The dedicated load balancer owns its frontend, backend pool, TCP/80 probe, and HTTP/HTTPS rules in one parent resource deployment. The backend address carries the virtual-network reference exactly once. The existing remote-access load balancer remains an observed dependency used only to resolve the synthetic transaction endpoint; it is not a deployment target.

Future readiness must:

- inventory any legacy demo child resources under `lb-remote-access-mst-dev` and fail closed if they exist;
- inventory reusable partial target resources such as the dedicated public IP or NSG rules;
- capture parent and nested deployment operations after every deploy attempt, including failures;
- capture post-deploy public IP, dedicated load balancer, NSG rules, VM extension, and legacy child-resource state.

## Cost and authority

A dedicated Standard Load Balancer adds a separate recurring load-balancer and data-processing cost beyond the existing public IP and VM costs. Exact West US 2 CAD pricing, actual Azure for Students credit, and current meter usage were not captured and must be refreshed before a new deployment decision.

This review authorizes no workflow dispatch, Azure authentication, deployment, retry, cleanup, rollback, guest command, or endpoint promotion. The next operational step after repository repair is a fresh exact-commit read-only What-If and a separate human deployment gate.
