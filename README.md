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
- A deterministic ServiceTracer prototype with a synthetic intermittent VPN incident.
- Load-balancer probe-gap analysis that distinguishes listener health from full transaction health.
- A post-drain containment dataset showing new sessions routed only through `VPN-01`.
- Structured containment verification, evidence-preservation guidance, and return-to-service gates.
- A related change-history record used only as an investigation lead.
- CI that builds and lints Bicep and runs the Python unit and CLI tests.

## Demo incident

Twenty synthetic remote-access attempts are traced through public DNS, load-balancer selection, TCP, TLS, RADIUS, VPN address assignment, tunnel creation, internal DNS, Kerberos, and RDP.

Nine attempts fail on `VPN-02` while waiting for a RADIUS response. The load balancer still marks `VPN-02` healthy because its probe validates only TCP 443 listener availability. `ServiceTracer` recommends draining new sessions from the suspected node, preserving evidence, comparing `VPN-02` with `VPN-01` and the approved configuration, and reviewing the overlapping change ticket.

A second deterministic dataset represents twelve new-session attempts after `VPN-02` is drained. All twelve complete through `VPN-01`, so ServiceTracer records that service stabilized under containment while retaining the uncertainty that `VPN-02` has not yet been repaired or independently validated.

## Governance

- `main` is the trusted baseline.
- Changes are developed in bounded feature branches.
- Pull requests must distinguish proposed, implemented, deployed, verified, and unresolved work.
- No Azure infrastructure has been deployed or operationally verified yet.
