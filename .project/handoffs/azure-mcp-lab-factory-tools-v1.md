# Azure MCP Lab Factory tools v1

## Objective

Expose the merged Azure Lab Factory Lite catalog and deterministic prepare-only planner through the existing local MCP server.

This increment adds:

```text
list_lab_profiles
prepare_lab_request
```

It preserves the existing:

```text
get_current_reality
```

## Starting boundary

```text
repository: anthonyedgar30000/azure-iac-msp-lab
base branch: main
base commit: 4136a47d9aa80da99e3849fc721bab55a883b20e
latest merged PR: #214
open PRs observed before branch: none
branch: agent/lab-factory-mcp-tools-v1
```

No live Azure query was performed for this repository-only increment. The latest preserved evidence remains time-bounded and must not be treated as current cost, quota, capacity, RBAC, deployment, runtime, backup, or recovery truth.

## Intended architecture

```text
Local MCP client
       |
       v
azure_mcp_reality.server
       |
       +-- get_current_reality
       |      fixed read-only Azure and Git observation
       |
       +-- list_lab_profiles
       |      repository catalog only
       |
       +-- prepare_lab_request
              repository catalog + deterministic planner only
```

The server remains local:

```text
stdio
or
127.0.0.1:8000/mcp
```

No remote endpoint, public ingress, API Management route, Container Apps deployment, or ChatGPT app connection is created.

## Scope and dependencies

Repository dependencies:

```text
azure_mcp_reality/server.py
azure_mcp_reality/lab_factory_tools.py
lab_factory/catalog.json
lab_factory/catalog.py
requirements/azure-mcp-reality-tool.txt
```

The lab tools reuse the merged Lab Factory planner. They do not create a second catalog, duplicate planning logic, or generate Bicep.

## Identity and permissions

```text
list_lab_profiles requires Azure identity: false
prepare_lab_request requires Azure identity: false
new managed identity: false
new Entra application: false
new Azure RBAC: false
secret created or persisted: false
```

The `get_current_reality` identity model is unchanged and remains separately bounded to an explicitly configured existing Azure CLI session. This increment does not authorize calling that tool.

## Network paths

```text
repository-only lab tools -> local filesystem reads
Azure network path added -> none
remote MCP path deployed -> none
public endpoint created -> none
```

## Security controls

- Default-deny tool admission.
- Exact three-tool allowlist.
- Read-only, non-destructive, idempotent annotations.
- Lab tools are closed-world and cannot select an arbitrary template.
- Profile, environment, location, TTL, and parameter names are validated by the catalog.
- Fixed parameters cannot be overridden.
- Parameter values are validated but not returned in the plan.
- No Azure CLI command is executed by either lab tool.
- Automatic cleanup remains disabled.
- Prepared plans explicitly preserve deployment and cleanup authority as false.

## Cost and quota

```text
expected recurring Azure resource cost delta: CAD $0
actual Azure cost freshly observed: false
Azure quota freshly observed: false
GitHub Actions and package-download usage may apply: true
```

## Deployment method

This is a repository-only pull request. It does not deploy infrastructure.

Runtime startup after merge remains:

```bash
python -m pip install -r requirements/azure-mcp-reality-tool.txt
python -m azure_mcp_reality.server --transport stdio
```

or loopback HTTP:

```bash
python -m azure_mcp_reality.server --transport streamable-http
```

## Validation

Required exact-head checks:

```text
contract validator passes
existing Azure MCP contract tests pass
new Lab Factory MCP unit tests pass
Lab Factory CLI/planner tests pass
server advertises exactly three approved tools
planner output matches direct Lab Factory output
identical request produces identical digest
unknown profile is rejected
TTL above 24 hours is rejected
eastus override is rejected
parameter values are absent from results
complete infrastructure and workload test discovery passes
Bicep lint/build passes
```

Expected tool classifications:

```text
get_current_reality: read-only, open-world
list_lab_profiles: read-only, closed-world
prepare_lab_request: read-only, closed-world
```

## Failure and rollback

Failures are fail-closed. A catalog error, unknown profile, unapproved location, out-of-range TTL, fixed-parameter override, missing template, or tool-inventory mismatch rejects the request before any Azure access.

Repository rollback:

```text
revert the exact pull request
```

Runtime rollback:

```text
stop the local MCP process
```

Azure rollback or cleanup:

```text
not applicable
```

No Azure resource is created or modified by this increment.

## Evidence to capture

- Exact source head.
- Changed-file inventory.
- Contract digest.
- Unit-test output.
- MCP tool descriptor output.
- Exact-head CI run identifiers and conclusions.
- Merge commit, only after merge.

## Claim boundaries

```text
historical_single_tool_contract != current_server_inventory
profile_listed != released_lab
prepared_request != ARM_what_if
prepared_request != deployment_authorized
catalog_allowed_location != live_capacity_available
parameter_validated != parameter_value_persisted
local_tool_implemented != ChatGPT_connected
cleanup_defined != cleanup_verified
```

## Next gate

After exact-head CI, connect a local MCP client and call only `list_lab_profiles` and `prepare_lab_request`.

Remote hosting, ChatGPT connection, Azure preflight, ARM What-If, deployment, RBAC changes, service validation, cleanup, and cleanup verification each require a separate bounded authorization.
