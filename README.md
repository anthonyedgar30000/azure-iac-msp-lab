# Azure IaC MSP Lab

A version-controlled Azure infrastructure-as-code portfolio lab for demonstrating practical MSP, systems administration, cloud infrastructure, security, and service-reliability troubleshooting skills.

## Current direction

The lab uses Azure infrastructure to host an on-premises-style Windows services environment. The planned service path includes a public load balancer, redundant VPN gateways, NPS/RADIUS, Active Directory-integrated DNS and Kerberos, and a Windows remote desktop target.

`ServiceTracer` is the deterministic incident-localization component. It traces remote-access transactions assembled from operational evidence, reports the last successful stage and first failed transition, identifies node-specific failure concentration, correlates relevant operational history, and recommends a bounded containment or comparison step.

## Implemented

- Bicep definitions for the segmented virtual network, Log Analytics workspace, and Standard public load balancer.
- Separate edge, identity, server, operations, and remote-user subnets with NSG boundaries.
- A listener-only TCP 443 load-balancer health probe and empty VPN backend pool.
- A durable ServiceTracer collector with JSON/JSONL import, authenticated HTTP or HTTPS ingestion, local structured-syslog ingestion, spool health reporting, size limits, and restart-safe identity indexing.
- A Windows PowerShell sender with bearer authentication and bounded retries.
- A hardened example systemd unit for the collector.
- Deterministic source adapters for load-balancer telemetry, VPN syslog, NPS/Windows events, SNMP collectors, synthetic checks, and ticket/change systems.
- Transaction assembly by correlation identity, ordered service stage, backend identity, timestamp, timeout, and retry evidence.
- Idempotent duplicate handling and rejection of reused evidence identity with divergent content at both the collector and analysis boundaries.
- Incomplete transactions reported as evidence gaps rather than filled with invented success states.
- Load-balancer probe-gap analysis, post-drain containment verification, evidence-preservation guidance, and return-to-service gates.
- CI that validates collector-to-spool-to-analysis flow, source-evidence analysis, replay compatibility, Python tests, and Bicep builds.

## Operational input path

ServiceTracer does not require generated demo attempts. Operational sources can submit structured records to a durable spool:

```text
VPN / load balancer / Windows / SNMP / synthetic probe / ticket source
  -> source-specific parser or exporter
  -> ServiceTracer collector
  -> durable evidence JSONL spool
  -> versioned adapters and transaction assembly
  -> deterministic incident analysis
```

```bash
export SERVICETRACER_COLLECTOR_TOKEN='replace-with-a-secret'

servicetracer-collector http \
  --listen 0.0.0.0 \
  --port 8080 \
  --spool /var/lib/servicetracer/evidence.jsonl \
  --tls-cert /etc/servicetracer/tls/collector.crt \
  --tls-key /etc/servicetracer/tls/collector.key

servicetracer \
  --evidence-records /var/lib/servicetracer/evidence.jsonl \
  --adapter-config servicetracer/examples/evidence_adapters.json \
  --service-path servicetracer/examples/remote_access_service_path.json \
  --output servicetracer-report.json
```

The committed source-record files are regression fixtures. The collector and analyzer accept the same contract from actual monitoring, Windows, network-appliance, synthetic-check, and ticketing integrations.

## Current controlled incident

Mixed source records show one successful attempt through `VPN-01` and one attempt through `VPN-02` that completes public DNS, load-balancer selection, TCP, TLS, and RADIUS request transmission before timing out waiting for a RADIUS response. Load-balancer context still marks `VPN-02` healthy under a listener-only TCP 443 probe. ServiceTracer recommends draining new sessions from the suspected node, preserving evidence, comparing it with `VPN-01` and the approved configuration, and reviewing the overlapping change record.

Post-containment records complete through `VPN-01`, so ServiceTracer records service stabilization under containment while retaining the uncertainty that `VPN-02` has not yet been repaired or independently validated.

## Governance

- `main` is the trusted baseline.
- Changes are developed in bounded feature branches.
- Pull requests distinguish proposed, implemented, deployed, verified, and unresolved work.
- The collector and analysis code are implemented and tested; no Azure infrastructure or live collector service has been deployed or operationally verified yet.
