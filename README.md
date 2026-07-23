# ServiceTracer — Governed Azure Operations Lab

A version-controlled Azure infrastructure and operations portfolio lab demonstrating deterministic service-path localization, evidence-bearing infrastructure-as-code, bounded AI-assisted control, explicit human authority, security, cost awareness, recovery design, and professional operational verification.

The repository retains the historical name `azure-iac-msp-lab`. **ServiceTracer — Governed Azure Operations Lab** is the bounded repository workstream inside the broader **HELIX — Governed Agent Engineering** conversational workspace.

## Authority model

Chat context supports continuity. It does not override:

1. live Git and GitHub state;
2. exact-head CI;
3. committed source, tests, and project governance;
4. protected workflow artifacts;
5. fresh Azure control-plane, guest, service, cost, and recovery evidence.

```text
declared_in_code != deployed_in_Azure
CI_passed != service_validated
resource_exists != securely_configured
backup_configured != recovery_tested
```

Shared durable state lives under [`.project/`](.project/). Current branches, pull requests, repository head, and CI are queried live rather than persisted as self-updating truth.

## Governed workstreams

The machine-readable catalog defines six streams:

1. architecture and design decisions;
2. Azure resource plan and IaC;
3. deployment evidence and screenshots;
4. cost, health, and configuration telemetry;
5. ServiceTracer findings and reports;
6. portfolio and demo narrative.

## What ServiceTracer does

ServiceTracer ingests structured operational evidence, preserves provenance, assembles correlated service transactions, and deterministically identifies:

- the last successful stage;
- the first failed transition;
- the backend or fault domain where failures concentrate;
- contradictions and missing evidence;
- a bounded comparison or containment action.

It does not claim an exact device root cause without supporting evidence.

## Current demo architecture

The active public demo strategy is collector-hosted:

```text
GitHub Pages
→ dedicated Azure public IP and DNS
→ second frontend on the existing Standard Load Balancer
→ IP-based backend pool targeting private collector 10.20.40.10
→ Nginx TLS termination and rate limiting
→ loopback-only Python API on 127.0.0.1:8090
→ existing remote-access transaction endpoint
→ synthetic VPN-01 and VPN-02 backends
```

The previous Microsoft.Web / Azure Function design is retired from the active path after the subscription exposed a zero-capacity boundary and the failed deployment left partial resources.

The collector-hosted deployment uses an isolated Bicep root:

```text
infra/collector-demo-api.bicep
```

It references the existing collector, virtual network, load balancer, and operations NSG instead of redeclaring the base infrastructure.

## Repository capabilities

Implemented and CI-verified:

- segmented Azure network and NSG design;
- Standard Public Load Balancer;
- private operations collector VM definition;
- Trusted Launch, Secure Boot, vTPM, managed identity, SSH-key-only administration, and separate evidence disk;
- deterministic ServiceTracer collector and analyzer;
- durable JSONL evidence spool;
- authenticated HTTP/HTTPS and structured-syslog ingestion;
- adapters for load-balancer, VPN, Windows/NPS, SNMP, synthetic checks, and ticket/change records;
- correlation-based transaction assembly;
- evidence-gap reporting;
- load-balancer probe-gap assessment;
- bounded technician handoff;
- strict public-report sanitizer;
- GitHub Pages operator console;
- existing-collector report-publication planning and execution workflows;
- collector replacement and recovery designs;
- synthetic VPN backend infrastructure;
- collector-hosted demo API, installer, workflow, readiness assessor, isolated What-If classifier, and Bicep root;
- Governed Persistence Loop controller.

## Azure reality currently supported by evidence

The newest promoted authenticated observation is deploy workflow run `30044644501`, captured at `2026-07-23T21:05:01Z`.

At that timestamp:

- resource group: `rg-servicetracer-dev-westus2`;
- region: `westus2`;
- collector: `vm-stcollector-mst-dev`;
- collector state: running;
- collector size: `Standard_B2ats_v2`;
- collector private IP: `10.20.40.10`;
- collector public IP: none;
- collector demo API public IP: not present;
- Public IP quota: 1 used of 3;
- resource-group read-only locks: none.

These are time-bounded control-plane observations. Current guest health, running version, evidence readability, effective permissions, and actual cost remain separate verification tasks.

Two synthetic backend VMs were observed in Azure after the retired legacy deployment attempt. Their services and transaction behavior remain unverified.

The failed legacy deployment also left:

- Application Insights `appi-demo-api-mst-dev`;
- storage account `storfxczr3fewce`.

No cleanup is authorized merely because those resources are known.

## Latest collector API planning and deploy result

Run `30040676542` proved the broad base template was unsafe because it predicted protected collector, disk, NIC, load-balancer, public-IP, VNet, subnet, and NSG changes. PR #56 introduced the isolated Bicep root.

Deploy run `30044644501` then:

