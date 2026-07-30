# Lab Factory ratified planner binding v1

## Outcome

The Lab Factory catalog and local MCP planning tools now identify the repository's existing ServiceTracer demo API planner instead of inventing a second Azure execution path.

```text
list_lab_profiles
        |
        v
catalog profile + ratified planner metadata

prepare_lab_request
        |
        v
deterministic prepare-only plan
+ workflow path
+ dual-subscription boundary
+ safe derived inputs
+ remaining human inputs
+ exact confirmation pattern
```

No workflow was dispatched and no Azure state was observed or changed.

## Bound architecture

```text
ChatGPT or local MCP client
            |
            v
prepare_lab_request
            |
            v
servicetracer-demo-api@1.0.0
            |
            v
.github/workflows/servicetracer-demo-api-subproject-plan.yml
            |
      separate OIDC identities
        /                 \
Azure for Students      Pay-As-You-Go
read-only dependency    planning-only target
```

The planner remains manual-only, uses the protected `azure-api-payg` GitHub Environment, validates with `ProviderNoRbac`, performs ARM validation and bounded What-If, uploads evidence, and contains no deployment command.

## MCP output boundary

The repository-only MCP tools expose enough information to route a prepared request correctly:

```text
workflow_path: .github/workflows/servicetracer-demo-api-subproject-plan.yml
github_environment: azure-api-payg
dispatch_mode: manual_only
subscription_boundary: dual_subscription
provider_validation_level: ProviderNoRbac
includes_arm_validation: true
includes_arm_what_if: true
deployment_command_present: false
```

For a `dev` request, the MCP plan can derive:

```text
environment: dev
location: westus2
prefix: mst
dependency_resource_group: rg-servicetracer-dev-westus2
vm_size: Standard_F1als_v7
```

It still requires human-provided planning inputs:

```text
dns_label
allowed_origin
maximum_monthly_cost_cad
```

The confirmation pattern is returned as:

```text
PLAN-DEMO-API-SUBPROJECT:dev:<dns-label>
```

Parameter values remain absent from MCP results.

## Identity, network, and security

```text
new Azure identity: none
new RBAC: none
new secret: none
new Azure network path: none
remote MCP endpoint: none
ChatGPT connection: not verified
model call: none
```

The binding fails closed when the workflow path disappears, the GitHub Environment changes, the subscription boundary stops being dual, ProviderNoRbac changes, identity-separation markers disappear, ARM validation or What-If is removed, the installer marker changes, or a deployment command appears.

## Cost and quota

```text
repository recurring Azure resource cost delta: CAD $0
actual Azure cost freshly observed: false
Azure quota freshly observed: false
planning cost ceiling supplied: false
```

The future planner's human cost ceiling remains planning context, not a billing control or deployment spend authority.

## Failure, rollback, and cleanup

Repository rollback is an exact PR revert. Azure rollback and cleanup do not apply because this increment performs no Azure authentication, query, validation, What-If, mutation, or deployment.

## Evidence to retain

- exact branch head;
- catalog diff and catalog version `1.1.0`;
- planner-binding module and validation tests;
- MCP profile and prepare-output tests;
- exact-head CI conclusions;
- live-main and open-PR freshness check before merge.

## Canonical boundaries

```text
catalog bound to planner != workflow dispatched
MCP plan prepared != Azure preflight observed
planner contains ARM What-If != ARM What-If executed
planning workflow success != deployment authorized
dependency subscription != target subscription
estimated cost != actual cost
```

## Next gate

After merge, a separate explicit decision can authorize one manual dispatch of the existing ServiceTracer dual-subscription planner from immutable `main`. The protected evidence must be reviewed and promoted before any deployment decision.
