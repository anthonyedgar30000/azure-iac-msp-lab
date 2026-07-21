# Implementation status

## Implemented

- Repository governance baseline.
- Repository-native workflow observability in `.project/`, including active work, environment facts, deployment history, decisions, handoffs, and CI validation.
- The bounded **ServiceTracer — Governed Azure Operations Lab** repository workstream inside the umbrella **HELIX — Governed Agent Engineering** conversational workspace, with an exact six-stream machine-readable catalog and validator enforcement.
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
- A fail-closed collector replacement execution contract pinned to the promoted planner run and artifact digest.
- A deterministic replacement-design validator covering target identity, phase order, mutation classification, review lenses, cost ceilings, cleanup boundaries, and unresolved rollback state.
- An inactive candidate replacement workflow stored under `infra/workflow-designs/`, outside `.github/workflows`, with an unconditional design-only blocker before Azure authentication.
- CI tests proving the candidate is non-dispatchable, contains no Azure mutation commands, rejects authorization in the design state, and remains `promotion_ready: false`.
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
- Unit tests for collector persistence, authentication, identity reuse, batch atomicity, structured syslog extraction, ingestion, evidence gaps, localization, probe gaps, containment, recovery gating, report sanitization, managed-identity upload, visual fallback, collector VM security, disk retention, bootstrap behavior, publication infrastructure, lifecycle guardrails, image-drift planning, replacement execution design, and safe default parameters.
- GitHub Actions validation of collector-to-spool-to-analysis-to-publication flow, source-evidence analysis, replay compatibility, collector VM and lifecycle contracts, workflow-observability state, canonical workstream catalog, replacement execution design, and Bicep builds.

## Deployed and manually verified

- The Azure operations collector VM, private NIC, system-assigned identity, OS disk, and separately managed evidence disk.
- Evidence-disk mounting at `/var/lib/servicetracer`.
- The hardened `servicetracer-collector.service` and local `/healthz` endpoint.
- ServiceTracer `0.4.0` after manual installation of Python 3.11 and repair of certificate generation.
- Generation of the bounded `technician-handoff` report from the deployed collector VM.
- GitHub Pages publication of the static operator console from `main/docs`.

## Read-only Azure evidence verified

- Collector replacement plan workflow run `29856203054` completed successfully against the target resource group.
- The run used repository commit `93fcdaf6c1d99f88f3ae8c34f86533a020e1a29a` and produced artifact `collector-replacement-plan-29856203054-1` with SHA-256 `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`.
- Azure mutations were not authorized and were not performed.
- The current control-plane VM size is `Standard_B2ats_v2`; the prior `Standard_B1ms` record remains historical evidence of an earlier verified working size.
- The deployed collector uses Canonical Ubuntu 22.04 Jammy while the desired contract uses Canonical Ubuntu 24.04; replacement is required.
- The evidence disk is attached, uses detach-on-delete semantics, disables public network access, and must be preserved.
- The NIC has static private addressing and VM `deleteOption: Delete`; preservation or deterministic recreation is unresolved.
- The VM uses a system-assigned identity and the planner returned no visible current role assignments.
- The current disposable OS disk allows public network access and should be hardened in the replacement design.
- The sanitized four-lens review is recorded in `docs/reviews/collector-replacement-plan-2026-07-21.md`.

## Designed and CI-verified but deliberately inactive

- PR #25 merged the collector replacement authority, evidence, phase, cost, cleanup, and review contract into `main`.
- The future workflow input surface and ordered state-machine candidate.
- The policy ceilings of CAD 10 temporary cost, at most two snapshots and 96 GiB total snapshot capacity, zero compute overlap, and 24-hour recovery-resource retention.
- The explicit rule that Azure budgets, billing alerts, action groups, and billing configuration are out of scope.
- The candidate workflow is not under `.github/workflows`, cannot be dispatched, does not authenticate to Azure, and contains no mutation commands.
- Rollback remains an explicit blocker; the design is not ready for promotion or execution.

## Implemented but not yet deployed or operationally verified

- Replacement collector deployment using the Ubuntu 24.04 image and corrected first-boot Python/certificate path.
- ServiceTracer `0.5.0` on the Azure collector.
- The dedicated public-report Storage account and collector Blob data role assignment.
- Managed-identity upload from the collector to `$web/reports/technician-handoff-report.json`.
- Browser loading of the Azure-hosted report, provenance display, expiry warning, and outage fallback.
- A recurring or event-triggered report-generation schedule.

