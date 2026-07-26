# Collector demo API backend convergence review

## Observed reality

Azure Cloud Shell was explicitly switched to the `Azure for Students` subscription. The resource group `rg-servicetracer-dev-westus2` was observed in `westus2` with provisioning state `Succeeded`.

The dedicated load balancer backend-address query returned no rows:

```bash
az network lb address-pool address list \
  --resource-group rg-servicetracer-dev-westus2 \
  --lb-name lb-st-demo-api-mst-dev \
  --pool-name be-st-demo-api \
  --output table
```

Therefore the pool exists but the expected `collector` address at `10.20.40.10` was not observed. The repository previously declared that address inline on the parent load-balancer resource.

```text
declared_inline_backend_address != backend_address_retained_by_Azure
resource_group_succeeded != workload_service_validated
```

## Repair

- Keep the dedicated load balancer, frontend, probe, rules, and an empty pool placeholder on the parent resource.
- Converge the exact `collector` IP through `Microsoft.Network/loadBalancers/backendAddressPools`.
- Set the virtual network at the backend-address level only.
- Make the VM extension depend on the backend-pool child resource.
- Require the public HTTP path to return the expected nginx `404` before invoking Certbot.
- Extend the What-If classifier and deterministic tests for the exact backend-pool child target and bounded `Modify` repair.

## Future validation sequence

A future separately authorized Azure attempt must capture:

1. ARM validation and FullResourcePayloads What-If.
2. Exact backend-address output showing one `collector` address at `10.20.40.10`.
3. Public HTTP reachability to the collector nginx configuration.
4. VM extension provisioning state.
5. Public HTTPS health and API contract.
6. ARM operations and post-deployment resource inventory.

## Authority boundary

This review and its branch authorize repository changes, pull-request creation, and ordinary CI only. They do not authorize Azure authentication, What-If, deployment, workflow dispatch, manual drift repair, pull-request merge, rollback, cleanup, or transaction replay.
