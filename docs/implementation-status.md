# Implementation status

## Implemented

- Repository governance baseline.
- Azure network and monitoring Bicep definitions.
- Standard public load balancer with a TCP 443 listener probe and empty VPN backend pool.
- ServiceTracer deterministic incident analyzer.
- Source-adapter configuration for structured load-balancer, VPN syslog, NPS/Windows, SNMP, synthetic-probe, and ticketing records.
- Canonical evidence identity, provenance fingerprinting, idempotent duplicate handling, and divergent identity rejection.
- Correlation-based assembly of source records into ordered service transactions.
- Explicit incomplete-transaction reporting when contiguous stage evidence is missing.
- Context-evidence preservation for load-balancer probe state and SNMP device health.
- Ticket/change records ingested through the same source-adapter boundary.
- Load-balancer state derived from contextual evidence rather than requiring a separate demo file.
- Load-balancer probe-gap assessment.
- Structured drain plan, evidence-preservation guidance, containment verification, and return-to-service gates.
- Preassembled attempt and deterministic generator retained only for replay and regression compatibility.
- Unit tests for ingestion, identity reuse, evidence gaps, failure-stage localization, node correlation, ticket correlation, probe-gap detection, containment, and recovery gating.
- GitHub Actions validation of the primary source-evidence CLI path, replay compatibility, and Bicep builds.

## Not deployed

- Azure resource group and resources.
- Windows Server virtual machines.
- Active Directory Domain Services, DNS, Kerberos, NPS, or RDS.
- VPN appliance virtual machines or backend-pool associations.
- Live syslog receiver, SNMP collector, Windows Event Forwarding, Azure Monitor data collection rules, or streaming transport.
- Live ticketing-system API connector.

## Not verified

- End-to-end Azure deployment.
- Real VPN transactions.
- Real RADIUS timeout behaviour.
- Real load-balancer backend draining.
- Real probe behaviour against VPN appliances.
- Vendor-specific raw syslog parsing and production collector mappings.
- Operational cost, performance, security, and recovery behaviour.

## Next bounded increments

1. Deploy and verify the network, load balancer, and Log Analytics foundation.
2. Add Windows VM definitions and domain bootstrap automation.
3. Add two VPN appliance nodes and associate their NICs with the load-balancer backend pool.
4. Add collectors or forwarding jobs that emit the implemented structured evidence contract from real syslog, SNMP, Windows events, Azure telemetry, and synthetic checks.
5. Add the live ticketing-system adapter.
6. Add governed configuration comparison for the controlled drift, repair, direct-node validation, and gradual return-to-service sequence.
