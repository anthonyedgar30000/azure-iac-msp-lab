from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Callable, Mapping, Sequence

from .catalog import CatalogError, load_catalog, prepare_lab_plan


PREFLIGHT_SCHEMA = "lab-factory.azure-preflight.v1"
REQUIRED_PROVIDERS = (
    "Microsoft.Resources",
    "Microsoft.Network",
    "Microsoft.Compute",
)
REQUIRED_DEPLOY_ACTIONS = (
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Resources/subscriptions/resourceGroups/write",
    "Microsoft.Resources/deployments/read",
    "Microsoft.Resources/deployments/write",
    "Microsoft.Resources/deployments/validate/action",
    "Microsoft.Network/networkSecurityGroups/read",
    "Microsoft.Network/networkSecurityGroups/write",
    "Microsoft.Network/virtualNetworks/read",
    "Microsoft.Network/virtualNetworks/write",
    "Microsoft.Network/publicIPAddresses/read",
    "Microsoft.Network/publicIPAddresses/write",
    "Microsoft.Network/networkInterfaces/read",
    "Microsoft.Network/networkInterfaces/write",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/write",
    "Microsoft.Compute/virtualMachines/extensions/read",
    "Microsoft.Compute/virtualMachines/extensions/write",
)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class PreflightError(RuntimeError):
    """Raised when a bounded Azure preflight cannot complete safely."""


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[Sequence[str], int, Path], CommandResult]
PriceFetcher = Callable[[str, str], Mapping[str, Any]]


def default_runner(argv: Sequence[str], timeout_seconds: int, cwd: Path) -> CommandResult:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        shell=False,
    )
    return CommandResult(tuple(argv), completed.returncode, completed.stdout, completed.stderr)


def _sanitize(value: Any, *, limit: int = 512) -> str:
    return _CONTROL_CHARS.sub("", str(value))[:limit]


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _run_json(
    runner: Runner,
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    allow_not_found: bool = False,
) -> Any:
    result = runner(argv, timeout_seconds, cwd)
    if result.returncode != 0:
        stderr = _sanitize(result.stderr)
        if allow_not_found and (
            "ResourceGroupNotFound" in stderr
            or "could not be found" in stderr.lower()
            or "was not found" in stderr.lower()
        ):
            return None
        raise PreflightError(
            f"read-only Azure command failed ({result.returncode}): "
            f"{' '.join(argv[:5])}; {stderr or 'no stderr'}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PreflightError(
            f"Azure command returned invalid JSON: {' '.join(argv[:5])}"
        ) from exc


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _find_named_usage(
    usages: Sequence[Mapping[str, Any]],
    *tokens: str,
) -> Mapping[str, Any] | None:
    normalized_tokens = tuple(_normalize_token(token) for token in tokens if token)
    for usage in usages:
        name = usage.get("name")
        if isinstance(name, Mapping):
            candidate = f"{name.get('value', '')} {name.get('localizedValue', '')}"
        else:
            candidate = str(name or usage.get("localName") or usage.get("name") or "")
        normalized = _normalize_token(candidate)
        if normalized_tokens and all(token in normalized for token in normalized_tokens):
            return usage
    return None


def _usage_summary(
    usage: Mapping[str, Any] | None,
    *,
    required: int,
) -> dict[str, Any]:
    if usage is None:
        return {
            "observation_status": "not_found",
            "current": None,
            "limit": None,
            "required": required,
            "headroom": None,
            "sufficient": False,
        }
    current = usage.get("currentValue", usage.get("current_value"))
    limit = usage.get("limit")
    if not isinstance(current, (int, float)) or not isinstance(limit, (int, float)):
        return {
            "observation_status": "invalid",
            "current": None,
            "limit": None,
            "required": required,
            "headroom": None,
            "sufficient": False,
        }
    headroom = limit - current
    return {
        "observation_status": "observed",
        "current": current,
        "limit": limit,
        "required": required,
        "headroom": headroom,
        "sufficient": headroom >= required,
    }


