#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "servicetracer.resource-group-boundary-cleanup.v1"
EVIDENCE_SCHEMA = "servicetracer.resource-group-cleanup-evidence.v1"
ASSESSMENT_SCHEMA = "servicetracer.resource-group-cleanup-assessment.v1"
CORE_RG = "rg-servicetracer-dev-westus2"
INDEPENDENT_RG = "rg-st-demo-api-dev-westus2"

CANDIDATES = [
    {"candidate_id": "legacy-app-insights", "name": "appi-demo-api-mst-dev", "type": "microsoft.insights/components"},
    {"candidate_id": "legacy-storage-account", "name": "storfxczr3fewce", "type": "microsoft.storage/storageaccounts"},
    {"candidate_id": "collector-demo-public-ip", "name": "pip-st-demo-api-mst-dev", "type": "microsoft.network/publicipaddresses"},
    {"candidate_id": "collector-demo-load-balancer", "name": "lb-st-demo-api-mst-dev", "type": "microsoft.network/loadbalancers"},
    {"candidate_id": "collector-demo-http-rule", "name": "Allow-Demo-API-HTTP-From-Internet", "type": "microsoft.network/networksecuritygroups/securityrules"},
    {"candidate_id": "collector-demo-https-rule", "name": "Allow-Demo-API-HTTPS-From-Internet", "type": "microsoft.network/networksecuritygroups/securityrules"},
    {"candidate_id": "collector-demo-vm-extension", "name": "servicetracer-demo-api", "type": "microsoft.compute/virtualmachines/extensions"},
]


class CleanupError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CleanupError(message)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def az_json(args: list[str], *, allow_failure: bool = False) -> tuple[bool, Any, str]:
    result = subprocess.run(["az", *args, "--only-show-errors", "--output", "json"], text=True, capture_output=True, check=False)
    if result.returncode:
        error = " ".join(result.stderr.split())[:1000]
        if allow_failure:
            return False, None, error
        raise CleanupError(error or f"Azure CLI failed with exit code {result.returncode}")
    return True, json.loads(result.stdout or "null"), ""


def validate_contract(path: Path) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    require(contract.get("schema_version") == CONTRACT_SCHEMA, "unexpected cleanup contract schema")
    authority = contract.get("authority") or {}
    for key in ("azure_resource_delete_authorized", "azure_resource_move_authorized", "azure_resource_update_authorized", "iac_declaration_removal_authorized"):
        require(authority.get(key) is False, f"{key} must remain false")
    model = contract.get("resource_group_model") or {}
    require(model.get("relationship") == "peer_operational_boundaries_not_nested_layers", "resource groups must remain peer boundaries")
    require((model.get("independent_demo_api") or {}).get("protected_from_this_cleanup") is True, "independent RG must be protected")
    exact = contract.get("exact_cleanup_candidates") or []
    observed = {(str(item.get("name")), str(item.get("type", "")).lower()) for item in exact}
    expected = {(item["name"], item["type"]) for item in CANDIDATES}
    require(observed == expected, "cleanup candidate allowlist changed")
    return contract


def normalize_records(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict) and isinstance(raw.get("data"), list):
        raw = raw["data"]
    require(isinstance(raw, list), "Resource Graph result must be an array or contain data[]")
    records: list[dict[str, Any]] = []
    for item in raw:
        require(isinstance(item, dict), "Resource Graph rows must be objects")
        record = dict(item)
        for field in ("id", "type", "resourceGroup", "referencedPublicIpId"):
            if isinstance(record.get(field), str):
                record[field] = record[field].lower()
        records.append(record)
    return records


def candidate_matches(record: dict[str, Any], candidate: dict[str, str]) -> bool:
    name = str(record.get("name", "")).split("/")[-1]
    return name.lower() == candidate["name"].lower() and str(record.get("type", "")).lower() == candidate["type"]


