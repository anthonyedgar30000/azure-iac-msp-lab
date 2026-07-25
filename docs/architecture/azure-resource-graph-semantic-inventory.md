# Azure Resource Graph semantic inventory adapter

## Decision

Use Azure Resource Graph (ARG) as the broad control-plane inventory source for the zoomable infrastructure universe.

This adapter is not the entire operational truth system. It produces a deterministic node-and-edge baseline that later enrichers can join with ARM provider detail, Network Watcher, Azure Monitor, Resource Health, policy, RBAC, cost, quota, and deployment evidence.

```text
Azure Resource Graph observations
→ bounded named KQL result sets
→ deterministic normalizer
→ infrastructure graph v1
→ semantic zoom and evidence reconciliation
```

## Current authority boundary

This increment implements repository code, queries, fixtures, tests, and CI only.

```text
adapter implemented = true
Azure authentication performed = false
ARG query executed = false
Azure resources mutated = false
MCP endpoint deployed = false
OpenAI API called = false
```

A later query run requires a separate authorization bound to explicit subscription IDs, an exact reviewed commit, expected query files, evidence output handling, and a no-mutation guarantee.

## Why ARG is the first layer

ARG can query Azure Resource Manager inventory at subscription or management-group scale and exposes KQL joins and projections suitable for resources, VMs, NICs, public IPs, VNets, and subnets. The REST resources operation is:

```text
POST https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2024-04-01
```

The Azure CLI `az graph query` command is provided by the Resource Graph extension and supports explicit subscription scoping. Shared-query creation is not required by this design.

Official references:

- Azure Resource Graph REST resources operation: https://learn.microsoft.com/en-us/rest/api/azureresourcegraph/resourcegraph/resources/resources?view=rest-azureresourcegraph-resourcegraph-2024-04-01
- Azure CLI `az graph query`: https://learn.microsoft.com/en-us/cli/azure/graph?view=azure-cli-latest
- Azure networking Resource Graph examples: https://learn.microsoft.com/en-us/azure/networking/resource-graph-samples
- Azure VM, NIC, and public-IP join example: https://learn.microsoft.com/en-us/azure/virtual-machines/resource-graph-samples

## Query package

The adapter intentionally uses several narrow queries rather than exporting every dynamic `properties` object.

| Query | Purpose |
|---|---|
| `resources.kql` | Generic resource nodes and hierarchy metadata |
| `vm-attachments.kql` | VM-to-NIC and VM-to-managed-disk relationships |
| `nic-ip-configurations.kql` | NIC IP configurations, private IPs, subnets, public IPs, NSGs, and backend pools |
| `subnets.kql` | VNet-to-subnet relationships, prefixes, subnet NSGs, and route tables |

Narrow projections reduce accidental protected-data capture and make changes to the evidence contract reviewable.

## Normalized model

The normalizer emits:

```json
{
  "schema_version": "servicetracer.infrastructure-graph.v1",
  "source_system": "azure_resource_graph",
  "observed_at_utc": "...",
  "subscription_scope": ["..."],
  "nodes": [],
  "edges": [],
  "limitations": [],
  "graph_digest": "sha256..."
}
```

### Nodes

- subscription;
- resource group;
- Azure resource;
- deterministic child nodes such as a NIC IP configuration;
- unresolved reference nodes when a relationship target was not returned by the bounded inventory query.

A NIC IP configuration becomes a first-class graph node, allowing the UI to zoom from:

```text
subscription
→ resource group
→ VM
→ NIC
→ IP configuration
→ private IP / subnet / public IP / NSG / backend pool
```

### Edges

- `contains`;
- `attached_to`;
- `connected_to`;
- `protected_by`;
- `uses`;
- `exposes`.

Each edge ID is the SHA-256 digest of `source|relationship|target`. Nodes and edges are sorted before the graph digest is calculated, so input ordering does not change the output.

## Required input envelope

The normalizer accepts a private evidence payload shaped as:

```json
{
  "metadata": {
    "observed_at_utc": "2026-07-25T02:00:00Z",
    "subscriptions": ["explicit-subscription-id"],
    "query_complete": true
  },
  "results": {
    "resources": [],
    "vm_attachments": [],
    "nic_ip_configurations": [],
    "subnets": []
  }
}
```

`query_complete` must not become true unless pagination is complete or the result is otherwise proven complete for its bounded scope.

## Validation

Run locally:

```bash
python scripts/azure_resource_graph_semantic_inventory.py --validate-contract-only
python -m unittest tests/test_azure_resource_graph_semantic_inventory.py -v
python scripts/azure_resource_graph_semantic_inventory.py \
  --input tests/fixtures/azure-resource-graph-sample.json \
  --output /tmp/azure-infrastructure-graph.json
```

Expected fixture result:

```text
nodes = 11
edges = 19
private IP node = 10.20.40.10
output deterministic across reordered input = true
```

## Fail-closed behavior

The adapter rejects:

- missing explicit subscription scope;
- records outside the declared subscription scope;
- malformed Azure resource IDs;
- unsupported result-set shapes;
- likely secret-bearing keys;
- invalid IP addresses or subnet prefixes;
- truncated query results without continuation evidence;
- conflicting duplicate edge identities.

## Limits

```text
ARG relationship != verified packet path
ARG private IP != guest interface state
ARG public IP != endpoint reachability
ARG resource existence != secure configuration
ARG role assignment != effective least privilege
ARG observation != deployment provenance
```

ARG is eventually consistent and control-plane oriented. Service validation still requires independent runtime and network evidence.

## Next bounded gate

After exact-head CI and review, separately authorize one read-only collection against an explicit subscription and resource-group allowlist. Capture the raw named query results privately, normalize them, record the graph digest, and reconcile selected graph nodes against the exact repository commit and existing `.project/` evidence.
