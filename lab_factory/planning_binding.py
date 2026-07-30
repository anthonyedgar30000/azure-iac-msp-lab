from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .catalog import CatalogError


_REQUIRED_PLANNING_KEYS = {
    "workflow_path",
    "github_environment",
    "dispatch_mode",
    "subscription_boundary",
    "dependency_subscription_role",
    "target_subscription_role",
    "dependency_resource_group_pattern",
    "prefix",
    "vm_size",
    "provider_validation_level",
    "includes_arm_validation",
    "includes_arm_what_if",
    "deployment_command_present",
    "required_human_inputs",
    "confirmation_pattern",
    "artifact_name_prefix",
}


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _selected_profile(
    catalog: Mapping[str, Any],
    *,
    profile_id: str,
    profile_version: str,
) -> Mapping[str, Any]:
    matches = [
        profile
        for profile in catalog.get("profiles", [])
        if profile.get("id") == profile_id
        and profile.get("version") == profile_version
    ]
    if len(matches) != 1:
        raise CatalogError(
            f"planner binding profile resolution failed: "
            f"{profile_id}@{profile_version}"
        )
    return matches[0]


def _validated_binding(
    profile: Mapping[str, Any],
    *,
    repository_root: Path,
) -> Mapping[str, Any]:
    planning = profile.get("planning")
    if not isinstance(planning, Mapping):
        raise CatalogError(
            f"profile has no planning binding: "
            f"{profile.get('id')}@{profile.get('version')}"
        )
    if set(planning) != _REQUIRED_PLANNING_KEYS:
        missing = sorted(_REQUIRED_PLANNING_KEYS - set(planning))
        unknown = sorted(set(planning) - _REQUIRED_PLANNING_KEYS)
        raise CatalogError(
            "planning binding keys do not match the bounded contract: "
            f"missing={missing}, unknown={unknown}"
        )

    workflow_text = planning.get("workflow_path")
    if not isinstance(workflow_text, str) or not workflow_text:
        raise CatalogError("planning.workflow_path is required")
    workflow_path = Path(workflow_text)
    if workflow_path.is_absolute():
        raise CatalogError("planning.workflow_path must be repository-relative")
    resolved_workflow = (repository_root / workflow_path).resolve()
    if (
        not resolved_workflow.is_relative_to(repository_root)
        or resolved_workflow.suffix not in {".yml", ".yaml"}
        or not resolved_workflow.is_file()
    ):
        raise CatalogError("planning.workflow_path must reference a repository workflow")

    string_keys = (
        "github_environment",
        "dispatch_mode",
        "subscription_boundary",
        "dependency_subscription_role",
        "target_subscription_role",
        "dependency_resource_group_pattern",
        "prefix",
        "vm_size",
        "provider_validation_level",
        "confirmation_pattern",
        "artifact_name_prefix",
    )
    for key in string_keys:
        if not isinstance(planning.get(key), str) or not planning[key]:
            raise CatalogError(f"planning.{key} must be a non-empty string")

    if planning["dispatch_mode"] != "manual_only":
        raise CatalogError("planning dispatch must remain manual-only")
    if planning["subscription_boundary"] != "single_subscription":
        raise CatalogError("planning subscription boundary must remain single-subscription")
    if planning["github_environment"] != "azure-lab":
        raise CatalogError("planning GitHub environment must remain azure-lab")
    if planning["provider_validation_level"] != "ProviderNoRbac":
        raise CatalogError("planning validation must remain ProviderNoRbac")
    if planning["includes_arm_validation"] is not True:
        raise CatalogError("planning must include ARM validation")
    if planning["includes_arm_what_if"] is not True:
        raise CatalogError("planning must include bounded ARM What-If")
    if planning["deployment_command_present"] is not False:
        raise CatalogError("planning binding must not contain a deployment command")

    human_inputs = planning.get("required_human_inputs")
    expected_inputs = [
        "dns_label",
        "allowed_origin",
        "maximum_monthly_cost_cad",
    ]
    if human_inputs != expected_inputs:
        raise CatalogError("planning human-input contract changed")

    environments = profile.get("environments")
    locations = profile.get("allowed_locations")
    if not isinstance(environments, list) or not isinstance(locations, list):
        raise CatalogError("profile environment or location contract is invalid")
    for environment in environments:
        rendered = planning["dependency_resource_group_pattern"].format(
            environment=environment
        )
        if re.fullmatch(r"[A-Za-z0-9._()\-]+", rendered) is None:
            raise CatalogError(
                "planning dependency resource-group pattern renders an invalid name"
            )
    if planning["vm_size"] != profile["parameters"]["defaults"]["vmSize"]:
        raise CatalogError("planning VM size diverges from the profile default")
    if planning["prefix"] != profile["parameters"]["fixed"]["prefix"]:
        raise CatalogError("planning prefix diverges from the profile fixed parameter")

    workflow = resolved_workflow.read_text(encoding="utf-8")
    required_markers = (
        "environment: azure-lab",
        "AZURE_CLIENT_ID",
        "AZURE_SUBSCRIPTION_ID",
        'subscription_boundary:"single_subscription"',
        "ProviderNoRbac",
        "az deployment sub validate",
        "az deployment sub what-if",
        "workloads/servicetracer-demo-api/scripts/install.sh",
    )
    missing_markers = [marker for marker in required_markers if marker not in workflow]
    if missing_markers:
        raise CatalogError(
            "ratified planner workflow is missing required markers: "
            + ", ".join(missing_markers)
        )
    forbidden_markers = (
        "AZURE_DEPENDENCY_CLIENT_ID",
        "AZURE_TARGET_CLIENT_ID",
        "AZURE_DEPENDENCY_SUBSCRIPTION_ID",
        "AZURE_TARGET_SUBSCRIPTION_ID",
        "az deployment sub create",
    )
    unexpected_markers = [marker for marker in forbidden_markers if marker in workflow]
    if unexpected_markers:
        raise CatalogError(
            "ratified planner workflow contains forbidden dual-subscription or deployment markers: "
            + ", ".join(unexpected_markers)
        )
    return planning


