# Implementation status

## Implemented

- Repository governance baseline.
- Azure network and monitoring Bicep definitions.
- Standard public load balancer with a TCP 443 listener probe and empty VPN backend pool.
- ServiceTracer deterministic incident analyzer.
- Durable JSONL evidence spool with restart-safe identity indexing.
- JSON, JSON-array, and JSONL import for monitoring and ticket exports.
- Authenticated HTTP or HTTPS evidence collection with body limits, health endpoint, and protected status endpoint.
- Local structured-syslog TCP and UDP listeners for records already converted to the ServiceTracer evidence contract.
- Windows PowerShell evidence sender with bearer authentication and bounded retries.
- Hardened example systemd unit for running the collector in the operations subnet.
- Source-adapter configuration for structured load-balancer, VPN syslog, NPS/Windows, SNMP, synthetic-probe, and ticketing records.
- Canonical evidence identity, provenance fingerprinting, idempotent duplicate handling, and divergent identity rejection.
- Batch preflight so conflicting evidence identity prevents partial collector writes.
- Correlation-based assembly of source records into ordered service transactions.
- Explicit incomplete-transaction reporting when contiguous stage evidence is missing.
- Context-evidence preservation for load-balancer probe state and SNMP device health.
- Ticket/change records ingested through the same source-adapter boundary.
- Load-balancer state derived from contextual evidence rather than requiring a separate demo file.
- Load-balancer probe-gap assessment.
- Structured drain plan, evidence-preservation guidance, containment verification, and return-to-service gates.
- Preassembled attempt and deterministic generator retained only for replay and regression compatibility.
- Unit tests for collector persistence, authentication, identity reuse, batch atomicity, structured syslog extraction, ingestion, evidence gaps, localization, probe gaps, containment, and recovery gating.
- GitHub Actions validation of collector-to-spool-to-analysis flow, source-evidence analysis, replay compatibility, and Bicep builds.

## Not deployed

- Azure resource group and resources.
- Windows Server virtual machines.
- Active Directory Domain Services, DNS, Kerberos, NPS, or RDS.
- VPN appliance virtual machines or backend-pool associations.
- Running collector VM or service in the operations subnet.
- Collector TLS certificate, bearer secret, service account, or durable Azure disk.
- Windows Event Forwarding, Azure Monitor data collection rules, or vendor-specific parsers.
- Live SNMP trap receiver or polling integration that emits the structured evidence contract.
- Live ticketing-system API connector.

## Not verified

- End-to-end Azure deployment.
- Real collector traffic from Windows, VPN appliances, Azure telemetry, or SNMP tooling.
- Real VPN transactions and RADIUS timeout behaviour.
- Real load-balancer backend draining and probe behaviour.
- Vendor-specific raw syslog parsing and production collector mappings.
- Collector throughput, disk retention, backup, failover, certificate rotation, and recovery behaviour.
- Operational cost, performance, and security behaviour in Azure.

## Next bounded increments

1. Add the operations collector VM definition, managed disk, identity, and bootstrap automation.
2. Deploy and verify the network, load balancer, Log Analytics workspace, and collector service.
3. Add Windows VM definitions and domain bootstrap automation.
4. Add two VPN appliance nodes and associate their NICs with the load-balancer backend pool.
5. Add source-specific Windows, Azure, VPN, SNMP, and synthetic-check exporters that emit the implemented contract.
6. Add the live ticketing-system adapter.
7. Add governed configuration comparison for drift repair, direct-node validation, and gradual return to service.
