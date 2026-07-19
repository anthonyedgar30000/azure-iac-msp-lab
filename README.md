# Azure IaC MSP Lab

A version-controlled Azure infrastructure-as-code portfolio lab for demonstrating practical MSP, systems administration, cloud infrastructure, security, and service-reliability troubleshooting skills.

## Current direction

The lab uses Azure infrastructure to host an on-premises-style Windows services environment. The planned service path includes a public load balancer, redundant VPN gateways, NPS/RADIUS, Active Directory-integrated DNS and Kerberos, and a Windows remote desktop target.

`ServiceTracer` is the deterministic incident-localization component. It traces a remote-access transaction through its observable stages, reports the last successful stage and first failed transition, identifies node-specific failure concentration, correlates relevant change history, and recommends a bounded containment or comparison step.

## Implemented in this increment

- Bicep definitions for the segmented virtual network and Log Analytics workspace.
- Separate edge, identity, server, operations, and remote-user subnets.
- Subnet network security groups with explicit demo traffic boundaries.
- A deterministic ServiceTracer prototype with a synthetic intermittent VPN incident.
- A related change-history record used only as an investigation lead.
- CI that builds and lints Bicep and runs the Python unit tests.

## Demo incident

Twenty synthetic remote-access attempts are traced through public DNS, load-balancer selection, TCP, TLS, RADIUS, VPN address assignment, tunnel creation, internal DNS, Kerberos, and RDP.

Nine attempts fail on `VPN-02` while waiting for a RADIUS response. `ServiceTracer` recommends draining new sessions from the suspected node, preserving evidence, comparing `VPN-02` with `VPN-01` and the approved configuration, and reviewing the overlapping change ticket.

## Governance

- `main` is the trusted baseline.
- Changes are developed in bounded feature branches.
- Pull requests must distinguish proposed, implemented, deployed, verified, and unresolved work.
- No Azure infrastructure has been deployed or operationally verified yet.