## Not yet implemented as live infrastructure or active execution

- An active mutation-capable collector replacement workflow, tested Azure mutation executor, and dispatch authority.
- Windows Server virtual machines.
- Active Directory Domain Services, DNS, Kerberos, NPS, or RDS.
- VPN appliance virtual machines or backend-pool associations.
- Windows Event Forwarding, Azure Monitor data collection rules, or production vendor-specific parsers.
- Live SNMP trap receiver or polling integration that emits the structured evidence contract.
- Live ticketing-system API connector.
- Live Proxmox-to-Azure service evidence path.

## Not yet verified

- Current guest service health, ServiceTracer version, evidence-disk mount source, filesystem identity, and recent evidence readability immediately before maintenance.
- A verified evidence-disk recovery point before any collector replacement execution.
- NIC preservation or deterministic recreation of its subnet, static addressing, and security relationships.
- Replacement of the current collector VM while retaining and reattaching the evidence disk.
- Availability and successful boot of the selected Ubuntu 24.04 image and final VM size in the target subscription and region.
- Corrected cloud-init execution without manual Python or certificate intervention.
- Evidence-disk backup, detachment, reattachment, and recovery behavior during VM replacement.
- Recreation and verification of managed-identity-dependent report permissions after a replacement VM receives a new principal identity.
- Replacement OS-disk public-network hardening.
- Temporary replacement-resource cost, maximum overlap period, cleanup ownership, and cleanup evidence.
- A tested rollback mechanism that resolves canonical OS-disk naming and can restore the prior bootable collector after VM deletion.
- Real collector traffic from Windows, VPN appliances, Azure telemetry, or SNMP tooling.
- Real VPN transactions and RADIUS timeout behavior.
- Real load-balancer backend draining and probe behavior.
- Vendor-specific raw syslog parsing and production collector mappings.
- Collector throughput, disk retention, failover, governed certificate replacement, secret recovery, and repeatable upgrade behavior.
- Storage public-output retention, deletion, cost, CORS, and security behavior in Azure.
- Operational cost and performance of the complete hybrid scenario.

## Next bounded increments

1. Perform independent evidence-quality, operations/recovery, security/identity, and Azure-cost reviews of the merged fail-closed design.
2. Resolve rollback by selecting and testing either temporary old-OS-disk preservation or verified OS-disk snapshot recreation.
3. Define the fresh pre-maintenance guest and control-plane evidence schema.
4. Implement recovery-point creation and independent verification behind fake-Azure-CLI tests.
5. Implement and test NIC delete-option preservation and post-delete resource verification.
6. Implement approved managed-identity/RBAC restoration from an explicit allowlist.
7. Implement replacement OS-disk public-network hardening and verification.
8. Add current cost estimation, cleanup owner, cleanup deadline, and deletion evidence.
9. Record the four separate review decisions and unresolved conditions in repository evidence.
10. Use a separate authority-changing PR to promote an implementation into `.github/workflows` only after every blocker is resolved.
11. Obtain separate explicit human authorization before dispatching any snapshot, detach, delete, create, update, or replacement operation.
12. Replace and verify the collector only through that governed execution path, then prove Ubuntu 24.04 bootstrap, ServiceTracer `0.5.0`, evidence-disk reattachment, service health, durable ingestion, and permission restoration.
13. Generate the technician-handoff report on the verified collector and publish it with managed identity.
14. Verify the public envelope contains no raw evidence, credentials, private endpoints, customer identifiers, or exact-root-cause claim.
15. Test the report URL through the console query-string override, then commit the verified URL to `docs/report-source.json`.
16. Confirm stale-report behavior and deliberate fallback by temporarily making the endpoint unavailable.
17. Add Windows VM definitions and domain bootstrap automation.
18. Add two VPN appliance nodes and associate their NICs with the load-balancer backend pool.
19. Add source-specific Windows, Azure, VPN, SNMP, and synthetic-check exporters that emit the implemented contract.
20. Replace the bootstrap self-signed certificate and locally generated token with governed certificate and secret delivery.
21. Add the live ticketing-system adapter and governed configuration comparison for drift repair and return to service.