def _sku_observation(
    skus: Sequence[Mapping[str, Any]],
    *,
    vm_size: str,
    location: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in skus
        if str(item.get("name", "")).lower() == vm_size.lower()
    ]
    if len(matches) != 1:
        return {
            "observation_status": "not_found" if not matches else "ambiguous",
            "vm_size": vm_size,
            "family": None,
            "vcpus": None,
            "location_available": False,
            "blocking_restrictions": [],
            "informational_restrictions": [],
        }
    sku = matches[0]
    capabilities = {
        str(item.get("name", "")): str(item.get("value", ""))
        for item in sku.get("capabilities", [])
        if isinstance(item, Mapping)
    }
    vcpus_text = capabilities.get("vCPUs") or capabilities.get("vCPUsAvailable") or ""
    try:
        vcpus = int(float(vcpus_text))
    except ValueError:
        vcpus = None

    blocking: list[dict[str, Any]] = []
    informational: list[dict[str, Any]] = []
    for raw in sku.get("restrictions", []) or []:
        if not isinstance(raw, Mapping):
            continue
        restriction_type = _sanitize(raw.get("type"), limit=128)
        reason_code = _sanitize(raw.get("reasonCode"), limit=128)
        values = [
            _sanitize(value, limit=128)
            for value in raw.get("values", [])
            if value is not None
        ]
        record = {
            "type": restriction_type,
            "reason_code": reason_code,
            "values": values,
        }
        normalized_values = {value.lower() for value in values}
        if restriction_type.lower() == "location" and location.lower() in normalized_values:
            blocking.append(record)
        elif (
            reason_code.lower() == "notavailableforsubscription"
            and restriction_type.lower() != "zone"
        ):
            blocking.append(record)
        else:
            informational.append(record)

    locations = {str(item).lower() for item in sku.get("locations", []) if item}
    location_available = location.lower() in locations and not blocking
    return {
        "observation_status": "observed",
        "vm_size": vm_size,
        "family": _sanitize(sku.get("family"), limit=128),
        "vcpus": vcpus,
        "location_available": location_available,
        "blocking_restrictions": blocking,
        "informational_restrictions": informational,
    }


def _action_matches(pattern: str, action: str) -> bool:
    return fnmatch.fnmatchcase(action.lower(), pattern.lower())


def _permissions_summary(payload: Any) -> dict[str, Any]:
    records = payload.get("value") if isinstance(payload, Mapping) else payload
    if not isinstance(records, list):
        return {
            "observation_status": "invalid",
            "required_action_count": len(REQUIRED_DEPLOY_ACTIONS),
            "allowed_action_count": 0,
            "missing_actions": list(REQUIRED_DEPLOY_ACTIONS),
            "sufficient_for_candidate_deployment": False,
            "least_privilege_verified": False,
        }

    missing: list[str] = []
    for required in REQUIRED_DEPLOY_ACTIONS:
        allowed = False
        for record in records:
            if not isinstance(record, Mapping):
                continue
            actions = record.get("actions") or []
            not_actions = record.get("notActions") or []
            if any(
                _action_matches(str(pattern), required)
                for pattern in actions
            ) and not any(
                _action_matches(str(pattern), required)
                for pattern in not_actions
            ):
                allowed = True
                break
        if not allowed:
            missing.append(required)

    return {
        "observation_status": "observed",
        "required_action_count": len(REQUIRED_DEPLOY_ACTIONS),
        "allowed_action_count": len(REQUIRED_DEPLOY_ACTIONS) - len(missing),
        "missing_actions": missing,
        "sufficient_for_candidate_deployment": not missing,
        "least_privilege_verified": False,
    }


def _policy_summary(assignments: Any) -> dict[str, Any]:
    if not isinstance(assignments, list):
        return {
            "observation_status": "invalid",
            "assignment_count": None,
            "deny_effect_assignments": None,
            "candidate_policy_compatibility_verified": False,
        }
    deny_effect = 0
    for assignment in assignments:
        if not isinstance(assignment, Mapping):
            continue
        parameters = assignment.get("parameters")
        text = json.dumps(parameters, sort_keys=True) if isinstance(parameters, Mapping) else ""
        if '"deny"' in text.lower():
            deny_effect += 1
    return {
        "observation_status": "observed",
        "assignment_count": len(assignments),
        "deny_effect_assignments": deny_effect,
        "candidate_policy_compatibility_verified": False,
        "boundary": (
            "assignment inventory is context; ARM template validation is the "
            "candidate-specific gate"
        ),
    }


