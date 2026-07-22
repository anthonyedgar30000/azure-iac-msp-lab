# Collector recovery evidence schemas

## Status

This is a repository-only, design-time evidence contract for a future ServiceTracer collector recovery operation.

It does not implement collection commands, activate a GitHub Actions workflow, authenticate to Azure, mutate resources, approve spending, or prove that recovery is operationally possible.

```text
evidence schema implemented
!= evidence collected
!= command authorized
!= Azure mutation performed
!= rollback verified
!= recovery accepted
```

PR #32 merged the first version into `main`, but its exact-head evidence-quality review recorded **CHANGES REQUIRED**. PR #34 is the bounded remediation increment for those findings. Merge state is therefore not treated as review acceptance.

## Authoritative files

- `infra/recovery/collector-recovery-evidence-contract.json`
- `infra/recovery/recovery_evidence_core.py`
- `infra/recovery/validate_recovery_evidence.py`
- `infra/tests/test_collector_recovery_evidence.py`

The package schema version remains `servicetracer.collector-recovery-evidence.v1`.

## Pinned v1 semantics

`validate_contract()` pins the values consumed later by `validate_evidence_package()` rather than merely checking that they are syntactically valid.

Pinned values include:

- package, record, claim, and record-type enumerations;
- maintenance, record, command, and SHA-256 patterns;
- phase requirements and claim requirements;
- secret-field fragments and forbidden credential prefixes;
- record-detail requirements;
- cleanup and failure requirements;
- prohibited failure behaviour;
- supersession rules;
- package size and nesting ceilings.

A contract edit cannot silently weaken one of these values while continuing to pass contract validation.

## Package model

Every package requires:

- a package identifier;
- an RFC 3339 UTC generation timestamp;
- one maintenance correlation identifier;
- exact target names and complete Azure resource IDs;
- declared phase identifiers;
- package status;
- explicit supersession state;
- bounded evidence records;
- explicit operational claims;
- a claim-boundary statement.

Unknown top-level and record fields are rejected.

## Common record envelope

Every record requires:

- `record_id`;
- `record_type`;
- `phase_id`;
- `observed_at`;
- logical `command_identity`;
- numeric `exit_status`;
- bounded `status`;
- exact `target_resource_id`;
- `before_state` and `after_state`;
- `evidence_sha256`;
- summary;
- typed evidence-bearing `details`;
- explicit redaction provenance.

`command_identity` is a logical identifier such as `guest.preflight.collect`, not a raw shell command. Raw stdout and stderr are outside the v1 package.

## Required record details

A record type is not accepted merely because its name is present. Each type has minimum evidence-bearing detail fields:

- `guest_preflight`: service state, health status, evidence mount, filesystem UUID, and recent-evidence readability;
- `azure_control_plane_preflight`: VM power state, NIC delete option, evidence-disk delete option, OS-disk public-network-access state, and observed role assignments;
- `operation_attempt`: operation, requester, and authorization reference;
- `state_observation`: observed state and source;
- `consistency_checkpoint`: checkpoint name, consistency decision, and evidence references;
- `integrity_verification`: verification name, result, and checks;
- `cleanup_commitment`: owner, deadline, retention ceiling, and approved cost ceiling;
- `cleanup_verification`: removed and retained resource IDs, verification time, verifier identity, and actual temporary cost;
- `decision`: decision, reason, authority, safest next step, and rollback requirement.

Type-specific validation also enforces timestamps, booleans, bounded retention, finite costs, and the CAD 10 hard ceiling.

## Target identity and subscription boundary

The package preserves complete Azure resource IDs for the collector VM, production NIC, evidence disk, and OS disk.

Each ID must:

- be a complete Azure resource ID;
- belong to `rg-servicetracer-dev-westus2`;
- end in its canonical resource name;
- be distinct from the other target IDs;
- share the same subscription identifier.

This prevents a plausible-looking package from combining resources across subscriptions.

Resource IDs are provenance, not credentials, and remain inside the protected evidence package.

## Redaction provenance

The validator recursively derives every location whose value is exactly `[REDACTED]` across `before_state`, `after_state`, and `details`.

The `redactions` array must contain exactly one entry for each derived path and no entries for paths that are not redacted. It rejects:

- a missing path;
- a wrong path;
- a path for a nonexistent marker;
- duplicate path metadata;
- a marker without an original-value SHA-256 digest.

Example path syntax:

```text
details.subscription.items[1]
```

Secret-like field names, common credential prefixes, oversized text, excessive nesting, excessive collections, unsupported JSON values, and raw output fields remain fail-closed.

## Canonical numeric handling

JSON packages must be serializable with `allow_nan = false`.

`NaN`, positive infinity, and negative infinity are rejected anywhere in the package. Finite numbers remain subject to type-specific bounds.

## Completeness and claims

Completeness is computed against the declared phases.

```text
package_status == complete
requires
all required record types for every declared phase
and
no failed or aborted records
```

An incomplete package may remain valid evidence, but the validator returns the missing record types and does not overstate completeness.

Verified claims require a complete package, all required phases, required passing record types, and a passing human decision whose `decision` is `accepted`.

The validator always returns:

```text
authority_granted = false
azure_mutations_authorized = false
```

## Failure and abort evidence

A failed or aborted package requires both an `operation_attempt` and a failed or aborted terminal `decision`.

The decision records the reason, authority, safest next step, and whether rollback is required. Silent retry, unbounded retry, automatic authority escalation, recovery claims without post-change verification, and premature deletion of recovery artifacts remain prohibited.

## Supersession provenance

Every package contains a `supersession` field.

- For statuses other than `superseded`, the field must be `null`.
- A superseded package must identify the prior package, state a bounded reason, and bind the superseding evidence with SHA-256.
- A package cannot supersede itself.
- A superseded package cannot retain a verified operational claim.

This prevents a stale package from disappearing behind an unexplained status change.

## Cleanup and cost boundary

Cleanup commitment and verification details are now actively validated rather than merely documented.

The contract preserves:

- 24-hour maximum temporary-resource retention;
- CAD 10 maximum approved temporary cost;
- finite numeric cost values;
- explicit cleanup owner, deadline, verifier, and removed/retained resource identities.

These constraints do not authorize resource creation or spending.

## Deterministic validation

```text
python infra/recovery/validate_recovery_evidence.py
python infra/recovery/validate_recovery_evidence.py --package <path>
python -m unittest discover -s infra/tests -v
```

Before PR #34 was opened, isolated local validation produced:

```text
contract-only validation: passed
recovery-evidence tests: 32 passed
```

Local tests are not GitHub CI. The exact final PR head must pass all configured CI jobs and then receive a fresh evidence-quality review.

## Current Azure evidence boundary

This remediation does not connect to Azure. The latest repository-promoted Azure evidence remains read-only planner run `29856203054`, observed July 21, 2026.

It does not prove current tenant or subscription context, resource state, quota, pricing, actual cost, RBAC effectiveness, guest health, snapshot recoverability, Trusted Launch bootability, rollback, or recovery.

## Current limitations

This increment does not provide guest or Azure collection adapters, evidence signing, append-only storage, protected-environment approvals, Azure authentication, mutation automation, actual-cost observation, restoration testing, or independent organizational review.

The next safe step after an accepted PR #34 is another repository-only design increment for fake-adapter-backed read-only collection. Live collection and Azure mutation remain separately authorized operations.