- passed readiness and ARM validation;
- accepted nine isolated Create changes;
- classified no protected base-resource modification;
- received explicit deployment authority for that run;
- attempted deployment;
- failed because the parent CLI and nested Bicep module used the same ARM deployment name;
- produced no deployment result JSON;
- skipped service verification.

PR #59 repairs the name collision in repository code and adds a regression test.

```text
isolated_WhatIf_accepted = true
deployment_attempted      = true
deployment_succeeded      = false
post_failure_mutation     = not_proven
service_validated         = false
```

Because the template changed and the failed run does not prove zero partial mutation, a fresh inventory and isolated What-If are required before a separately authorized retry.

## Visual portfolio demo

Serve the operator console locally:

```bash
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000`.

The default source remains the committed controlled fixture. No unverified live endpoint is committed.

After a bounded deployment, test a verified endpoint without changing repository defaults:

```text
?api=https://<verified-fqdn>/api/demo/run
```

The page requests 20 correlated transactions, validates the bounded API response, and falls back to the controlled fixture when the live source is unavailable.

A live URL is promoted only after Azure existence, TLS, API health, transaction, CORS, and browser-rendering evidence is recorded.

## Operational data path

```text
monitoring / VPN / Windows / SNMP / synthetic / ticket source
→ source-specific exporter
→ ServiceTracer collector
→ durable evidence spool
→ versioned adapters
→ correlated service transactions
→ deterministic analysis
→ bounded technician handoff
→ optional strict public sanitizer
→ governed publication and browser presentation
```

Example local commands:

```bash
export SERVICETRACER_COLLECTOR_TOKEN='replace-with-a-secret'

servicetracer-collector http   --listen 0.0.0.0   --port 8080   --spool /var/lib/servicetracer/evidence.jsonl   --tls-cert /var/lib/servicetracer/tls/collector.crt   --tls-key /var/lib/servicetracer/tls/collector.key

servicetracer   --evidence-records /var/lib/servicetracer/evidence.jsonl   --adapter-config servicetracer/examples/evidence_adapters.json   --service-path servicetracer/examples/remote_access_service_path.json   --report-view technician-handoff   --output /tmp/technician-handoff-report.json
```

Do not commit credentials, tokens, private keys, raw protected evidence, or customer-sensitive data.

## Azure execution boundary

Manual workflows use:

- exact reviewed commits;
- typed confirmations;
- the protected `azure-lab` environment;
- workload identity federation;
- fail-closed planning and classifiers;
- protected evidence artifacts.

A workflow being present does not authorize dispatch.

An accepted What-If does not authorize deployment.

A deployment does not prove service success.

Current durable authority grants only the separately bounded read-only existing-collector publication planner. Collector API planning or deployment requires a fresh explicit instruction.

## Governed Persistence Loop

The repository contains a deterministic controller for:

- `proceed`;
- `fix`;
- `sync_with_reality`;
- `restrategize`;
- `verify`;
- `rollback`;
- `escalate`;
- `complete`.

The controller preserves the objective, authorized scope, and authority boundaries. It recommends a typed next message from recorded evidence; it does not execute or grant new authority.

## Collector replacement and recovery

The lab includes fail-closed replacement and recovery contracts for:

- image-drift detection;
- evidence-disk preservation;
- NIC handling;
- identity and RBAC restoration;
- snapshot-based rollback;
- isolated boot rehearsal;
- cleanup and cost ceilings;
- evidence-package validation.

These are repository designs, not recovery proof.

No active mutation-capable replacement workflow, verified snapshot recovery point, boot rehearsal, rollback execution, or disaster-recovery validation exists.

## Cost and quota

Promoted evidence includes bounded planning observations, not billing truth.

At the latest collector API observation before the failed deploy:

- Public IP usage was 1 of 3;
- two units remained.

An earlier backend plan estimated approximately CAD 19.42 for 730 hours of two selected VMs using captured retail rows.

Not currently observed:

- invoice-level spend;
- remaining student credit;
- complete resource-level allocation;
- taxes, discounts, or negotiated pricing;
- actual ongoing cost of partial resources.

```text
retail_estimate != actual_cost
student_credit_available != zero_cost
```

## Project workflow

Before changing infrastructure:

1. query live repository and PR state;
2. inspect exact-head CI;
3. read `.project/active-work.json`;
4. read `.project/environment-state.json`;
5. read the latest deployment-history event;
6. read the current handoff;
7. inspect fresh Azure evidence for the exact scope;
8. define authority, validation, rollback, cleanup, and evidence capture.

Validate durable state with:

```bash
python .project/validate.py
```

## Safe next operation

After the full reality-sync change is reviewed and merged, the next bounded operation is a fresh read-only collector API `what-if` against the exact merged commit containing PR #59 and the isolated Bicep root.

Any protected-resource Modify, Delete, Replace, or unexpected Create remains a blocker.

Deployment, partial-resource cleanup, report publication, collector replacement, and rollback each require separate explicit authority and evidence gates.
