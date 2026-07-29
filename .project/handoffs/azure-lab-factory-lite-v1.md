# Azure Lab Factory Lite v1 handoff

## Objective

Create a practical, portfolio-sized Azure lab delivery foundation:

```text
fixed catalog
→ deterministic request preparation
→ future read-only preflight
→ separately authorized deployment
→ service validation
→ verified cleanup
```

The work is intentionally smaller than a general cloud platform. It reuses the repository's existing Bicep workload and operational evidence discipline.

## Live repository boundary at start

```text
repository: anthonyedgar30000/azure-iac-msp-lab
previous substantive main: ca0712569f0b4bc18ceba2610c988a01f91750f2
current base main: 5509a982ea118b2c1108af8ee5c6a44d60df9884
open pull requests before implementation: none
implementation branch: agent/azure-lab-factory-lite-v1
pull request: #212 / draft
```

Two administrative commits temporarily created and then removed `tmp-placeholder` on `main`. GitHub comparison reports two commits and zero file differences between `ca071256...` and `5509a982...`. They are not Azure evidence and do not alter repository content.

## Exact-head baseline evidence

The latest substantive source head before this increment was PR #211 head `c426ef5759b9a7ad7a3ef18083c9c740218d2225`.

Its pull-request workflows succeeded:

```text
CI: 30452108536 / success
Azure MCP reality bridge contract: 30452111122 / success
Azure AI activation static validation: 30452114873 / success
```

No fresh Azure query was performed for this increment.

## Implemented files

```text
lab_factory/__init__.py
lab_factory/__main__.py
lab_factory/catalog.json
lab_factory/catalog.py
lab_factory/cli.py
infra/tests/test_lab_factory_lite.py
docs/architecture/azure-lab-factory-lite-v1.md
.project/contracts/azure-lab-factory-lite-v1.json
.project/handoffs/azure-lab-factory-lite-v1.md
```

## First profile

```text
profile: servicetracer-demo-api@1.0.0
state: candidate
template: workloads/servicetracer-demo-api/infra/main.bicep
scope: subscription
location: westus2
default TTL: 8 hours
maximum TTL: 24 hours
cleanup automation: disabled
```

`candidate` preserves that the source and contract exist while current capacity, quota, price, permissions, What-If safety, deployment, service health, and cleanup remain unverified for a new lab request.

## Planner behavior

The local CLI can:

- list approved profiles;
- select one fixed profile and version;
- validate environment, location, TTL, request id, and parameter names;
- reject arbitrary profile, template, location, or fixed-parameter overrides;
- report missing parameters;
- calculate catalog, template, and plan digests;
- produce the deterministic resource-group name;
- preserve preflight, deployment-authorization, service-validation, and cleanup gates;
- avoid echoing supplied parameter values.

It cannot:

- authenticate to Azure;
- query Azure;
- execute What-If;
- deploy or delete resources;
- grant roles;
- call a model;
- host a remote MCP endpoint;
- register a ChatGPT plugin.

## Exact-head validation

The new tests are discovered by the existing `Bicep lint and build` CI job through:

```bash
python -m unittest discover -s infra/tests -v
```

The tests cover catalog structure, Bicep source binding, missing-parameter gating, complete request preparation, value redaction, deterministic output, location rejection, fixed-parameter protection, TTL boundaries, static CLI listing, and duplicate-parameter rejection.

PR #212 head before this handoff refresh was `62d0c4d9671202b4f9cc63b20d1629ff698340af`. Exact-head CI run `30500683486` succeeded:

```text
ServiceTracer tests: success
Validate infrastructure and workload contracts: success
Bicep lint and build: success
```

This handoff refresh creates a newer repository-only head. Its content change does not alter executable code, but the newest exact head still requires ordinary CI before merge.

## Authority and cost

```text
repository implementation: authorized
branch and pull request: authorized
ordinary pull-request CI: authorized
merge: not assumed
workflow dispatch or rerun: not authorized
Azure authentication or query: not authorized
Azure mutation: not authorized
remote MCP deployment: not authorized
cleanup: not authorized
expected recurring Azure cost delta: CAD $0
actual cost freshly observed: false
quota freshly observed: false
```

## Failure and rollback

Catalog or request errors fail before a plan is emitted and perform no cloud action. Repository rollback is an exact revert or pull-request closure. No Azure rollback exists because this increment exposes no Azure execution path.

## Next gate

Wait for ordinary CI on the refreshed exact head, then review PR #212. Merge requires a separate decision. The next implementation increment should expose `list_lab_profiles` and `prepare_lab_request` through the existing local MCP server without adding Azure authority.
