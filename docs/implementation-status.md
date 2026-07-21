# Implementation status

## Implemented

- Repository governance baseline.
- Repository-native workflow observability in `.project/`, including active work, environment facts, deployment history, decisions, handoffs, and CI validation.
- HELIX retrieval and archive governance in `.helix/`, including authority precedence, retrieval classes, candidate promotion, scoped review lenses, and explicit-only historical lookup.
- Azure network and monitoring Bicep definitions.
- Standard public load balancer with a TCP 443 listener probe and empty VPN backend pool.
- Optional private Ubuntu 24.04 operations collector VM definition.
- Static private collector NIC with no public IP.
- System-assigned collector managed identity.
- Trusted Launch, Secure Boot, virtual TPM, managed boot diagnostics, and SSH-key-only administration.
- Separately managed Standard SSD evidence disk configured to detach rather than be deleted with the VM.
- Cloud-init that preserves an existing evidence filesystem, mounts the managed disk, verifies Python 3.11 or newer, installs a configured ServiceTracer source ref, generates a local bearer token and deterministic TLS certificate, starts the systemd service, and verifies its health endpoint.
- Committed development parameters that keep collector compute and public-report storage disabled by default.
- Manual GitHub Actions Azure lifecycle workflow using workload identity federation.
- Guarded `what-if`, `deploy`, `verify`, and `teardown` operations with a protected environment boundary.
- Deployment requires a tested 40-character source commit and an environment-provided SSH public key.
- Teardown requires an approved ServiceTracer resource-group name and exact typed confirmation.
- Azure and guest verification through VM Run Command covering private networking, managed identity, evidence-disk policy, cloud-init, mount state, systemd health, authenticated durable receipt, and restart persistence.
- Non-secret Azure lifecycle evidence artifacts for validation, What-If, deployment, verification, inventory, and teardown results.
- A shared desired collector-image contract used by Bicep and validation.
- Pre-planning detection of immutable collector image-line drift that blocks ordinary What-If or Deploy when replacement is required.
- A separate manually dispatched, read-only collector replacement planner with exact confirmation, inventory collection, preservation boundaries, and explicit proof that Azure mutations are not authorized or performed.
- Runtime and static tests for the image-drift guard, replacement-planning workflow, desired-image contract, and pre-ARM execution order.
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
- Bounded technician-handoff report that localizes the incident to `VPN-02` without claiming a device-level root cause.
- Static GitHub Pages operator console with technician workflow visualization.
- Strict public-report sanitizer and versioned `servicetracer.public-report.v1` envelope with source, version, generation, and expiry metadata.
- Local atomic public-envelope output and Azure Blob publication using managed-identity OAuth.
- Optional dedicated Azure Storage static-website module with restricted CORS, disabled shared-key authorization, Blob versioning, delete retention, and a narrowly scoped collector data role.
- Operator console support for live public envelopes, stale-report warning, provenance display, query-string test override, and controlled fixture fallback.
- Preassembled attempts and the deterministic generator retained only for replay and regression compatibility.
- Unit tests for collector persistence, authentication, identity reuse, batch atomicity, structured syslog extraction, ingestion, evidence gaps, localization, probe gaps, containment, recovery gating, report sanitization, managed-identity upload, visual fallback, collector VM security, disk retention, bootstrap behavior, publication infrastructure, lifecycle guardrails, image-drift planning, and safe default parameters.
- GitHub Actions validation of collector-to-spool-to-analysis-to-publication flow, source-evidence analysis, replay compatibility, collector VM and lifecycle contracts, workflow-observability state, and Bicep builds.

## Deployed and manually verified

- The Azure operations collector VM, private NIC, system-assigned identity, OS disk, and separately managed evidence disk.
- Evidence-disk mounting at `/var/lib/servicetracer`.
- The hardened `servicetracer-collector.service` and local `/healthz` endpoint.
- ServiceTracer `0.4.0` after manual installation of Python 3.11 and repair of certificate generation.
- Generation of the bounded `technician-handoff` report from the deployed collector VM.
- GitHub Pages publication of the static operator console from `main/docs`.

## Implemented but not yet deployed or operationally verified

