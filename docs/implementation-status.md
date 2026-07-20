# Implementation status

## Implemented

- Repository governance baseline.
- Azure network and monitoring Bicep definitions.
- Standard public load balancer with a TCP 443 listener probe and empty VPN backend pool.
- Optional private Ubuntu operations collector VM definition.
- Static private collector NIC with no public IP.
- System-assigned collector managed identity with no broad role assignment.
- Trusted Launch, Secure Boot, virtual TPM, managed boot diagnostics, and SSH-key-only administration.
- Separately managed Standard SSD evidence disk configured to detach rather than be deleted with the VM.
- Cloud-init that preserves an existing evidence filesystem, mounts the managed disk, installs a configured ServiceTracer source ref, generates a local bearer token and TLS certificate, starts the systemd service, and verifies its health endpoint.
- Committed development parameters that keep collector compute disabled by default.
- ServiceTracer deterministic incident analyzer.
- Durable JSONL evidence spool with restart-safe identity indexing.
- JSON, JSON-array, and JSONL import for monitoring and ticket exports.
- Authenticated HTTP or HTTPS evidence collection with body limits, health endpoint, and protected status endpoint.
- Local structured-syslog TCP and UDP listeners for records already converted to the ServiceTracer evidence contract.
- Windows PowerShell evidence sender with bearer authentication and bounded retries.
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
- Preassembled attempts and the deterministic generator retained only for replay and regression compatibility.
- Unit tests for collector persistence, authentication, identity reuse, batch atomicity, structured syslog extraction, ingestion, evidence gaps, localization, probe gaps, containment, recovery gating, collector VM security, disk retention, bootstrap behavior, and safe default parameters.
- GitHub Actions validation of collector-to-spool-to-analysis flow, source-evidence analysis, replay compatibility, collector VM contracts, and Bicep builds.

## Not deployed

- Azure resource group and resources.
- Operations collector VM, NIC, identity, OS disk, or evidence disk.
- Collector TLS certificate, bearer token, or running systemd service in Azure.
- Windows Server virtual machines.
- Active Directory Domain Services, DNS, Kerberos, NPS, or RDS.
- VPN appliance virtual machines or backend-pool associations.
- Windows Event Forwarding, Azure Monitor data collection rules, or vendor-specific parsers.
- Live SNMP trap receiver or polling integration that emits the structured evidence contract.
- Live ticketing-system API connector.

## Not verified

- End-to-end Azure deployment.
- Availability of the selected Ubuntu image and VM size in the target subscription and region.
- Cloud-init execution on a real Azure VM.
- Evidence-disk formatting, remounting, detachment, reattachment, backup, and recovery behavior.
- Real collector traffic from Windows, VPN appliances, Azure telemetry, or SNMP tooling.
- Real VPN transactions and RADIUS timeout behavior.
- Real load-balancer backend draining and probe behavior.
- Vendor-specific raw syslog parsing and production collector mappings.
- Collector throughput, disk retention, failover, certificate replacement, secret recovery, and upgrade behavior.
- Operational cost, performance, and security behavior in Azure.

## Next bounded increments

1. Deploy and verify the network, load balancer, Log Analytics workspace, and collector VM using a pinned source commit.
2. Record collector VM, NIC, identity, disk, cloud-init, systemd, TLS, authenticated receipt, restart, and teardown evidence.
3. Add Windows VM definitions and domain bootstrap automation.
4. Add two VPN appliance nodes and associate their NICs with the load-balancer backend pool.
5. Add source-specific Windows, Azure, VPN, SNMP, and synthetic-check exporters that emit the implemented contract.
6. Replace the bootstrap self-signed certificate and locally generated token with governed certificate and secret delivery.
7. Add the live ticketing-system adapter.
8. Add governed configuration comparison for drift repair, direct-node validation, and gradual return to service.
