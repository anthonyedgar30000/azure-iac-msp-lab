# ServiceTracer — Governed Azure Operations Lab

A version-controlled Azure operations and infrastructure-as-code portfolio lab demonstrating deterministic service-path localization, governed evidence, bounded AI-assisted reasoning, explicit human authority, cloud infrastructure, security, cost awareness, and service-reliability troubleshooting.

The GitHub repository retains the historical name `azure-iac-msp-lab`. **ServiceTracer — Governed Azure Operations Lab** is the canonical portfolio and bounded repository-workstream identity inside the broader **HELIX — Governed Agent Engineering** conversational workspace.

## Canonical workspace

**HELIX — Governed Agent Engineering** is the umbrella ChatGPT project for governed-agent architecture, cross-workstream reasoning, and review routing. This repository represents the bounded **ServiceTracer — Governed Azure Operations Lab** workstream. Chat context supports continuity; GitHub, pull requests, CI, workflow artifacts, Azure evidence, and [`.project/`](.project/) remain authoritative for implementation, coordination, deployment, and operational state.

ServiceTracer work is organized into six governed streams:

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
