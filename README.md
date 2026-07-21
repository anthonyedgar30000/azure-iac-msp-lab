# ServiceTracer — Governed Azure Operations Lab

A version-controlled Azure operations and infrastructure-as-code portfolio lab demonstrating deterministic service-path localization, governed evidence, bounded AI-assisted reasoning, explicit human authority, cloud infrastructure, security, cost awareness, and service-reliability troubleshooting.

The GitHub repository retains the historical name `azure-iac-msp-lab`; this project title is the canonical portfolio and workspace identity.

## Canonical workspace

The ChatGPT project is the canonical conversational workspace. GitHub, pull requests, CI, workflow artifacts, Azure evidence, and [`.project/`](.project/) remain authoritative for implementation, coordination, deployment, and operational state.

Work is organized into six governed streams:

1. **Architecture and design decisions**
2. **Azure resource plan and IaC**
3. **Deployment evidence and screenshots**
4. **Cost, health, and configuration telemetry**
5. **ServiceTracer findings and reports**
6. **Portfolio/demo narrative**

The machine-readable catalog in [`.project/workstream-catalog.json`](.project/workstream-catalog.json) defines each stream's purpose, repository paths, and claim boundary.

## Current direction

The lab uses Azure infrastructure to host an on-premises-style Windows services environment. The planned service path includes a public load balancer, redundant VPN gateways, NPS/RADIUS, Active Directory-integrated DNS and Kerberos, and a Windows remote desktop target.

`ServiceTracer` is the deterministic incident-localization component. It traces remote-access transactions assembled from operational evidence, reports the last successful stage and first failed transition, identifies node-specific failure concentration, correlates relevant operational history, and recommends a bounded containment or comparison step.

## Visual portfolio demo

The operator console in [`docs/`](docs/) presents the bounded VPN incident in a browser-friendly format:

- both VPN backends remain healthy under the configured listener-only load-balancer probe;
- observed failures are concentrated on `VPN-02` while `VPN-01` remains the healthy comparison;
- ServiceTracer stops at the `VPN-02` investigation boundary and does not claim the exact root cause;
- the technician then moves the affected user to `VPN-01`, repairs `VPN-02`, validates it with a test user, and returns the original user.

Run it locally:

```bash
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000`. GitHub Pages publishes `main` from the `/docs` folder.

The browser first checks [`docs/report-source.json`](docs/report-source.json) for a live public-report URL. A live report must use the versioned `servicetracer.public-report.v1` envelope, include provenance and expiry metadata, and preserve the bounded technician-handoff contract. If no live URL is configured, the page uses the committed demonstration fixture. The browser remains a presentation layer and does not perform incident analysis.

For a one-time test without committing the endpoint URL, append a URL-encoded `report` query parameter:

```text
?report=https://<storage-account>.z13.web.core.windows.net/reports/technician-handoff-report.json
```

## Implemented

- Bicep definitions for the segmented virtual network, Log Analytics workspace, Standard public load balancer, and optional private operations collector VM.
- Separate edge, identity, server, operations, and remote-user subnets with NSG boundaries.
- A listener-only TCP 443 load-balancer health probe and empty VPN backend pool.
- An optional Ubuntu 24.04 collector VM with no public IP, a system-assigned identity, Trusted Launch, static private addressing, and a separately managed evidence disk that detaches rather than being deleted with the VM.
- Cloud-init that mounts the evidence disk without overwriting an existing filesystem, verifies Python 3.11 or newer, installs a pinned ServiceTracer source ref, generates a local bearer token and deterministic private TLS certificate, starts the collector, and verifies its health endpoint.
- A durable ServiceTracer collector with JSON/JSONL import, authenticated HTTP or HTTPS ingestion, local structured-syslog ingestion, spool health reporting, size limits, and restart-safe identity indexing.
- A Windows PowerShell sender with bearer authentication and bounded retries.
- Deterministic source adapters for load-balancer telemetry, VPN syslog, NPS/Windows events, SNMP collectors, synthetic checks, and ticket/change systems.
- Transaction assembly by correlation identity, ordered service stage, backend identity, timestamp, timeout, and retry evidence.
- Idempotent duplicate handling and rejection of reused evidence identity with divergent content at both the collector and analysis boundaries.
- Incomplete transactions reported as evidence gaps rather than filled with invented success states.
- Load-balancer probe-gap analysis, post-drain containment verification, evidence-preservation guidance, and return-to-service gates.
- A strict public-report sanitizer that drops fields outside the technician-handoff allowlist and refuses reports that claim an exact root cause.
- Managed-identity publication of sanitized reports to an optional, dedicated Azure Storage static-website endpoint.
- A responsive operator console with live-report provenance, expiry warnings, and bounded fixture fallback.
- CI that validates collector-to-spool-to-analysis-to-publication flow, collector VM and bootstrap contracts, source-evidence analysis, replay compatibility, visual-demo boundaries, Python tests, Bicep builds, and shared workflow state.

## Operational input and publication path

ServiceTracer does not require generated demo attempts. Operational sources can submit structured records to a durable spool:

```text
VPN / load balancer / Windows / SNMP / synthetic probe / ticket source
  -> source-specific parser or exporter
  -> ServiceTracer collector
  -> durable evidence JSONL spool
  -> versioned adapters and transaction assembly
  -> deterministic incident analysis
  -> bounded technician-handoff report
  -> strict public sanitizer
  -> Azure Storage public-report endpoint
  -> GitHub Pages presentation layer
```

```bash
export SERVICETRACER_COLLECTOR_TOKEN='replace-with-a-secret'

servicetracer-collector http \
  --listen 0.0.0.0 \
  --port 8080 \
  --spool /var/lib/servicetracer/evidence.jsonl \
  --tls-cert /var/lib/servicetracer/tls/collector.crt \
  --tls-key /var/lib/servicetracer/tls/collector.key

servicetracer \
  --evidence-records /var/lib/servicetracer/evidence/evidence.jsonl \
  --adapter-config servicetracer/examples/evidence_adapters.json \
  --service-path servicetracer/examples/remote_access_service_path.json \
  --report-view technician-handoff \
  --output /tmp/technician-handoff-report.json

servicetracer-publish-report \
  --input /tmp/technician-handoff-report.json \
  --storage-account '<public-report-storage-account>' \
  --source-id 'stcollector-dev'
```

The final command obtains a Storage data-plane token from the Azure Instance Metadata Service and uploads only the sanitized public envelope. It does not embed an account key, SAS token, collector bearer token, or Azure credential in the report or web page.

The committed source-record files are regression fixtures. The collector and analyzer accept the same contract from actual monitoring, Windows, network-appliance, synthetic-check, and ticketing integrations.

## Azure deployment boundary

The committed development parameters keep both `deployOperationsCollector=false` and `deployPublicReportEndpoint=false` to avoid accidental compute or storage deployment. A real deployment must provide an SSH public key, pin a tested source commit, review the target Azure resources, and complete the verification gates documented in [`docs/collector-vm.md`](docs/collector-vm.md).

The public endpoint is deployed only when both the collector and `deployPublicReportEndpoint` are enabled. Its Bicep output supplies the storage account name and browser report URL. The operator must then run the publisher and place that URL in `docs/report-source.json` or use the query-string override during verification.

## Current controlled incident

Mixed source records show one successful attempt through `VPN-01` and one attempt through `VPN-02` that completes public DNS, load-balancer selection, TCP, TLS, and RADIUS request transmission before timing out waiting for a RADIUS response. Load-balancer context still marks `VPN-02` healthy under a listener-only TCP 443 probe. ServiceTracer recommends draining new sessions from the suspected node, preserving evidence, comparing it with `VPN-01` and the approved configuration, and reviewing the overlapping change record.

Post-containment records complete through `VPN-01`, so ServiceTracer records service stabilization under containment while retaining the uncertainty that `VPN-02` has not yet been repaired or independently validated.

## Workflow observability

Shared project state lives in [`.project/`](.project/). It records active branch ownership, trusted baseline, verified environment facts, deployment history, decisions, workstream boundaries, and the current handoff so separate conversations do not reconstruct conflicting versions of reality.

Before changing the project, read `.project/active-work.json`, `.project/workstream-catalog.json`, `.project/environment-state.json`, and the current handoff, then confirm the live GitHub and CI state. Validate the metadata locally with:

```bash
python .project/validate.py
```

One bounded workstream owns writes to one branch. Other conversations may review that branch, but parallel implementation requires a separate branch and workstream entry.

## Repository context governance

Repository lookup follows [`HELIX-RETRIEVAL-POLICY.md`](HELIX-RETRIEVAL-POLICY.md). [`.helix/`](.helix/) classifies current, supporting, candidate, explicit-only archive, and excluded-sensitive context.

Keyword matches and conversation recollections are candidates until authority, state, freshness, and retrieval class are verified. `.helix/archive/` is excluded from ordinary lookup and never overrides current source, tests, decisions, CI, or runtime evidence.

Structured metadata can itself become stale. When `.project/`, implementation-status documents, or runbooks conflict with live Git, pull-request, CI, or Azure evidence, surface the conflict and refresh the record rather than silently trusting the older description.

## Governance

- `main` is the trusted baseline.
- Changes are developed in bounded feature branches.
- Pull requests distinguish proposed, implemented, deployed, verified, and unresolved work.
- Conversations and agent progress summaries are reasoning context, not repository authority; durable insights are promoted as decisions, schemas, tests, runbooks, current-state records, or bounded evidence summaries.
- The collector VM has been deployed and manually verified in Azure.
- Python and certificate bootstrap drift found during that deployment is corrected in the IaC/bootstrap source, but the corrected image path has not yet been verified by replacing or redeploying the existing VM.
- Collector image-drift detection and a read-only replacement plan are implemented; no collector replacement execution is authorized or operationally verified.
- The live public-report endpoint and browser integration are implemented and statically tested but are not yet deployed or operationally verified in Azure.