- Replacement collector deployment using the Ubuntu 24.04 image and corrected first-boot Python/certificate path.
- ServiceTracer `0.5.0` on the Azure collector.
- The dedicated public-report Storage account and collector Blob data role assignment.
- Managed-identity upload from the collector to `$web/reports/technician-handoff-report.json`.
- Browser loading of the Azure-hosted report, provenance display, expiry warning, and outage fallback.
- A recurring or event-triggered report-generation schedule.
- The read-only collector replacement planner against the actual target resource group; the workflow is merged and CI-verified, but no run artifact is recorded in the repository state.

## Not yet implemented as live infrastructure

- Windows Server virtual machines.
- Active Directory Domain Services, DNS, Kerberos, NPS, or RDS.
- VPN appliance virtual machines or backend-pool associations.
- Windows Event Forwarding, Azure Monitor data collection rules, or production vendor-specific parsers.
- Live SNMP trap receiver or polling integration that emits the structured evidence contract.
- Live ticketing-system API connector.
- Live Proxmox-to-Azure service evidence path.

## Not yet verified

- A current read-only inventory of the collector VM, desired and deployed image references, NIC, OS disk, evidence disk, system-assigned identity, and visible RBAC assignments.
- Promotion of the exact Azure workflow evidence for the immutable `imageReference` deployment failure into the repository state layer.
- Replacement of the current collector VM while retaining and reattaching the evidence disk.
- A verified recovery point before any collector replacement execution.
- Availability and successful boot of the selected Ubuntu 24.04 image and VM size in the target subscription and region.
- Corrected cloud-init execution without manual Python or certificate intervention.
- Evidence-disk backup, detachment, reattachment, and recovery behavior during VM replacement.
- Recreation of managed-identity-dependent report permissions after a replacement VM receives a new principal identity.
- Real collector traffic from Windows, VPN appliances, Azure telemetry, or SNMP tooling.
- Real VPN transactions and RADIUS timeout behavior.
- Real load-balancer backend draining and probe behavior.
- Vendor-specific raw syslog parsing and production collector mappings.
- Collector throughput, disk retention, failover, governed certificate replacement, secret recovery, and repeatable upgrade behavior.
- Storage public-output retention, deletion, cost, CORS, and security behavior in Azure.
- Operational cost and performance of the complete hybrid scenario.

## Next bounded increments

1. Manually run the read-only **Collector replacement plan** workflow with the exact planning confirmation for the target collector.
2. Review the resulting package separately under evidence-quality, operations/recovery, security/identity, and Azure-cost lenses; record what each review did not cover.
3. Promote the bounded inventory, immutable-image finding, preservation requirements, identity/RBAC dependencies, and unresolved evidence into `.project/environment-state.json`, `deployment-history.jsonl`, and a scoped review artifact.
4. Design a separate replacement-execution branch only after a recovery point is verified and the evidence disk, disposable compute boundary, managed identity, role restoration, and rollback sequence are explicit.
5. Obtain separate explicit human authorization before any delete, detach, snapshot, create, update, or replacement operation.
6. Replace and verify the collector only through that governed execution path, then prove the Ubuntu 24.04 bootstrap, ServiceTracer `0.5.0`, evidence-disk reattachment, service health, durable ingestion, and permission restoration.
7. Generate the technician-handoff report on the verified collector and publish it with managed identity.
8. Verify the public envelope contains no raw evidence, credentials, private endpoints, customer identifiers, or exact-root-cause claim.
9. Test the report URL through the console query-string override, then commit the verified URL to `docs/report-source.json`.
10. Confirm stale-report behavior and deliberate fallback by temporarily making the endpoint unavailable.
11. Add Windows VM definitions and domain bootstrap automation.
12. Add two VPN appliance nodes and associate their NICs with the load-balancer backend pool.
13. Add source-specific Windows, Azure, VPN, SNMP, and synthetic-check exporters that emit the implemented contract.
14. Replace the bootstrap self-signed certificate and locally generated token with governed certificate and secret delivery.
15. Add the live ticketing-system adapter and governed configuration comparison for drift repair and return to service.