def assess(payload: dict[str, Any]) -> dict[str, Any]:
    require(payload.get("schema_version") == EVIDENCE_SCHEMA, "unexpected evidence schema")
    metadata = payload.get("metadata") or {}
    require(metadata.get("query_complete") is True, "query_result_truncated_without_continuation_evidence")
    require(isinstance(metadata.get("subscription_id_sha256"), str), "subscription hash is required")
    require(metadata.get("resource_groups") == [CORE_RG, INDEPENDENT_RG], "resource-group scope mismatch")
    records = normalize_records(payload.get("resource_graph_records"))
    deployments = payload.get("deployment_records")
    require(isinstance(deployments, list), "deployment_records must be an array")

    protected = [r for r in records if str(r.get("recordKind", "")).lower() == "candidate" and str(r.get("resourceGroup", "")).lower() == INDEPENDENT_RG]
    require(not protected, "independent demo API resources cannot be cleanup candidates")

    public_ip_ids = {str(r.get("id", "")).lower() for r in records if candidate_matches(r, CANDIDATES[2])}
    public_ip_refs = [r for r in records if str(r.get("recordKind", "")).lower() == "public_ip_reference" and str(r.get("referencedPublicIpId", "")).lower() in public_ip_ids]
    tag_refs = [r for r in records if str(r.get("recordKind", "")).lower() == "tag_reference"]

    results: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        matches = [r for r in records if candidate_matches(r, candidate)]
        if not matches:
            results.append({
                **candidate,
                "observation_status": "not_observed",
                "dependency_status": "not_observed",
                "cleanup_readiness": "not_determined",
                "limitations": ["The bounded query did not return this exact candidate; absence is not established."],
            })
            continue

        blockers: list[str] = []
        limitations: list[str] = []
        if candidate["candidate_id"] == "collector-demo-public-ip" and public_ip_refs:
            blockers.append("public_ip_has_observed_attachment_reference")
        if candidate["candidate_id"] in {"legacy-app-insights", "legacy-storage-account"}:
            limitations.append("ARG cannot prove application-level or guest-level usage; deployment and runtime review remain required.")
        if candidate["candidate_id"] in {"collector-demo-load-balancer", "collector-demo-http-rule", "collector-demo-https-rule", "collector-demo-vm-extension"}:
            blockers.append("historical_collector_hosted_component_still_observed")
        if any(candidate["name"].lower() in json.dumps(r.get("tags") or {}, sort_keys=True).lower() for r in tag_refs):
            blockers.append("tag_reference_observed")

        results.append({
            **candidate,
            "observation_status": "observed",
            "observed_records": matches,
            "dependency_status": "blocked" if blockers else "no_bounded_dependency_observed",
            "blockers": sorted(set(blockers)),
            "limitations": limitations or ["No bounded dependency was observed; this does not prove the resource is orphaned."],
            "cleanup_readiness": "blocked" if blockers else "requires_what_if_and_human_authorization",
        })

    return {
        "schema_version": ASSESSMENT_SCHEMA,
        "observed_at_utc": metadata.get("observed_at_utc"),
        "source_commit": metadata.get("source_commit"),
        "subscription_id_sha256": metadata.get("subscription_id_sha256"),
        "resource_group_model": "peer_operational_boundaries_not_nested_layers",
        "protected_resource_group": INDEPENDENT_RG,
        "candidate_results": results,
        "deployment_records": deployments,
        "summary": {
            "observed_candidates": sum(r["observation_status"] == "observed" for r in results),
            "not_observed_candidates": sum(r["observation_status"] == "not_observed" for r in results),
            "blocked_candidates": sum(r["cleanup_readiness"] == "blocked" for r in results),
            "deletion_authorized": False,
            "move_authorized": False,
            "iac_declaration_removal_authorized": False,
        },
        "canonical_distinctions": [
            "candidate_observed != orphaned",
            "no_bounded_dependency_observed != no_dependency_exists",
            "not_observed != absent",
            "cleanup_assessed != cleanup_authorized",
        ],
    }


