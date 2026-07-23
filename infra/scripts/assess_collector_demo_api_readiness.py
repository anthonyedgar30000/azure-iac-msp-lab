from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
from typing import Any


PUBLIC_IP_QUOTA_NAMES = {"publicipaddress", "publicipaddresses"}
REQUIRED_COLLECTOR_PARAMETERS = {
    "adminUsername",
    "dataDiskSizeGb",
    "collectorPort",
    "collectorSourceRepository",
    "collectorSourceRef",
}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid JSON evidence {path}: {exc}") from exc


def _normalized_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _parse_nonnegative_count(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None

    if isinstance(value, int):
        return value if value >= 0 else None

    if isinstance(value, float):
        if not math.isfinite(value) or value < 0 or not value.is_integer():
            return None
        return int(value)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = Decimal(text)
        except InvalidOperation:
            return None
        if not parsed.is_finite() or parsed < 0 or parsed != parsed.to_integral_value():
            return None
        return int(parsed)

    return None


def _find_public_ip_quota(network_usage: Any) -> dict[str, Any] | None:
    if not isinstance(network_usage, list):
        return None

    matches: list[dict[str, Any]] = []
    for item in network_usage:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, dict):
            continue
        candidates = {
            _normalized_name(name.get("value")),
            _normalized_name(name.get("localizedValue")),
        }
        if candidates & PUBLIC_IP_QUOTA_NAMES:
            matches.append(item)

    return matches[0] if len(matches) == 1 else None


def assess_collector_demo_api_readiness(
    *,
    collector_vm: Any,
    collector_nic: Any,
    collector_module_deployment: Any,
    network_usage: Any,
    resource_locks: Any,
    demo_api_public_ip_state: Any,
    prior_demo_api_resources: Any,
    dns_label: str,
    location: str,
    expected_private_ip: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    limitations: list[str] = []

    vm = collector_vm if isinstance(collector_vm, dict) else {}
    nic = collector_nic if isinstance(collector_nic, dict) else {}
    module = collector_module_deployment if isinstance(collector_module_deployment, dict) else {}
    locks = resource_locks if isinstance(resource_locks, list) else []
    pip_state = demo_api_public_ip_state if isinstance(demo_api_public_ip_state, dict) else {}
    prior = prior_demo_api_resources if isinstance(prior_demo_api_resources, list) else []

    if vm.get("provisioningState") != "Succeeded":
        blockers.append("collector_vm_not_succeeded")
    if vm.get("powerState") not in {"VM running", "VM deallocated"}:
        blockers.append("collector_vm_power_state_unexpected")

    configs = nic.get("ipConfigurations") or []
    if not isinstance(configs, list) or len(configs) != 1:
        blockers.append("collector_nic_primary_configuration_ambiguous")
        private_ip = None
    else:
        private_ip = configs[0].get("privateIPAddress") if isinstance(configs[0], dict) else None
    if private_ip != expected_private_ip:
        blockers.append("collector_private_ip_drift")

    parameters = module.get("properties", {}).get("parameters", {})
    if not isinstance(parameters, dict):
        parameters = {}
    missing = sorted(
        name
        for name in REQUIRED_COLLECTOR_PARAMETERS
        if not isinstance(parameters.get(name), dict) or parameters[name].get("value") in (None, "")
    )
    if missing:
        blockers.append("collector_module_parameters_missing:" + ",".join(missing))

    if any(
        isinstance(item, dict) and str(item.get("level") or "").lower() == "readonly"
        for item in locks
    ):
        blockers.append("resource_group_read_only_lock_present")

    quota_evidence: dict[str, Any]
    if pip_state.get("status") == "observed_existing":
        quota_evidence = {
            "status": "not_required_existing_public_ip",
            "required_additional": 0,
            "sufficient": True,
        }
    else:
        quota = _find_public_ip_quota(network_usage)
        if quota is None:
            blockers.append("public_ip_quota_not_observable")
            quota_evidence = {
                "status": "not_observable",
                "required_additional": 1,
                "sufficient": False,
            }
        else:
            current_raw = quota.get("currentValue")
            limit_raw = quota.get("limit")
            current = _parse_nonnegative_count(current_raw)
            limit = _parse_nonnegative_count(limit_raw)
            quota_evidence = {
                "status": "observed",
                "name": quota.get("name"),
                "unit": quota.get("unit"),
                "current_raw": current_raw,
                "current_raw_type": _json_type(current_raw),
                "limit_raw": limit_raw,
                "limit_raw_type": _json_type(limit_raw),
                "current": current,
                "limit": limit,
                "required_additional": 1,
                "remaining": None if current is None or limit is None else limit - current,
                "sufficient": False,
            }
            if current is None or limit is None or limit < current:
                blockers.append("public_ip_quota_invalid")
                quota_evidence["status"] = "invalid"
            elif limit - current < 1:
                blockers.append("public_ip_quota_insufficient")
                quota_evidence["status"] = "insufficient"
            else:
                quota_evidence["status"] = "sufficient"
                quota_evidence["sufficient"] = True

    if prior:
        limitations.append("previous_app_service_attempt_left_resources_for_separate_cleanup_review")

    return {
        "schema_version": "servicetracer.collector-demo-api-readiness.v2",
        "collector_vm_name": vm.get("name"),
        "collector_vm_size": vm.get("hardwareProfile", {}).get("vmSize"),
        "collector_private_ip": private_ip,
        "dns_label": dns_label,
        "location": location,
        "public_ip_quota": quota_evidence,
        "blockers": blockers,
        "limitations": limitations,
        "deployment_decision_ready": not blockers,
        "microsoft_web_required": False,
        "deployment_authorized": False,
        "azure_mutations_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assess the collector-hosted demo API against current Azure evidence"
    )
    parser.add_argument("--collector-vm", required=True)
    parser.add_argument("--collector-nic", required=True)
    parser.add_argument("--collector-module-deployment", required=True)
    parser.add_argument("--network-usage", required=True)
    parser.add_argument("--resource-locks", required=True)
    parser.add_argument("--demo-api-public-ip-state", required=True)
    parser.add_argument("--prior-demo-api-resources", required=True)
    parser.add_argument("--dns-label", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--expected-private-ip", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    assessment = assess_collector_demo_api_readiness(
        collector_vm=_load_json(Path(args.collector_vm)),
        collector_nic=_load_json(Path(args.collector_nic)),
        collector_module_deployment=_load_json(Path(args.collector_module_deployment)),
        network_usage=_load_json(Path(args.network_usage)),
        resource_locks=_load_json(Path(args.resource_locks)),
        demo_api_public_ip_state=_load_json(Path(args.demo_api_public_ip_state)),
        prior_demo_api_resources=_load_json(Path(args.prior_demo_api_resources)),
        dns_label=args.dns_label,
        location=args.location,
        expected_private_ip=args.expected_private_ip,
    )
    output = Path(args.output)
    output.write_text(json.dumps(assessment, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if assessment["blockers"]:
        raise SystemExit(
            "Collector demo API readiness blockers: " + ", ".join(assessment["blockers"])
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
