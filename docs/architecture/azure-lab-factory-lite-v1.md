# Azure Lab Factory Lite v1

## Purpose

Azure Lab Factory Lite turns known-good Bicep workloads into a small catalog of repeatable labs that can be selected, prepared, preflighted, deployed, validated, and removed through one consistent operational path.

The portfolio claim is intentionally practical:

> Select a lab, prove that Azure can support it, deploy the reviewed template, verify the service, and remove the lab cleanly.

This is an infrastructure-delivery feature inside the existing Azure IaC MSP Lab. It is not a general-purpose cloud platform, a dynamic IaC generator, or a multi-agent research system.

## v1 architecture

```text
ChatGPT plugin / simple web UI / CLI
                 |
                 v
       bounded MCP or API tool
                 |
                 v
        fixed lab catalog entry
                 |
                 v
     GitHub Actions preflight gate
                 |
                 v
       reviewed Bicep deployment
                 |
                 v
    service validation and receipt
                 |
                 v
      explicit verified cleanup
```

The AI-facing layer may translate natural language into a candidate request. It does not invent Bicep, select arbitrary resources, grant deployment authority, or bypass the catalog.

## First increment

This increment implements only the deterministic repository foundation:

- a versioned catalog;
- one candidate profile backed by the existing ServiceTracer demo API Bicep root;
- a local `list` command;
- a local `prepare` command;
- request validation;
- template and plan digests;
- fixed preflight, validation, cleanup, and claim boundaries;
- CI tests through the existing infrastructure test job.

It performs no Azure login, query, What-If, deployment, role assignment, model request, MCP network call, cleanup, or workflow dispatch.

## Lab profile contract

A profile must define:

- a stable profile id and semantic version;
- release state: `candidate`, `released`, or `retired`;
- one repository-relative Bicep root and deployment scope;
- bounded environments and locations;
- default, minimum, and maximum TTL;
- a deterministic resource-group naming pattern;
- required, fixed, and default parameters;
- required preflight checks;
- required post-deployment validation checks;
- cleanup strategy and verification;
- explicit claim boundaries.

The initial profile is:

```text
servicetracer-demo-api@1.0.0
release state: candidate
location: westus2 only
default TTL: 8 hours
maximum TTL: 24 hours
template: workloads/servicetracer-demo-api/infra/main.bicep
```

`candidate` means the catalog contract and source are present. It does not mean current capacity, quota, price, permissions, What-If safety, deployment success, or service health have been freshly verified.

## Local usage

List profiles:

```bash
python -m lab_factory list
```

Prepare an incomplete request and see the exact missing parameters:

```bash
python -m lab_factory prepare \
  --profile servicetracer-demo-api \
  --environment dev \
  --ttl-hours 8
```

Prepare a complete request:

```bash
python -m lab_factory prepare \
  --profile servicetracer-demo-api \
  --environment test \
  --location westus2 \
  --ttl-hours 6 \
  --request-id lab-demo-001 \
  --parameter dnsLabel=<unique-label> \
  --parameter allowedOrigin=<https-origin> \
  --parameter backendTransactionUrl=<https-url> \
  --parameter adminSshPublicKey='<public-key>' \
  --parameter sourceRepository=<repository-url> \
  --parameter sourceRef=<exact-commit> \
  --parameter installerUri=<immutable-installer-url>
```

The output does not echo supplied parameter values. It records names, template digest, request scope, gates, and the fact that no Azure action or deployment authority exists.

## Lifecycle

```text
Requested
→ Prepared
→ PreflightPassed
→ Authorized
→ Deploying
→ AzureConverged
→ Validating
→ Ready
→ ExpiredOrDeleteRequested
→ CleaningUp
→ CleanupVerified
```

Failure states preserve the stopping boundary:

```text
ParametersRequired
PreflightRejected
DeploymentFailed
ServiceValidationFailed
CleanupIncomplete
```

A retry is not implied by a failure.

## Preflight gate

A later workflow will verify, in order:

1. exact subscription and tenant context;
2. subscription enabled state;
3. required provider registration;
4. live location and VM SKU availability;
5. regional and VM-family quota;
6. exact resource-group state;
7. ARM template validation;
8. fail-closed What-If classification;
9. accepted cost ceiling;
10. exact reviewed commit and profile version.

The profile's allowed location is a request boundary, not proof of live capacity.

## Deployment gate

Deployment remains a separate explicit authorization after preflight. The future workflow will consume one bounded request and stop after its single permitted attempt.

```text
preflight_passed != deployment_authorized
deployment_attempted != deployment_succeeded
deployment_succeeded != service_validated
```

## Validation and evidence

A lab reaches `Ready` only after the profile-specific service checks pass. The first profile requires:

- successful ARM deployment;
- expected inventory;
- successful VM provisioning;
- HTTP 200 from the health endpoint;
- a bounded transaction response;
- verified CORS origin;
- an evidence receipt.

The evidence receipt should include the request id, exact commit, catalog and template digests, subscription fingerprint, resource group, region, timestamps, What-If summary, deployment result, service tests, and final lifecycle state. Secrets and raw tenant or subscription identifiers must not be promoted.

## Cleanup

The v1 cleanup strategy is resource-group deletion followed by a fresh absence check. Automatic cleanup is deliberately disabled in the repository contract until the deletion path, permissions, failure handling, and evidence receipt are separately implemented and tested.

```text
cleanup_command_succeeded != resources_absent
resource_group_absent != billing_fully_reconciled
```

## Cost boundary

This repository-only increment adds no recurring Azure resource cost. Actual lab cost remains unknown until a fresh preflight obtains current price context and the resulting deployment is observed in billing data.

## Planned increments

1. Add a static MCP `list_lab_profiles` and `prepare_lab_request` interface over this package.
2. Add one read-only GitHub Actions preflight workflow with no mutation authority.
3. Promote the first profile from `candidate` to `released` only after exact-head CI, accepted What-If, deployment, service validation, and cleanup evidence exist.
4. Add one separately authorized deployment workflow.
5. Add expiration registration and verified cleanup.
6. Add a second small lab only after the first profile is operationally repeatable.