def collect(args: argparse.Namespace) -> dict[str, Any]:
    require(args.subscription_id, "--subscription-id is required for collection")
    query_path = Path(args.query).resolve()
    require(query_path.is_file(), "cleanup dependency query is missing")
    query_text = query_path.read_text(encoding="utf-8")
    require(CORE_RG in query_text and INDEPENDENT_RG in query_text, "query scope markers missing")

    ok, account, error = az_json(["account", "show", "--subscription", args.subscription_id], allow_failure=True)
    require(ok, f"Azure account observation failed: {error}")
    require(str(account.get("id", "")).lower() == args.subscription_id.lower(), "authenticated subscription mismatch")
    ok, extension, _ = az_json(["extension", "show", "--name", "resource-graph"], allow_failure=True)
    require(ok and extension, "Azure Resource Graph CLI extension must already be installed; the collector will not install it")

    _, graph_result, _ = az_json(["graph", "query", "--subscriptions", args.subscription_id, "-q", query_text, "--first", "1000"])
    ok, deployments, dep_error = az_json([
        "deployment", "group", "list", "--resource-group", CORE_RG, "--subscription", args.subscription_id,
        "--query", "[?contains(name, 'demo')].{name:name,provisioningState:properties.provisioningState,timestamp:properties.timestamp,correlationId:properties.correlationId}",
    ], allow_failure=True)
    if not ok:
        deployments = [{"observation_status": "observation_failed", "error": dep_error, "claim_boundary": "Deployment history remains not_observed; failure is not absence."}]

    return {
        "schema_version": EVIDENCE_SCHEMA,
        "metadata": {
            "observed_at_utc": now(),
            "source_commit": args.source_commit,
            "subscription_id_sha256": hashlib.sha256(args.subscription_id.encode()).hexdigest(),
            "tenant_id_sha256": hashlib.sha256(str(account.get("tenantId", "")).encode()).hexdigest(),
            "resource_groups": [CORE_RG, INDEPENDENT_RG],
            "query_complete": True,
            "azure_authentication_performed": True,
            "azure_control_plane_queried": True,
            "azure_mutations_authorized": False,
            "azure_mutations_performed": False,
            "cleanup_authorized": False,
        },
        "resource_graph_records": normalize_records(graph_result),
        "deployment_records": deployments,
        "claim_boundary": "This evidence supports dependency assessment only. It does not authorize move, update, delete, redeployment, or IaC declaration removal.",
    }


def write_package(workdir: Path, evidence: dict[str, Any], assessment: dict[str, Any]) -> None:
    evidence_dir = workdir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=False)
    os.chmod(workdir, 0o700)
    os.chmod(evidence_dir, 0o700)
    write_json(evidence_dir / "cleanup-dependency-evidence.json", evidence)
    write_json(evidence_dir / "cleanup-assessment.json", assessment)
    manifest = []
    for path in sorted(evidence_dir.glob("*.json")):
        manifest.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(evidence_dir / "manifest.json", {"files": manifest})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default=".project/contracts/servicetracer-resource-group-boundary-cleanup.json")
    parser.add_argument("--query", default="queries/azure-resource-graph/servicetracer-cleanup-dependencies.kql")
    parser.add_argument("--validate-contract-only", action="store_true")
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--subscription-id")
    parser.add_argument("--source-commit")
    parser.add_argument("--workdir")
    args = parser.parse_args()
    try:
        validate_contract(Path(args.contract))
        if args.validate_contract_only:
            print("ServiceTracer resource-group cleanup contract: valid")
            return 0
        if args.collect:
            require(args.source_commit, "--source-commit is required for collection")
            require(args.workdir, "--workdir is required for collection")
            evidence = collect(args)
            assessment = assess(evidence)
            workdir = Path(args.workdir).expanduser().resolve()
            write_package(workdir, evidence, assessment)
            print(json.dumps(assessment["summary"], indent=2))
            print(f"Evidence directory: {workdir / 'evidence'}")
            print("STOP: no Azure move, update, delete, deployment, guest command, or cleanup operation was run.")
            return 0
        require(args.input and args.output, "--input and --output are required unless --collect or --validate-contract-only is used")
        assessment = assess(json.loads(Path(args.input).read_text(encoding="utf-8")))
        write_json(Path(args.output), assessment)
        print(json.dumps(assessment["summary"], indent=2))
        return 0
    except (CleanupError, json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
