#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TARGET_HEAD = "5b5af74d57fb5fd87ece2a34239cc6f29d04b12b"
TARGET_BRANCH = "agent/verify-extension-write-permission-20260725"
TARGET_WORKFLOW = "Verify ServiceTracer demo API extension write permission attempt 2"
TARGET_CI_RUN = 30160681565
EXPECTED_RESOURCE_COUNT = 7

SUCCESS_REQUIRED_FILES = {
    "exact-head-ci.json",
    "resources-before.json",
    "resources-after.json",
    "health-before.json",
    "health-after.json",
    "validation.json",
    "what-if.json",
    "permission-verification.json",
    "summary.json",
    "artifact-manifest.sha256",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_file(root: Path, name: str) -> Path | None:
    matches = [path for path in root.rglob(name) if path.is_file()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"multiple artifact files named {name}: {matches}")
    return None


def _resolve_manifest_path(root: Path, recorded: str) -> Path | None:
    normalized = recorded.lstrip("./")
    candidates = [root / normalized]
    parts = Path(normalized).parts
    if len(parts) > 1:
        candidates.append(root.joinpath(*parts[1:]))
    candidates.append(root / Path(normalized).name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def verify_manifest(root: Path, manifest_path: Path) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for raw in manifest_path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            digest, recorded_path = raw.split(maxsplit=1)
        except ValueError:
            failures.append(f"malformed manifest line: {raw}")
            continue
        target = _resolve_manifest_path(root, recorded_path.lstrip("*"))
        if target is None:
            failures.append(f"manifest target missing: {recorded_path}")
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest:
            failures.append(f"manifest digest mismatch: {recorded_path}")
    return (not failures, failures)


def inspect_recovery(
    run: dict[str, Any], artifact: dict[str, Any], root: Path
) -> dict[str, Any]:
    run_id = int(run["id"])
    if run.get("head_sha") != TARGET_HEAD:
        raise ValueError("target run head SHA mismatch")
    if run.get("head_branch") != TARGET_BRANCH:
        raise ValueError("target run branch mismatch")
    if run.get("event") != "push":
        raise ValueError("target run event is not push")
    if run.get("name") != TARGET_WORKFLOW:
        raise ValueError("target workflow name mismatch")
    if artifact.get("workflow_run", {}).get("id") != run_id:
        raise ValueError("artifact is not bound to the target run")
    expected_artifact_name = (
        f"servicetracer-demo-api-extension-write-verify-only-2-{run_id}"
    )
    if artifact.get("name") != expected_artifact_name:
        raise ValueError("artifact name mismatch")

    available = {path.name for path in root.rglob("*") if path.is_file()}
    missing = sorted(SUCCESS_REQUIRED_FILES - available)
    manifest_path = find_file(root, "artifact-manifest.sha256")
    manifest_verified = False
    manifest_failures: list[str] = []
    if manifest_path:
        manifest_verified, manifest_failures = verify_manifest(root, manifest_path)

    result: dict[str, Any] = {
        "schema_version": "project.pr92-protected-verification-recovery.v1",
        "status": "protected_verification_recovered_permission_unverified",
        "target": {
            "pull_request": 92,
            "workflow_run_id": run_id,
            "workflow_run_url": run.get("html_url"),
            "workflow_name": run.get("name"),
            "event": run.get("event"),
            "head_branch": run.get("head_branch"),
            "head_sha": run.get("head_sha"),
            "run_attempt": run.get("run_attempt"),
            "run_status": run.get("status"),
            "run_conclusion": run.get("conclusion"),
            "created_at": run.get("created_at"),
            "updated_at": run.get("updated_at"),
        },
        "artifact": {
            "id": artifact.get("id"),
            "name": artifact.get("name"),
            "digest": artifact.get("digest"),
            "size_in_bytes": artifact.get("size_in_bytes"),
            "expired": artifact.get("expired"),
        },
        "inspection": {
            "manifest_present": manifest_path is not None,
            "manifest_verified": manifest_verified,
            "manifest_failures": manifest_failures,
            "missing_success_files": missing,
            "available_filenames": sorted(available),
        },
        "effective_extension_write_permission_verified": False,
        "arm_validation_succeeded": False,
        "extension_only_what_if_accepted": False,
        "resource_count_preserved": False,
        "public_health_preserved": False,
        "azure_mutation_performed": False,
        "application_deployment_performed": False,
        "transaction_replay_performed": False,
        "deployment_authorized": False,
        "claim_boundary": (
            "Recovery of a run or artifact does not by itself prove effective permission. "
            "The success claim is promoted only when the completed successful run, manifest, "
            "permission record, resource inventories, and public health evidence agree."
        ),
    }

    success_candidate = (
        run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and not missing
        and manifest_verified
    )
    if not success_candidate:
        return result

    exact_head_ci = read_json(find_file(root, "exact-head-ci.json"))
    permission = read_json(find_file(root, "permission-verification.json"))
    summary = read_json(find_file(root, "summary.json"))
    before = read_json(find_file(root, "resources-before.json"))
    after = read_json(find_file(root, "resources-after.json"))
    health_before = read_json(find_file(root, "health-before.json"))
    health_after = read_json(find_file(root, "health-after.json"))

    ci_ok = (
        exact_head_ci.get("status") == "success"
        and int(exact_head_ci.get("run_id")) == TARGET_CI_RUN
        and exact_head_ci.get("source_head") == TARGET_HEAD
    )
    permission_ok = (
        permission.get("status") == "effective_extension_write_permission_verified"
        and permission.get("effective_extension_write_permission_verified") is True
        and permission.get("arm_validation_succeeded") is True
        and permission.get("extension_only_what_if_accepted") is True
        and permission.get("azure_mutation_performed") is False
        and permission.get("deployment_authorized") is False
    )
    summary_ok = (
        summary.get("status") == "effective_extension_write_permission_verified"
        and summary.get("source_head") == TARGET_HEAD
        and summary.get("arm_validation_succeeded") is True
        and summary.get("extension_only_what_if_accepted") is True
        and summary.get("resource_count_preserved") == EXPECTED_RESOURCE_COUNT
        and summary.get("public_health_preserved") is True
        and summary.get("azure_mutation_performed") is False
        and summary.get("application_deployment_performed") is False
        and summary.get("transaction_replay_performed") is False
        and summary.get("deployment_authorized") is False
    )
    normalized_before = sorted(
        before, key=lambda item: (item.get("type", ""), item.get("name", ""))
    )
    normalized_after = sorted(
        after, key=lambda item: (item.get("type", ""), item.get("name", ""))
    )
    resources_ok = (
        len(before) == EXPECTED_RESOURCE_COUNT
        and normalized_before == normalized_after
    )
    health_ok = (
        health_before.get("status") == "healthy"
        and health_before.get("hosting_model") == "dedicated_vm_subproject"
        and health_after.get("status") == "healthy"
        and health_after.get("hosting_model") == "dedicated_vm_subproject"
    )

    if not all((ci_ok, permission_ok, summary_ok, resources_ok, health_ok)):
        result["inspection"]["success_checks"] = {
            "exact_head_ci": ci_ok,
            "permission_record": permission_ok,
            "summary_record": summary_ok,
            "resource_inventory": resources_ok,
            "public_health": health_ok,
        }
        return result

    result.update(
        {
            "status": "effective_extension_write_permission_verified",
            "effective_extension_write_permission_verified": True,
            "arm_validation_succeeded": True,
            "extension_only_what_if_accepted": True,
            "resource_count_preserved": True,
            "public_health_preserved": True,
            "inspection": {
                **result["inspection"],
                "success_checks": {
                    "exact_head_ci": True,
                    "permission_record": True,
                    "summary_record": True,
                    "resource_inventory": True,
                    "public_health": True,
                },
            },
            "claim_boundary": (
                "The recovered protected run proves that the dedicated target identity could "
                "authorize the proposed VM extension write through successful ARM validation "
                "and an accepted extension-only What-If. No Azure mutation or deployment was "
                "performed or authorized."
            ),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-json", type=Path, required=True)
    parser.add_argument("--artifact-json", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = inspect_recovery(
        read_json(args.run_json),
        read_json(args.artifact_json),
        args.artifact_dir,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
