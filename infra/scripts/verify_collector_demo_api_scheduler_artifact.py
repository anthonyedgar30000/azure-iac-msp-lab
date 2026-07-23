from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "request.json",
    "evidence-manifest.json",
    "readiness-assessment.json",
    "arm-validation.json",
    "arm-what-if.json",
    "what-if-assessment.json",
    "sha256sums.txt",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid JSON evidence {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"Evidence file must contain a JSON object: {path}")
    return payload


def verify_sha256sums(directory: Path) -> int:
    sums_path = directory / "sha256sums.txt"
    if not sums_path.is_file():
        raise SystemExit("Artifact is missing sha256sums.txt")

    verified = 0
    seen: set[str] = set()
    for raw_line in sums_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            expected, recorded_path = line.split(maxsplit=1)
        except ValueError as exc:
            raise SystemExit(f"Invalid SHA-256 manifest line: {raw_line!r}") from exc
        if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected.lower()):
            raise SystemExit(f"Invalid SHA-256 digest in manifest: {expected}")
        basename = Path(recorded_path.lstrip("* ")).name
        if basename == "sha256sums.txt":
            raise SystemExit("sha256sums.txt must not hash itself")
        if basename in seen:
            raise SystemExit(f"Duplicate basename in SHA-256 manifest: {basename}")
        seen.add(basename)
        candidate = directory / basename
        if not candidate.is_file():
            raise SystemExit(f"Manifest file is missing after artifact extraction: {basename}")
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual.lower() != expected.lower():
            raise SystemExit(f"SHA-256 mismatch for {basename}")
        verified += 1

    if verified < 6:
        raise SystemExit(f"Artifact manifest verified only {verified} files")
    return verified


def verify_artifact(
    directory: Path,
    *,
    expected_run_id: str,
    expected_commit: str,
    expected_resource_group: str,
    expected_location: str,
    expected_environment: str,
    expected_prefix: str,
    expected_dns_label: str,
    expected_allowed_origin: str,
) -> dict[str, Any]:
    missing = sorted(name for name in REQUIRED_FILES if not (directory / name).is_file())
    if missing:
        raise SystemExit("Artifact is missing required files: " + ", ".join(missing))

    verified_files = verify_sha256sums(directory)
    request = _load_json(directory / "request.json")
    manifest = _load_json(directory / "evidence-manifest.json")
    readiness = _load_json(directory / "readiness-assessment.json")
    validation = _load_json(directory / "arm-validation.json")
    what_if = _load_json(directory / "what-if-assessment.json")

    if manifest.get("schema_version") != "servicetracer.collector-demo-api-evidence.v1":
        raise SystemExit("Unexpected workflow evidence-manifest schema")
    if str(manifest.get("run_id")) != expected_run_id:
        raise SystemExit("Evidence manifest run ID differs from the scheduler-selected run")
    if manifest.get("reviewed_commit") != expected_commit:
        raise SystemExit("Evidence manifest commit differs from the scheduler pin")
    if manifest.get("operation") != "what-if":
        raise SystemExit("Evidence manifest does not describe a read-only What-If")

    expected_request = {
        "schema_version": "servicetracer.collector-demo-api-request.v2",
        "operation": "what-if",
        "reviewed_commit": expected_commit,
        "resource_group": expected_resource_group,
        "location": expected_location,
        "environment": expected_environment,
        "prefix": expected_prefix,
        "dns_label": expected_dns_label,
        "allowed_origin": expected_allowed_origin,
        "azure_authentication_authorized": True,
        "azure_mutations_authorized": False,
        "collector_configuration_mutation_authorized": False,
        "base_infrastructure_mutation_authorized": False,
        "microsoft_web_authorized": False,
    }
    for name, expected in expected_request.items():
        if request.get(name) != expected:
            raise SystemExit(f"Bounded request field {name} differs from the scheduler contract")

    if readiness.get("schema_version") != "servicetracer.collector-demo-api-readiness.v2":
        raise SystemExit("Unexpected readiness schema")
    blockers = readiness.get("blockers")
    if blockers != []:
        raise SystemExit("Current Azure readiness contains blockers")
    if readiness.get("deployment_decision_ready") is not True:
        raise SystemExit("Current Azure readiness is not decision-ready")
    quota = readiness.get("public_ip_quota")
    if not isinstance(quota, dict) or quota.get("sufficient") is not True:
        raise SystemExit("Public-IP quota is not proven sufficient")
    if readiness.get("deployment_authorized") is not False:
        raise SystemExit("Readiness evidence unexpectedly authorizes deployment")
    if readiness.get("azure_mutations_performed") is not False:
        raise SystemExit("Readiness evidence unexpectedly records Azure mutation")

    if validation.get("properties", {}).get("provisioningState") != "Succeeded":
        raise SystemExit("ARM validation did not succeed")

    expected_what_if = {
        "schema_version": "servicetracer.collector-demo-api-what-if.v2",
        "status": "accepted_isolated_collector_api_changes",
        "collector_nic_modifications": [],
        "collector_vm_modifications": [],
        "base_infrastructure_modifications": [],
        "forbidden_changes": [],
        "managed_web_resources_proposed": False,
        "deployment_authorized": False,
        "azure_mutations_performed": False,
    }
    for name, expected in expected_what_if.items():
        if what_if.get(name) != expected:
            raise SystemExit(f"What-If assessment field {name} differs from the accepted isolated contract")
    creates = what_if.get("creates")
    if isinstance(creates, bool) or not isinstance(creates, int) or creates < 0:
        raise SystemExit("What-If assessment has an invalid Create count")

    return {
        "schema_version": "servicetracer.collector-demo-api-scheduler-verification.v1",
        "status": "verified_read_only_what_if_artifact",
        "run_id": expected_run_id,
        "reviewed_commit": expected_commit,
        "resource_group": expected_resource_group,
        "location": expected_location,
        "environment": expected_environment,
        "prefix": expected_prefix,
        "dns_label": expected_dns_label,
        "allowed_origin": expected_allowed_origin,
        "verified_manifest_files": verified_files,
        "readiness_passed": True,
        "public_ip_quota": quota,
        "what_if_status": what_if["status"],
        "create_count": creates,
        "ignored_managed_leftovers": what_if.get("ignored_managed_leftovers", []),
        "base_infrastructure_modifications": [],
        "azure_mutations_authorized": False,
        "azure_mutations_performed": False,
        "deployment_authorized": False,
        "claim_boundary": (
            "The scheduler verified one exact read-only What-If artifact. "
            "This does not authorize workflow deployment, Azure mutation, cleanup, rollback, or guest commands."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a cron-dispatched collector demo API What-If artifact"
    )
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-resource-group", required=True)
    parser.add_argument("--expected-location", required=True)
    parser.add_argument("--expected-environment", required=True)
    parser.add_argument("--expected-prefix", required=True)
    parser.add_argument("--expected-dns-label", required=True)
    parser.add_argument("--expected-allowed-origin", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = verify_artifact(
        Path(args.artifact_dir),
        expected_run_id=args.expected_run_id,
        expected_commit=args.expected_commit,
        expected_resource_group=args.expected_resource_group,
        expected_location=args.expected_location,
        expected_environment=args.expected_environment,
        expected_prefix=args.expected_prefix,
        expected_dns_label=args.expected_dns_label,
        expected_allowed_origin=args.expected_allowed_origin,
    )
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
