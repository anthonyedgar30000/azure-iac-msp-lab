# Collector recovery evidence schema design

## Status and authority

This increment is **repository design only**. It defines evidence formats and deterministic validation for a future collector replacement or rollback operation. It does not authenticate to Azure, connect to the guest, activate a workflow, create resources, change state, restore RBAC, or authorize the `REPLACE:` confirmation phrase.

Canonical boundary:

`schema_valid != evidence_captured != execution_authorized != recovery_succeeded`

## Intended architecture

The evidence path is deliberately separate from the future execution path:

```text
read-only guest probes ─┐
                       ├─> typed evidence records ─> correlated bundle ─> fail-closed validator ─> human review
read-only Azure probes ─┘                                      │
                                                               ├─> phase-failure evidence when a gate fails
future authorized actions ─────────────────────────────────────└─> rollback-outcome evidence when rollback is attempted
```

The authoritative design contract is `infra/recovery-evidence/collector-recovery-evidence-contract.json`. Five JSON Schema draft 2020-12 documents define guest preflight, Azure control-plane preflight, phase failure, rollback outcome, and the correlated evidence bundle. The standard-library validator enforces cross-record rules that JSON Schema alone cannot prove, including exact observation coverage, shared correlation, unique evidence identities, target binding, freshness, exit-code consistency, redaction, and authority boundaries.

## Region and resource scope

The design remains pinned to the current collector replacement target:

- resource group: `rg-servicetracer-dev-westus2`;
- Azure region: `westus2`;
- collector VM: `vm-stcollector-mst-dev`;
- collector NIC: `nic-stcollector-mst-dev`;
- evidence disk: `disk-stcollector-evidence-mst-dev`;
- OS disk: `disk-stcollector-os-mst-dev`;
- guest evidence mount: `/var/lib/servicetracer`.

These names express intended evidence binding. They do not prove that the resources still exist or retain the previously observed configuration. The latest promoted Azure observation remains planner run `29856203054` from July 21, 2026 and is not current-day proof.

## Dependencies

Repository validation requires only Python 3.12 and the standard library. No new package, service, workflow, Azure role, managed identity, endpoint, or paid resource is introduced.

Future runtime capture will depend on separately reviewed implementations for:

- bounded guest read-only probes;
- authenticated Azure read-only queries;
- protected raw evidence storage;
- sanitized review generation;
- artifact hashing and retention enforcement;
- explicit execution authorization outside this design increment.

## Identity and permissions

This increment grants no permissions. The design records identity provenance without storing raw tenant, subscription, or principal identifiers in repository-promoted evidence.

Future guest collection should use a bounded read-only identity capable of checking service state, the local health endpoint, mount source, filesystem UUID, recent evidence readability, checkpoint digest, OS identity, and quiescence capability. Future Azure collection should use the minimum read-only permissions needed to inspect the exact target resources, visible role assignments, SKU availability, quota, and subscription-specific cost inputs.

A valid preflight bundle explicitly records:

- `read_only: true`;
- `azure_mutations_authorized: false`;
- the authenticated principal as a SHA-256 binding rather than a repository-visible identifier;
- no execution authorization reference.

## Network paths

No network path is opened or changed. The schemas merely describe future observations from existing approved paths. A later collection implementation must document its guest access path, Azure control-plane endpoints, DNS dependencies, firewall or NSG path, proxy requirements, and failure behavior before use.

## Required guest observations

A complete guest preflight bundle contains exactly one fresh record for each of these kinds:

1. `collector_service_active`;
2. `local_health_endpoint_success`;
3. `evidence_mount_source`;
4. `filesystem_uuid`;
5. `recent_evidence_readable`;
6. `evidence_checkpoint_digest`;
7. `guest_os_identity`;
8. `collector_write_quiescence_capability`.

Every record includes command identity, redacted arguments, execution identity, shell, exit code, duration, stdout and stderr digests, timestamps, before and after observation state, target binding, redaction metadata, and provenance.

## Required Azure control-plane observations

A complete Azure preflight bundle contains exactly one fresh record for each of these kinds:

1. `subscription_context`;
2. `resource_group_identity`;
3. `collector_vm_state`;
4. `collector_vm_security_profile`;
5. `collector_nic_binding`;
6. `collector_static_address`;
7. `evidence_disk_identity`;
8. `evidence_disk_access_policy`;
9. `os_disk_identity`;
10. `os_disk_recreation_metadata`;
11. `managed_identity_principal`;
12. `visible_role_assignments`;
13. `sku_availability`;
14. `regional_quota`;
15. `temporary_cost_preflight`;
16. `cleanup_owner_and_deadline`.

The evidence must distinguish “no visible role assignment” from “least privilege verified.” Visibility is not proof of effective permission evaluation.

## Correlation and state rules

All preflight records must share one `maintenance_correlation_id`, bind to one operation ID, identify the exact phase, and target the same collector resource digest. Evidence IDs must be unique. Observed and recorded timestamps use RFC3339 UTC with a maximum 120-second capture skew. Each observation carries an explicit freshness value and fails validation above 900 seconds.

Preflight evidence is read-only, so `state.changed` must be false. The `before` and `after` objects describe observed state, not a mutation. Future mutation-phase records must preserve actual before and after state rather than reusing this preflight rule.

## Command and result integrity