def _cost_summary(
    price: Mapping[str, Any],
    *,
    ttl_hours: int,
    ceiling_cad: float,
) -> dict[str, Any]:
    vm_hourly = price.get("vm_hourly_cad")
    public_ip_hourly = price.get("public_ip_hourly_cad")
    disk_monthly = price.get("disk_monthly_cad")
    if not all(
        isinstance(value, (int, float))
        for value in (vm_hourly, public_ip_hourly, disk_monthly)
    ):
        return {
            "observation_status": "incomplete",
            "currency": "CAD",
            "ttl_hours": ttl_hours,
            "estimated_fixed_cost_cad": None,
            "cost_ceiling_cad": ceiling_cad,
            "ceiling_accepted": False,
            "variable_egress_excluded": True,
        }
    estimate = (
        float(vm_hourly) * ttl_hours
        + float(public_ip_hourly) * ttl_hours
        + float(disk_monthly) * (ttl_hours / 730.0)
    )
    return {
        "observation_status": "observed",
        "currency": "CAD",
        "ttl_hours": ttl_hours,
        "vm_hourly_cad": round(float(vm_hourly), 6),
        "public_ip_hourly_cad": round(float(public_ip_hourly), 6),
        "disk_monthly_cad": round(float(disk_monthly), 6),
        "estimated_fixed_cost_cad": round(estimate, 4),
        "cost_ceiling_cad": round(ceiling_cad, 2),
        "ceiling_accepted": estimate <= ceiling_cad,
        "variable_egress_excluded": True,
        "disk_assumption": "Standard SSD E4 LRS (32 GiB)",
        "retail_price_is_not_actual_billed_cost": True,
    }