def profile_planning_summary(
    catalog: Mapping[str, Any],
    *,
    profile_id: str,
    profile_version: str,
    repository_root: str | Path,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    profile = _selected_profile(
        catalog,
        profile_id=profile_id,
        profile_version=profile_version,
    )
    planning = _validated_binding(profile, repository_root=root)
    return {
        "workflow_path": planning["workflow_path"],
        "github_environment": planning["github_environment"],
        "dispatch_mode": planning["dispatch_mode"],
        "subscription_boundary": planning["subscription_boundary"],
        "dependency_subscription_role": planning["dependency_subscription_role"],
        "target_subscription_role": planning["target_subscription_role"],
        "provider_validation_level": planning["provider_validation_level"],
        "includes_arm_validation": planning["includes_arm_validation"],
        "includes_arm_what_if": planning["includes_arm_what_if"],
        "deployment_command_present": planning["deployment_command_present"],
        "artifact_name_prefix": planning["artifact_name_prefix"],
    }


def enrich_plan_with_planning(
    catalog: Mapping[str, Any],
    plan: Mapping[str, Any],
    *,
    repository_root: str | Path,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    request = plan.get("request")
    if not isinstance(request, Mapping):
        raise CatalogError("prepared plan has no request object")
    profile = _selected_profile(
        catalog,
        profile_id=str(request.get("profile_id", "")),
        profile_version=str(request.get("profile_version", "")),
    )
    planning = _validated_binding(profile, repository_root=root)
    environment = str(request.get("environment", ""))
    location = str(request.get("location", ""))
    dependency_resource_group = planning["dependency_resource_group_pattern"].format(
        environment=environment
    )

    enriched = dict(plan)
    base_plan_digest = enriched.pop("plan_digest", None)
    enriched["planning"] = {
        "workflow_path": planning["workflow_path"],
        "github_environment": planning["github_environment"],
        "dispatch_mode": planning["dispatch_mode"],
        "workflow_dispatch_performed": False,
        "subscription_boundary": planning["subscription_boundary"],
        "dependency_subscription_role": planning["dependency_subscription_role"],
        "target_subscription_role": planning["target_subscription_role"],
        "provider_validation_level": planning["provider_validation_level"],
        "includes_arm_validation": planning["includes_arm_validation"],
        "includes_arm_what_if": planning["includes_arm_what_if"],
        "deployment_command_present": planning["deployment_command_present"],
        "derived_non_secret_inputs": {
            "environment": environment,
            "location": location,
            "prefix": planning["prefix"],
            "dependency_resource_group": dependency_resource_group,
            "vm_size": planning["vm_size"],
        },
        "required_human_input_names": list(planning["required_human_inputs"]),
        "confirmation_pattern": planning["confirmation_pattern"].format(
            environment=environment
        ),
        "artifact_name_prefix": planning["artifact_name_prefix"],
        "live_subscription_state_observed": False,
        "dispatch_authorized": False,
    }
    enriched["base_plan_digest"] = base_plan_digest
    enriched["plan_digest"] = _digest(enriched)
    return enriched


__all__ = [
    "enrich_plan_with_planning",
    "profile_planning_summary",
]
