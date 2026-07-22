# Collector recovery evidence schemas

## Status

This document defines a repository-only, design-time evidence contract for a future
ServiceTracer collector recovery operation.

It does not implement evidence collection commands, activate a GitHub Actions
workflow, authenticate to Azure, mutate resources, or establish that recovery is
operationally possible.

Canonical boundary:

```text
evidence schema implemented
!= evidence collected
!= command authorized
!= Azure mutation performed
!= rollback verified
!= recovery accepted
```

## Purpose

The replacement execution contract defines what a safe recovery procedure must do.
This evidence contract defines what must be recorded before any later system can
claim that a phase was observed, attempted, failed, aborted, rolled back, cleaned
up, or accepted.

The contract is stored at:

- `infra/recovery/collector-recovery-evidence-contract.json`

The deterministic validator is split across:

- `infra/recovery/recovery_evidence_core.py`;
- `infra/recovery/validate_recovery_evidence.py`.

The negative and positive regression tests are:

- `infra/tests/test_collector_recovery_evidence.py`

## Evidence package model

A package uses schema version
`servicetracer.collector-recovery-evidence.v1`.

Every package must contain:

- a unique package identifier;
- an RFC 3339 UTC generation timestamp;
- one maintenance correlation identifier;
- exact target names and complete Azure resource IDs;
- an explicit list of declared evidence phases;
- a package status;
- bounded evidence records;
- explicit operational claims;
- a claim-boundary statement.

The validator rejects unknown top-level and record fields. This prevents evidence
producers from silently attaching arbitrary data or expanding the trust boundary.

## Common record envelope

Every record requires:

- `record_id`;
- `record_type`;
- `phase_id`;
- `observed_at`;
- a logical `command_identity`;
- numeric `exit_status`;
- bounded `status`;
- exact `target_resource_id`;
- `before_state`;
- `after_state`;
- `evidence_sha256`;
- a short summary;
- bounded structured details;
- explicit redaction metadata.

`command_identity` is a logical identifier such as
`guest.preflight.collect`, not a raw shell command. Raw stdout and stderr are not
part of the v1 package contract.

## Record types

The contract recognizes:

- `guest_preflight`;
- `azure_control_plane_preflight`;
- `operation_attempt`;
- `state_observation`;
- `consistency_checkpoint`;
- `integrity_verification`;
- `cleanup_commitment`;
- `cleanup_verification`;
- `decision`.

A record type alone does not prove a phase. Each declared phase has an exact set of
required record types.

## Completeness semantics

Completeness is computed against the package's declared phase list.

```text
package_status == complete
requires
all required record types for every declared phase
and
no failed or aborted records
```

An incomplete package may still be valid evidence. The validator returns the
missing record types per phase instead of silently claiming the package is
complete.

This permits bounded preflight packages without pretending that a full recovery
was performed.

## Target identity

The package must preserve complete Azure resource IDs for:

- the collector VM;
- the production NIC;
- the evidence disk;
- the OS disk.

Each resource ID must:

- be a complete Azure resource ID;
- belong to `rg-servicetracer-dev-westus2`;
- end in the canonical resource name;
- remain inside the package's declared target boundary.

Resource IDs are provenance, not credentials, and must not be replaced by a
redaction marker in the internal evidence package.

## Redaction and secret handling

The validator recursively inspects `before_state`, `after_state`, and `details`.

It rejects:

- secret-like field names;
- common credential prefixes;
- unsupported nested values;
- excessive object or list sizes;
- excessive nesting depth;
- oversized text;
- unknown record fields;
- raw output fields outside the contract.

The `[REDACTED]` marker is allowed only when the record contains corresponding
redaction metadata with:

- the structured field path;
- the exact marker;
- a SHA-256 digest of the original value.

This preserves evidence that a value existed and was deliberately removed without
moving the secret into the package.

## Failure and abort evidence

A package with status `failed` or `aborted` must include:

- a failed or aborted `operation_attempt`;
- a terminal failed or aborted `decision`.

The terminal decision must record:

- the decision;
- reason;
- authority;
- safest next step;
- whether rollback is required.

The contract explicitly prohibits treating silent retry, unbounded retry, or
automatic authority escalation as valid recovery evidence.

## Cleanup evidence

A cleanup commitment records:

- owner;
- deadline;
- maximum retention;
- approved cost ceiling.

A cleanup verification records:

- removed resource IDs;
- retained resource IDs;
- verification timestamp;
- verifier identity;
- actual temporary cost.

The contract preserves the existing boundaries of 24 hours maximum temporary
retention and CAD 10 hard cost ceiling. This schema does not approve spending or
resource creation.

## Operational claim gates

The package supports four claims:

- snapshot recoverability;
- Trusted Launch bootability;
- rollback;
- recovery.

A claim may be marked `verified` only when:

1. the package is complete;
2. every required phase is declared and complete;
3. the required passing record types exist;
4. a passing human-recovery decision explicitly records `decision = accepted`;
5. no failed or aborted record invalidates the package.

The validator never grants authority. Even a structurally valid package with a
verified claim remains evidence for governed review, not permission to execute a
new operation.

## Deterministic validation

The validator has two entry points:

- `validate_contract()` verifies that the repository contract remains
  design-only and that its authority, phase, claim, redaction, cost, and cleanup
  boundaries have not drifted;
- `validate_evidence_package()` verifies a future evidence package against the
  exact contract.

The CLI can validate the contract alone or a supplied package:

```text
python infra/recovery/validate_recovery_evidence.py
python infra/recovery/validate_recovery_evidence.py --package <path>
```

These commands validate files only. They do not query the guest, Azure, GitHub, or
any runtime system.

## Regression coverage

The tests cover:

- a valid complete preflight package;
- a valid incomplete package with explicit missing evidence;
- rejection of false completeness;
- recursive secret-field rejection;
- credential-prefix rejection;
- logical command identity enforcement;
- target-resource boundary enforcement;
- UTC timestamp enforcement;
- redaction digest requirements;
- nested-size limits;
- duplicate record rejection;
- failed-package terminal-decision requirements;
- claim requirements;
- positive rollback-claim validation using synthetic evidence;
- rejection of unknown record fields.

Synthetic fixtures prove validator behavior only. They are not operational
evidence.

## Current limitations

This increment does not provide:

- guest collection adapters;
- Azure CLI collection adapters;
- evidence signing;
- an append-only evidence store;
- protected-environment approvals;
- Azure authentication;
- execution or rollback automation;
- actual-cost observation;
- snapshot restoration or Trusted Launch proof;
- external reviewer independence.

## Safest next step

After exact-head CI and evidence-quality review, the next bounded increment should
design fake-adapter-backed evidence collection for guest and Azure preflight. It
should remain read-only, use synthetic command responses, and prove that generated
packages satisfy this contract before any live Azure collection is considered.