def run_lab_preflight(
    *,
    expected_subscription_id: str,
    profile_id: str,
    environment: str,
    ttl_hours: int,
    cost_ceiling_cad: float,
    parameters: Mapping[str, str],
    repository_root: str | Path,
    runner: Runner = default_runner,
    price_fetcher: PriceFetcher,
    timeout_seconds: int = 90,
    now: Callable[[], datetime] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Run a fixed, read-only Azure preflight for one catalog-backed lab request."""

    if not re.fullmatch(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        expected_subscription_id,
    ):
        raise PreflightError("expected_subscription_id must be a UUID")
    if (
        not isinstance(cost_ceiling_cad, (int, float))
        or isinstance(cost_ceiling_cad, bool)
        or cost_ceiling_cad <= 0
    ):
        raise PreflightError("cost_ceiling_cad must be a positive number")

    root = Path(repository_root).resolve()
    catalog = load_catalog(repository_root=root)
    try:
        plan = prepare_lab_plan(
            catalog,
            profile_id=profile_id,
            environment=environment,
            ttl_hours=ttl_hours,
            parameters=parameters,
            request_id=request_id,
            repository_root=root,
        )
    except CatalogError as exc:
        raise PreflightError(str(exc)) from exc
    if plan["next_gate"] != "preflight_required":
        raise PreflightError("lab request is not complete enough for preflight")

    location = plan["request"]["location"]
    resource_group = plan["deployment"]["resource_group"]
    vm_size = parameters.get("vmSize") or "Standard_F1als_v7"
    template_path = (root / plan["deployment"]["template_path"]).resolve()
    if not template_path.is_relative_to(root) or not template_path.is_file():
        raise PreflightError("template path escaped the repository or is missing")

    account = _run_json(
        runner,
        ("az", "account", "show", "--output", "json", "--only-show-errors"),
        cwd=root,
        timeout_seconds=timeout_seconds,
    )
    if not isinstance(account, Mapping):
        raise PreflightError("Azure account context must be an object")
    subscription_id = str(account.get("id", ""))
    tenant_id = str(account.get("tenantId", ""))
    if subscription_id.lower() != expected_subscription_id.lower():
        raise PreflightError("active Azure subscription does not match the exact allowlist")
    if str(account.get("state", "")).lower() != "enabled":
        raise PreflightError("active Azure subscription is not enabled")

    locations = _run_json(
        runner,
        ("az", "account", "list-locations", "--output", "json", "--only-show-errors"),
        cwd=root,
        timeout_seconds=timeout_seconds,
    )
    if not isinstance(locations, list):
        raise PreflightError("location catalog must be an array")
    location_available = any(
        str(item.get("name", "")).lower() == location.lower()
        for item in locations
        if isinstance(item, Mapping)
    )

    provider_states: list[dict[str, Any]] = []
    for namespace in REQUIRED_PROVIDERS:
        provider = _run_json(
            runner,
            (
                "az",
                "provider",
                "show",
                "--namespace",
                namespace,
                "--output",
                "json",
                "--only-show-errors",
            ),
            cwd=root,
            timeout_seconds=timeout_seconds,
        )
        state = _sanitize(
            provider.get("registrationState") if isinstance(provider, Mapping) else None,
            limit=64,
        )
        provider_states.append(
            {
                "namespace": namespace,
                "registration_state": state,
                "registered": state.lower() == "registered",
            }
        )

    skus = _run_json(
        runner,
        (
            "az",
            "vm",
            "list-skus",
            "--location",
            location,
            "--size",
            vm_size,
            "--all",
            "--output",
            "json",
            "--only-show-errors",
        ),
        cwd=root,
        timeout_seconds=timeout_seconds,
    )
    if not isinstance(skus, list):
        raise PreflightError("VM SKU observation must be an array")
    sku = _sku_observation(skus, vm_size=vm_size, location=location)
    required_vcpus = sku.get("vcpus") if isinstance(sku.get("vcpus"), int) else 1

    compute_usages = _run_json(
        runner,
        (
            "az",
            "vm",
            "list-usage",
            "--location",
            location,
            "--output",
            "json",
            "--only-show-errors",
        ),
        cwd=root,
        timeout_seconds=timeout_seconds,
    )
    network_usages = _run_json(
        runner,
        (
            "az",
            "network",
            "list-usages",
            "--location",
            location,
            "--output",
            "json",
            "--only-show-errors",
        ),
        cwd=root,
        timeout_seconds=timeout_seconds,
    )
    if not isinstance(compute_usages, list) or not isinstance(network_usages, list):
        raise PreflightError("quota observations must be arrays")
    regional_quota = _usage_summary(
        _find_named_usage(compute_usages, "total", "regional", "vcpus")
        or _find_named_usage(compute_usages, "cores"),
        required=required_vcpus,
    )
    family_name = str(sku.get("family") or "")
    family_token = family_name.replace("standard", "").replace("family", "")
    family_quota = _usage_summary(
        _find_named_usage(compute_usages, family_token, "vcpus"),
        required=required_vcpus,
    )
    public_ip_quota = _usage_summary(
        _find_named_usage(network_usages, "public", "ip", "standard")
        or _find_named_usage(network_usages, "public", "ip"),
        required=1,
    )

    group = _run_json(
        runner,
        (
            "az",
            "group",
            "show",
            "--name",
            resource_group,
            "--output",
            "json",
            "--only-show-errors",
        ),
        cwd=root,
        timeout_seconds=timeout_seconds,
        allow_not_found=True,
    )
    group_summary: dict[str, Any]
    if group is None:
        group_summary = {
            "observation_status": "not_present",
            "name": resource_group,
            "location": None,
            "resource_count": 0,
            "safe_for_dedicated_lab": True,
        }
    elif isinstance(group, Mapping):
        resources = _run_json(
            runner,
            (
                "az",
                "resource",
                "list",
                "--resource-group",
                resource_group,
                "--output",
                "json",
                "--only-show-errors",
            ),
            cwd=root,
            timeout_seconds=timeout_seconds,
        )
        if not isinstance(resources, list):
            raise PreflightError("resource inventory must be an array")
        observed_location = _sanitize(group.get("location"), limit=64)
        group_summary = {
            "observation_status": "observed",
            "name": resource_group,
            "location": observed_location,
            "resource_count": len(resources),
            "safe_for_dedicated_lab": (
                observed_location.lower() == location.lower() and len(resources) == 0
            ),
        }
    else:
        raise PreflightError("resource-group observation must be an object or not found")

    scope = f"/subscriptions/{subscription_id}"
    permissions = _run_json(
        runner,
        (
            "az",
            "rest",
            "--method",
            "get",
            "--url",
            (
                f"https://management.azure.com{scope}/providers/"
                "Microsoft.Authorization/permissions?api-version=2022-04-01"
            ),
            "--output",
            "json",
            "--only-show-errors",
        ),
        cwd=root,
        timeout_seconds=timeout_seconds,
    )
    permission_summary = _permissions_summary(permissions)

    policies = _run_json(
        runner,
        (
            "az",
            "policy",
            "assignment",
            "list",
            "--scope",
            scope,
            "--disable-scope-strict-match",
            "--output",
            "json",
            "--only-show-errors",
        ),
        cwd=root,
        timeout_seconds=timeout_seconds,
    )
    policy_summary = _policy_summary(policies)

    price = price_fetcher(location, vm_size)
    cost = _cost_summary(
        price,
        ttl_hours=ttl_hours,
        ceiling_cad=float(cost_ceiling_cad),
    )

    parameter_document = {
        "$schema": (
            "https://schema.management.azure.com/schemas/"
            "2019-04-01/deploymentParameters.json#"
        ),
        "contentVersion": "1.0.0.0",
        "parameters": {
            name: {"value": value}
            for name, value in parameters.items()
        },
    }
    parameter_document["parameters"].update(
        {
            "environment": {"value": environment},
            "location": {"value": location},
        }
    )

    with tempfile.TemporaryDirectory(prefix="lab-preflight-") as temporary:
        parameter_file = Path(temporary) / "parameters.json"
        parameter_file.write_text(
            json.dumps(parameter_document, sort_keys=True),
            encoding="utf-8",
        )
        parameter_file.chmod(0o600)
        validation = _run_json(
            runner,
            (
                "az",
                "deployment",
                "sub",
                "validate",
                "--name",
                f"lab-preflight-{plan['request']['request_id']}",
                "--location",
                location,
                "--template-file",
                str(template_path),
                "--parameters",
                f"@{parameter_file}",
                "--output",
                "json",
                "--only-show-errors",
            ),
            cwd=root,
            timeout_seconds=max(timeout_seconds, 180),
        )
    validation_state = None
    if isinstance(validation, Mapping):
        properties = validation.get("properties")
        if isinstance(properties, Mapping):
            validation_state = properties.get("provisioningState")
        validation_state = validation_state or validation.get("provisioningState")
    template_validation = {
        "observation_status": "observed",
        "provisioning_state": _sanitize(validation_state, limit=64),
        "passed": str(validation_state).lower() == "succeeded",
        "parameter_values_returned": False,
        "arm_what_if_performed": False,
    }

    blockers: list[str] = []
    if not location_available:
        blockers.append("location_not_in_subscription_catalog")
    if not all(item["registered"] for item in provider_states):
        blockers.append("required_provider_not_registered")
    if not sku["location_available"]:
        blockers.append("vm_sku_not_available")
    for name, summary in (
        ("regional_compute_quota", regional_quota),
        ("family_compute_quota", family_quota),
        ("standard_public_ip_quota", public_ip_quota),
    ):
        if not summary["sufficient"]:
            blockers.append(f"{name}_insufficient_or_unobserved")
    if not group_summary["safe_for_dedicated_lab"]:
        blockers.append("target_resource_group_not_safe")
    if not permission_summary["sufficient_for_candidate_deployment"]:
        blockers.append("effective_permissions_insufficient_or_unobserved")
    if not cost["ceiling_accepted"]:
        blockers.append("cost_ceiling_not_accepted")
    if not template_validation["passed"]:
        blockers.append("template_validation_failed")

    clock = now or (lambda: datetime.now(timezone.utc))
    result: dict[str, Any] = {
        "schema_version": PREFLIGHT_SCHEMA,
        "observed_at_utc": (
            clock().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        ),
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "request": plan["request"],
        "plan_digest": plan["plan_digest"],
        "template": {
            "path": plan["deployment"]["template_path"],
            "sha256": plan["deployment"]["template_sha256"],
            "scope": plan["deployment"]["template_scope"],
        },
        "azure_context": {
            "subscription_name": _sanitize(account.get("name"), limit=128),
            "subscription_state": _sanitize(account.get("state"), limit=64),
            "subscription_fingerprint": _fingerprint(subscription_id),
            "tenant_fingerprint": _fingerprint(tenant_id),
            "raw_identifiers_returned": False,
        },
        "location": {
            "name": location,
            "available_in_subscription_catalog": location_available,
        },
        "providers": provider_states,
        "sku": sku,
        "quota": {
            "regional_compute": regional_quota,
            "family_compute": family_quota,
            "standard_public_ip": public_ip_quota,
        },
        "resource_group": group_summary,
        "permissions": permission_summary,
        "policy": policy_summary,
        "cost": cost,
        "template_validation": template_validation,
        "execution": {
            "azure_authentication_performed": True,
            "azure_queries_performed": True,
            "azure_mutations_performed": False,
            "arm_what_if_performed": False,
            "deployment_authorized": False,
            "deployment_performed": False,
            "cleanup_authorized": False,
            "cleanup_performed": False,
        },
        "next_gate": (
            "what_if_review_required"
            if not blockers
            else "preflight_remediation_required"
        ),
        "claim_boundaries": [
            "preflight_passed != ARM_What_If_reviewed",
            "template_validation_passed != deployment_authorized",
            "permission_check_sufficient != effective_least_privilege_verified",
            "retail_price_estimate != actual_billed_cost",
            "resource_group_safe != cleanup_verified",
        ],
    }
    result["preflight_digest"] = _canonical_digest(result)
    return result
