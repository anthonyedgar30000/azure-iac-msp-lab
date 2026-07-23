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
- Optional dedicated Azure Storage publication module using the Blob service endpoint, exact-origin Blob CORS, disabled shared-key authorization, OAuth writes, account-level anonymous Blob access limited to the dedicated sanitized-output account, `$web` Blob-only public access, Blob versioning, delete retention, and a narrowly scoped collector data role.
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

### Collector replacement

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

### Existing-collector report publication

- Read-only publication planner run `29965079470` completed successfully against `main` commit `19b8eddf4fb9038a41ba1fb0e81567dcbdfe2e92`.
- It produced artifact `existing-collector-report-publication-plan-29965079470-1` with GitHub digest `sha256:0f0ba512d1c61acc3149cb11c33e66ad7218cc1391f6b32f2fa1176459c2be10`.
- The run verified the intended resource group, region, existing collector identity, no tagged report Storage account, and no visible collector publication role assignment.
- ProviderNoRbac ARM validation and What-If completed with 21 `Ignore` changes and exactly three old-architecture `Create` changes.
- Current price evidence and quota remained unresolved, deployment remained blocked, and Azure mutations were not authorized or performed.
- The run evaluated the superseded static-website URL architecture. It is historical planning evidence and cannot authorize the revised Blob-endpoint deployment.

## Designed and CI-verified but deliberately inactive

- The future collector replacement workflow input surface and ordered state-machine candidate.
- Collector replacement policy ceilings of CAD 10 temporary cost, at most two snapshots and 96 GiB total snapshot capacity, zero compute overlap, and 24-hour recovery-resource retention.
- The explicit rule that Azure budgets, billing alerts, action groups, and billing configuration are out of scope for collector replacement.
- The replacement candidate workflow remains outside `.github/workflows`, cannot be dispatched, does not authenticate to Azure, and contains no mutation commands.
- Rollback remains an explicit collector replacement blocker; that design is not ready for promotion or execution.
- PR #41 is a draft authority-changing publication workflow and is not part of `main`. Its prior three-create planner pin and static-website endpoint assumptions must be replaced after the Blob-endpoint repair is merged and freshly planned.

## Implemented but not yet deployed or operationally verified

- Replacement collector deployment using the Ubuntu 24.04 image and corrected first-boot Python/certificate path.
- ServiceTracer `0.5.0` on the Azure collector.
- The dedicated public-report Storage account, Blob service, `$web` Blob-only access configuration, and collector Blob data role assignment.
- Managed-identity upload from the collector to `$web/reports/technician-handoff-report.json`.
- Anonymous fetch from the Blob service URL with the exact reviewed CORS response.
- Browser loading of the Azure-hosted report, provenance display, expiry warning, and outage fallback.
- A recurring or event-triggered report-generation schedule.

## Not yet implemented as live infrastructure or active execution

- An active mutation-capable collector replacement workflow, tested Azure mutation executor, and dispatch authority.
- A merged and separately authorized live-report publication execution workflow.
- Windows Server virtual machines.
- Active Directory Domain Services, DNS, Kerberos, NPS, or RDS.
- VPN appliance virtual machines or backend-pool associations.
- Windows Event Forwarding, Azure Monitor data collection rules, or production vendor-specific parsers.
- Live SNMP trap receiver or polling integration that emits the structured evidence contract.
- Live ticketing-system API connector.
- Live Proxmox-to-Azure service evidence path.

## Not yet verified

- Current guest service health, ServiceTracer version, evidence-disk mount source, filesystem identity, recent evidence readability, and publisher availability immediately before maintenance or publication.
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
- A fresh four-create publication What-If against the merged Blob-endpoint architecture.
- Current publication Storage pricing, quota, policy allowance, and effective execution identity permissions.
- Account anonymous Blob access, `$web` Blob-only access, CORS, retention, versioning, public fetch, and teardown behavior in Azure.
- Browser rendering of a fresh collector-published report.
- Real collector traffic from Windows, VPN appliances, Azure telemetry, or SNMP tooling.
- Real VPN transactions and RADIUS timeout behavior.
- Real load-balancer backend draining and probe behavior.
- Vendor-specific raw syslog parsing and production collector mappings.
- Collector throughput, disk retention, failover, governed certificate replacement, secret recovery, and repeatable upgrade behavior.
- Operational cost and performance of the complete hybrid scenario.

## Next bounded increments

1. Complete exact-head CI and review for the Blob-endpoint browser-CORS architecture repair.
2. Merge the repair only after explicit merge authorization.
3. Manually rerun the existing read-only publication planner against the exact merge commit.
4. Verify the new What-If contains only the reviewed Storage account, Blob service, `$web` container, and current-principal role-assignment creations, with protected infrastructure ignored.
5. Obtain fresh West US 2 cost and quota evidence and define the minimum execution identity permissions.
6. Rebase or repin PR #41 to the merged architecture and fresh planner artifact; keep it draft until its execution guards and rollback are re-reviewed.
7. Obtain separate explicit human authorization before dispatching any Azure mutation workflow.
8. Prove the collector publisher exists and works before creating the endpoint.
9. Deploy the bounded publication resources, publish through managed identity, fetch from the Blob service URL, and verify schema, freshness, CORS, content equality, and rollback behavior.
10. Test the report through the console query-string override, then commit the verified URL to `docs/report-source.json` in a separate repository-only increment.
11. Confirm stale-report behavior and deliberate fallback by temporarily making the endpoint unavailable.
12. Continue collector replacement only after recovery, rollback, network-preservation, cost, and permission blockers are independently resolved.
13. Add Windows VM definitions and domain bootstrap automation.
14. Add two VPN appliance nodes and associate their NICs with the load-balancer backend pool.
15. Add source-specific Windows, Azure, VPN, SNMP, and synthetic-check exporters that emit the implemented contract.
16. Replace the bootstrap self-signed certificate and locally generated token with governed certificate and secret delivery.
17. Add the live ticketing-system adapter and governed configuration comparison for drift repair and return to service.
