# Azure IaC MSP Lab

A version-controlled Azure infrastructure-as-code portfolio lab for demonstrating practical MSP, systems administration, cloud infrastructure, security, and service-reliability troubleshooting skills.

## Current direction

The lab uses Azure infrastructure to host an on-premises-style Windows services environment. The planned service path includes a public load balancer, redundant VPN gateways, NPS/RADIUS, Active Directory-integrated DNS and Kerberos, and a Windows remote desktop target.

`ServiceTracer` is the deterministic incident-localization component. It traces a remote-access transaction through its observable stages, reports the last successful stage and first failed transition, identifies node-specific failure concentration, correlates relevant change history, and recommends a bounded containment or comparison step.

## Implemented

- Bicep definitions for the segmented virtual network, Log Analytics workspace, and Standard public load balancer.
- Separate edge, identity, server, operations, and remote-user subnets.
- Subnet network security groups with explicit demo traffic boundaries.
- A listener-only TCP 443 load-balancer health probe and empty VPN backend pool ready for future appliance nodes.
- Deterministic source adapters that normalize structured records from load-balancer telemetry, VPN syslog, NPS/Windows events, SNMP collectors, synthetic probes, and ticket/change systems.
- Transaction assembly by correlation identity, ordered service stage, backend identity, timestamp, timeout, and retry evidence.
- Idempotent duplicate handling and rejection of reused evidence identity with divergent content.
- Incomplete transactions are reported as evidence gaps rather than filled with invented success states.
- Load-balancer probe-gap analysis that distinguishes listener health from full transaction health.
- Post-drain containment verification showing new sessions routed only through `VPN-01`.
- Structured containment guidance, evidence preservation, and return-to-service gates.
- CI that validates the source-evidence path, preassembled replay compatibility, Python tests, and Bicep builds.

## Operational input boundary

ServiceTracer does not require the synthetic demo generator. Its primary CLI path accepts one or more structured source-record streams and an adapter configuration:

```bash
servicetracer \
  --evidence-records collector-export.jsonl \
  --adapter-config servicetracer/examples/evidence_adapters.json \
  --service-path servicetracer/examples/remote_access_service_path.json \
  --output servicetracer-report.json
```

The committed source-record files are regression fixtures. In the deployed lab, the same contract is intended to receive structured exports or forwarded events from the actual monitoring and ticketing integrations.

## Current controlled incident

Mixed source records show one successful attempt through `VPN-01` and one attempt through `VPN-02` that completes public DNS, load-balancer selection, TCP, TLS, and RADIUS request transmission before timing out waiting for a RADIUS response. Load-balancer context still marks `VPN-02` healthy under a listener-only TCP 443 probe. ServiceTracer recommends draining new sessions from the suspected node, preserving evidence, comparing it with `VPN-01` and the approved configuration, and reviewing the overlapping change record.

Post-containment source records complete through `VPN-01`, so ServiceTracer records service stabilization under containment while retaining the uncertainty that `VPN-02` has not yet been repaired or independently validated.

## Governance

- `main` is the trusted baseline.
- Changes are developed in bounded feature branches.
- Pull requests must distinguish proposed, implemented, deployed, verified, and unresolved work.
- No Azure infrastructure has been deployed or operationally verified yet.
