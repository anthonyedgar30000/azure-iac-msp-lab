from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from lab_factory.catalog import (
    CatalogError,
    list_profiles,
    load_catalog,
    prepare_lab_plan,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _select_profile(
    catalog: Mapping[str, Any],
    *,
    profile_id: str,
    version: str | None,
) -> Mapping[str, Any]:
    matches = [
        profile
        for profile in catalog["profiles"]
        if profile["id"] == profile_id
        and (version is None or profile["version"] == version)
    ]
    if not matches:
        if version is None:
            raise CatalogError(f"unknown profile: {profile_id}")
        raise CatalogError(f"unknown profile version: {profile_id}@{version}")
    return max(
        matches,
        key=lambda profile: tuple(int(part) for part in profile["version"].split(".")),
    )


def _planner_binding(
    profile: Mapping[str, Any],
    *,
    repository_root: Path,
    supplied_parameter_names: set[str],
    base_ready: bool,
) -> dict[str, Any]:
    planner = profile.get("planner")
    if not isinstance(planner, Mapping):
        raise CatalogError(
            f"profile has no canonical planner binding: {profile['id']}@{profile['version']}"
        )

    workflow_path_text = planner.get("workflow_path")
    installer_path_text = planner.get("installer_path")
    if not isinstance(workflow_path_text, str) or not workflow_path_text:
        raise CatalogError("planner.workflow_path is required")
    if not isinstance(installer_path_text, str) or not installer_path_text:
        raise CatalogError("planner.installer_path is required")

    workflow_path = (repository_root / workflow_path_text).resolve()
    installer_path = (repository_root / installer_path_text).resolve()
    for label, path in (
        ("planner workflow", workflow_path),
        ("planner installer", installer_path),
    ):
        if not path.is_relative_to(repository_root) or not path.is_file():
            raise CatalogError(f"{label} escaped the repository or is missing")

    required_literals = {
        "trigger": "workflow_dispatch",
        "github_environment": "azure-api-payg",
        "subscription_boundary": "dual_subscription",
        "dependency_subscription_access": "read_only",
        "target_subscription_access": "planning_only",
        "provider_validation_level": "ProviderNoRbac",
    }
    for field, expected in required_literals.items():
        if planner.get(field) != expected:
            raise CatalogError(f"planner.{field} must equal {expected}")
    for field, expected in (
        ("arm_validation_required", True),
        ("arm_what_if_required", True),
        ("deployment_command_available", False),
    ):
        if planner.get(field) is not expected:
            raise CatalogError(f"planner.{field} must equal {expected}")

    input_bindings = planner.get("input_bindings")
    derived_parameters = planner.get("derived_template_parameters")
    if not isinstance(input_bindings, Mapping) or not isinstance(
        derived_parameters, Mapping
    ):
        raise CatalogError(
            "planner input_bindings and derived_template_parameters must be objects"
        )

    bound_input_names: list[str] = []
    missing_input_names: list[str] = []
    for input_name, source in sorted(input_bindings.items()):
        if not isinstance(input_name, str) or not isinstance(source, str):
            raise CatalogError("planner input bindings must contain string names and sources")
        if source.startswith("parameter:"):
            parameter_name = source.split(":", 1)[1]
            target = (
                bound_input_names
                if parameter_name in supplied_parameter_names
                else missing_input_names
            )
            target.append(input_name)
        elif source == "derived_not_returned":
            target = bound_input_names if base_ready else missing_input_names
            target.append(input_name)
        else:
            bound_input_names.append(input_name)

    ready_for_dispatch_review = base_ready and not missing_input_names
    return {
        "schema_version": "lab-factory.planner-binding.v1",
        "operation": "prepare_only",
        "workflow_path": workflow_path_text,
        "workflow_sha256": _file_digest(workflow_path),
        "trigger": planner["trigger"],
        "github_environment": planner["github_environment"],
        "subscription_boundary": planner["subscription_boundary"],
        "dependency_subscription_access": planner[
            "dependency_subscription_access"
        ],
        "target_subscription_access": planner["target_subscription_access"],
        "provider_validation_level": planner["provider_validation_level"],
        "arm_validation_required": planner["arm_validation_required"],
        "arm_what_if_required": planner["arm_what_if_required"],
        "deployment_command_available": planner[
            "deployment_command_available"
        ],
        "installer_path": installer_path_text,
        "installer_sha256": _file_digest(installer_path),
        "input_bindings": dict(sorted(input_bindings.items())),
        "derived_template_parameters": dict(
            sorted(derived_parameters.items())
        ),
        "bound_input_names": bound_input_names,
        "missing_input_names": missing_input_names,
        "parameter_values_returned": False,
        "confirmation_value_returned": False,
        "ready_for_dispatch_review": ready_for_dispatch_review,
        "live_dispatch_authorized": False,
    }


def list_lab_profiles_payload(
    *,
    catalog_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return the bounded repository catalog without querying Azure."""

    root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else REPOSITORY_ROOT
    )
    catalog = load_catalog(catalog_path, repository_root=root)
    profiles = list_profiles(catalog)
    for item in profiles:
        profile = _select_profile(
            catalog,
            profile_id=item["id"],
            version=item["version"],
        )
        binding = _planner_binding(
            profile,
            repository_root=root,
            supplied_parameter_names=set(),
            base_ready=False,
        )
        item["planner"] = {
            "workflow_path": binding["workflow_path"],
            "workflow_sha256": binding["workflow_sha256"],
            "trigger": binding["trigger"],
            "github_environment": binding["github_environment"],
            "subscription_boundary": binding["subscription_boundary"],
            "provider_validation_level": binding[
                "provider_validation_level"
            ],
            "deployment_command_available": binding[
                "deployment_command_available"
            ],
            "live_dispatch_authorized": False,
        }
    return {
        "schema_version": "lab-factory.profile-list.v2",
        "profiles": profiles,
        "execution": {
            "azure_queries_performed": False,
            "azure_mutations_performed": False,
            "workflow_dispatch_performed": False,
            "deployment_authorized": False,
            "cleanup_authorized": False,
        },
        "claim_boundaries": [
            "catalog_entry != released_lab",
            "allowed_location != live_capacity_available",
            "profile_listed != workflow_dispatched",
            "planner_bound != deployment_authorized",
        ],
    }


def prepare_lab_request_payload(
    *,
    profile_id: str,
    environment: str = "dev",
    location: str | None = None,
    ttl_hours: int | None = None,
    version: str | None = None,
    request_id: str | None = None,
    parameters: Mapping[str, str] | None = None,
    catalog_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Prepare a planner-bound request without Azure access or dispatch authority."""

    root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else REPOSITORY_ROOT
    )
    catalog = load_catalog(catalog_path, repository_root=root)
    supplied = dict(parameters or {})
    plan = prepare_lab_plan(
        catalog,
        profile_id=profile_id,
        environment=environment,
        location=location,
        ttl_hours=ttl_hours,
        version=version,
        request_id=request_id,
        parameters=supplied,
        repository_root=root,
    )
    profile = _select_profile(
        catalog,
        profile_id=profile_id,
        version=plan["request"]["profile_version"],
    )
    binding = _planner_binding(
        profile,
        repository_root=root,
        supplied_parameter_names=set(
            plan["deployment"]["user_supplied_parameter_names"]
        ),
        base_ready=bool(plan["gates"]["ready_for_preflight"]),
    )
    plan["planner"] = binding
    plan["execution"]["workflow_dispatch_performed"] = False
    plan["next_gate"] = (
        "planner_dispatch_review_required"
        if binding["ready_for_dispatch_review"]
        else "parameters_required"
    )
    plan["claim_boundaries"] = list(plan["claim_boundaries"]) + [
        "planner_bound != workflow_dispatched",
        "workflow_dispatch_prepared != ARM_What_If_reviewed",
        "planning_succeeded != deployment_authorized",
    ]
    plan.pop("plan_digest", None)
    plan["plan_digest"] = _canonical_digest(plan)
    return plan


__all__ = [
    "CatalogError",
    "list_lab_profiles_payload",
    "prepare_lab_request_payload",
]