A record cannot claim success when either the command or result exit code is non-zero. Command identity, stdout, stderr, artifact, target resource, guest host, and authenticated principal bindings use lowercase SHA-256 digests. Raw command output is not embedded in repository-promoted records.

The validator rejects:

- missing or duplicate required observations;
- correlation or target mismatches;
- duplicate evidence IDs;
- stale evidence;
- inconsistent exit codes;
- preflight state mutation;
- enabled Azure mutation authority;
- missing sanitized target digests;
- exact resource IDs in sanitized records;
- known secret-bearing markers;
- failed preflight evidence without a phase-failure record;
- rollback success without separate authorized runtime evidence.

## Redaction and evidence hygiene

Raw evidence and sanitized review evidence are different products.

- `raw_private` evidence requires exact resource identity and belongs only in a protected evidence store with bounded retention.
- `sanitized_review` evidence replaces subscription, tenant, principal, and resource identifiers with placeholders and SHA-256 bindings.
- Raw private records may not be promoted into this public repository.
- Repository examples must be sanitized and must declare `secrets_detected: false`.
- Bearer headers, client secrets, passwords, private keys, SAS signatures, and similar markers fail validation.

The generated design fixture is synthetic data. Its passing result proves only that the contract and validator agree.

## Failure evidence

Any failed preflight record requires a phase-failure record containing:

- failed phase and evidence ID;
- failure class and observed state;
- stop decision;
- mutations observed, including an explicit empty list before mutation;
- whether rollback is required;
- the operator action required.

Allowed stop decisions are `abort_before_mutation`, `stop_and_preserve`, and `initiate_reviewed_rollback`. Failure evidence cannot claim success.

## Rollback evidence

If rollback is attempted, a rollback-outcome record must identify the triggering failure, selected strategy, authorization reference, timing, ordered steps, verification, outcome, and residual risk. The only selected strategy remains `os_disk_snapshot_recreate_canonical_name`.

A rollback outcome of `succeeded`, or `operationally_tested: true`, is rejected unless separate runtime evidence shows Azure authentication and mutation authority were explicitly granted and carries a non-empty authorization reference. This repository design does not provide such evidence.

## Security controls

- closed JSON objects reject undeclared fields;
- schema IDs and versions are pinned by the contract;
- raw output is represented by hashes, not embedded content;
- sanitized evidence forbids exact resource IDs;
- mutation authority is false for all preflight evidence;
- secret markers fail closed;
- target and correlation drift fail closed;
- runtime success claims require a separate authorization and evidence boundary.

## Cost implications

The repository increment has no Azure runtime cost. A future operation must include a fresh `temporary_cost_preflight` record, subscription-specific pricing, regional SKU availability, quota, cleanup owner, and cleanup deadline before temporary recovery resources are created. Existing planning boundaries remain CAD 4 reviewed estimate, renewed approval above CAD 4, and unconditional stop above CAD 10.

## Deployment method

There is no Azure deployment method in this increment. The repository change is delivered through a bounded branch and pull request. The schemas and validator are not copied into `.github/workflows/` and no execution command is added.

A future promotion must use a separate pull request that defines the collector implementation, protected artifact storage, identity, network path, retention, and explicit human authorization. Promotion must not silently reinterpret this design as permission to run recovery.

## Validation commands and expected outputs

Run from the repository root:

```bash
python infra/recovery-evidence/validate_recovery_evidence.py
python -m unittest discover -s infra/tests -v
python .project/validate.py
```

Expected validator summary:

```json
{
  "design": {
    "design_valid": true,
    "design_state": "fail_closed_design_only",
    "schema_count": 5,
    "runtime_execution_authorized": false,
    "azure_mutations_authorized": false
  },
  "bundle": {
    "bundle_valid": true,
    "guest_record_count": 8,
    "azure_record_count": 16,
    "evidence_identity_count": 24,
    "runtime_execution_authorized": false,
    "azure_mutations_authorized": false
  }
}
```

The exact-head GitHub CI run must also pass ServiceTracer tests, operational smoke checks, the complete `infra/tests` suite, and Bicep lint/build.

## Failure and rollback behavior for this increment

If schema or fixture validation fails, keep the pull request draft, inspect the exact failing invariant, patch only the declared repository files, and rerun exact-head CI. Do not loosen a security, correlation, freshness, or authority requirement merely to make a fixture pass.

Repository rollback is closing the pull request without merge or reverting the merge commit. No Azure rollback applies because this increment performs no Azure authentication or mutation.

## Cleanup and decommissioning

No temporary Azure resource is created. Repository cleanup is limited to removing the design branch after merge or closure according to normal Git practice. The generated synthetic fixture remains a regression asset inside the validator. Raw runtime evidence must never be substituted for it in the repository.

## Evidence to capture

For this increment, retain:

- the exact branch and commit SHA;
- the changed-file list;
- validator output;
- focused negative-test results;
- complete exact-head CI job and step outcomes;
- evidence-quality review disposition;
- the merge or closure decision.

Do not label any of those artifacts as guest health, Azure preflight, snapshot recoverability, Trusted Launch bootability, rollback success, or current cost evidence.

## Remaining blockers

- no runtime collector emits these records;
- no active workflow consumes the bundle;
- no current guest or Azure evidence exists under the new schemas;
- no recovery or rollback has been operationally tested;
- identity, network path, protected storage, and retention implementation remain unbuilt;
- independent evidence-quality and security-and-identity review remain required before promotion.
