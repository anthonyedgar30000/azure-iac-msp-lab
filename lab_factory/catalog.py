from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


DEFAULT_CATALOG_PATH = Path(__file__).with_name("catalog.json")
_ALLOWED_RELEASE_STATES = {"candidate", "released", "retired"}
_ALLOWED_TEMPLATE_SCOPES = {"subscription", "resourceGroup"}
_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
_SEMVER_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


class CatalogError(ValueError):
    """Raised when a catalog or lab request violates the bounded contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _version_key(version: str) -> tuple[int, int, int]:
    match = _SEMVER_PATTERN.fullmatch(version)
    if match is None:
        raise CatalogError(f"invalid semantic version: {version}")
    return tuple(int(part) for part in match.groups())


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CatalogError(f"{name} must be an object")
    return value


def _require_string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise CatalogError(f"{name} must be a non-empty string array")
    if len(value) != len(set(value)):
        raise CatalogError(f"{name} must not contain duplicates")
    return value


def _resolve_repository_root(catalog_path: Path, repository_root: str | Path | None) -> Path:
    if repository_root is not None:
        return Path(repository_root).resolve()
    if catalog_path == DEFAULT_CATALOG_PATH.resolve():
        return Path(__file__).resolve().parents[1]
    return catalog_path.resolve().parent.parent


def validate_catalog(catalog: Mapping[str, Any], repository_root: str | Path) -> None:
    root = Path(repository_root).resolve()
    if catalog.get("schema_version") != "lab-factory.catalog.v1":
        raise CatalogError("unsupported catalog schema_version")
    _version_key(str(catalog.get("catalog_version", "")))

    profiles = catalog.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise CatalogError("profiles must be a non-empty array")

    identities: set[tuple[str, str]] = set()
    for index, raw_profile in enumerate(profiles):
        profile = _require_mapping(raw_profile, f"profiles[{index}]")
        profile_id = profile.get("id")
        version = profile.get("version")
        if not isinstance(profile_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", profile_id):
            raise CatalogError(f"profiles[{index}].id is invalid")
        if not isinstance(version, str):
            raise CatalogError(f"profiles[{index}].version is required")
        _version_key(version)
        identity = (profile_id, version)
        if identity in identities:
            raise CatalogError(f"duplicate profile identity: {profile_id}@{version}")
        identities.add(identity)

        if profile.get("release_state") not in _ALLOWED_RELEASE_STATES:
            raise CatalogError(f"{profile_id}@{version} has an invalid release_state")

        template = _require_mapping(profile.get("template"), f"{profile_id}.template")
        template_path_text = template.get("path")
        if not isinstance(template_path_text, str) or not template_path_text:
            raise CatalogError(f"{profile_id}.template.path is required")
        template_path = Path(template_path_text)
        if template_path.is_absolute():
            raise CatalogError(f"{profile_id}.template.path must be repository-relative")
        resolved_template = (root / template_path).resolve()
        if not resolved_template.is_relative_to(root):
            raise CatalogError(f"{profile_id}.template.path escapes the repository")
        if resolved_template.suffix != ".bicep" or not resolved_template.is_file():
            raise CatalogError(f"{profile_id}.template.path must reference an existing Bicep file")
        if template.get("scope") not in _ALLOWED_TEMPLATE_SCOPES:
            raise CatalogError(f"{profile_id}.template.scope is invalid")

        environments = _require_string_list(profile.get("environments"), f"{profile_id}.environments")
        locations = _require_string_list(profile.get("allowed_locations"), f"{profile_id}.allowed_locations")
        default_location = profile.get("default_location")
        if default_location not in locations:
            raise CatalogError(f"{profile_id}.default_location must be allowed")

        ttl = _require_mapping(profile.get("ttl"), f"{profile_id}.ttl")
        minimum = ttl.get("minimum_hours")
        default = ttl.get("default_hours")
        maximum = ttl.get("maximum_hours")
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in (minimum, default, maximum)):
            raise CatalogError(f"{profile_id}.ttl values must be integers")
        if not 1 <= minimum <= default <= maximum <= 168:
            raise CatalogError(f"{profile_id}.ttl values are outside the bounded range")

        pattern = profile.get("resource_group_pattern")
        if not isinstance(pattern, str) or not pattern:
            raise CatalogError(f"{profile_id}.resource_group_pattern is required")
        try:
            rendered = pattern.format(environment=environments[0], location=locations[0])
        except (KeyError, ValueError) as exc:
            raise CatalogError(f"{profile_id}.resource_group_pattern is invalid") from exc
        if "{" in rendered or "}" in rendered or not re.fullmatch(r"[A-Za-z0-9._()\-]+", rendered):
            raise CatalogError(f"{profile_id}.resource_group_pattern renders an invalid name")

        parameters = _require_mapping(profile.get("parameters"), f"{profile_id}.parameters")
        required = _require_string_list(parameters.get("required"), f"{profile_id}.parameters.required")
        fixed = _require_mapping(parameters.get("fixed"), f"{profile_id}.parameters.fixed")
        defaults = _require_mapping(parameters.get("defaults"), f"{profile_id}.parameters.defaults")
        parameter_names = set(required) | set(fixed) | set(defaults)
        if any(_NAME_PATTERN.fullmatch(name) is None for name in parameter_names):
            raise CatalogError(f"{profile_id} contains an invalid parameter name")
        if set(required) & set(fixed) or set(required) & set(defaults) or set(fixed) & set(defaults):
            raise CatalogError(f"{profile_id} parameter groups must be disjoint")

        _require_string_list(profile.get("preflight_checks"), f"{profile_id}.preflight_checks")
        _require_string_list(profile.get("validation_checks"), f"{profile_id}.validation_checks")
        _require_string_list(profile.get("claim_boundaries"), f"{profile_id}.claim_boundaries")

        cleanup = _require_mapping(profile.get("cleanup"), f"{profile_id}.cleanup")
        if cleanup.get("automatic_execution_enabled") is not False:
            raise CatalogError(f"{profile_id} cleanup must remain fail-closed")


def load_catalog(
    path: str | Path | None = None,
    *,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    catalog_path = Path(path).resolve() if path is not None else DEFAULT_CATALOG_PATH.resolve()
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogError(f"catalog not found: {catalog_path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogError(f"catalog is not valid JSON: {catalog_path}") from exc
    if not isinstance(catalog, dict):
        raise CatalogError("catalog root must be an object")
    root = _resolve_repository_root(catalog_path, repository_root)
    validate_catalog(catalog, root)
    return catalog


def list_profiles(catalog: Mapping[str, Any]) -> list[dict[str, Any]]:
    profiles = []
    for profile in catalog["profiles"]:
        profiles.append(
            {
                "id": profile["id"],
                "version": profile["version"],
                "display_name": profile["display_name"],
                "description": profile["description"],
                "release_state": profile["release_state"],
                "default_location": profile["default_location"],
                "allowed_locations": list(profile["allowed_locations"]),
                "default_ttl_hours": profile["ttl"]["default_hours"],
            }
        )
    return sorted(profiles, key=lambda item: (item["id"], _version_key(item["version"])))


def _select_profile(catalog: Mapping[str, Any], profile_id: str, version: str | None) -> Mapping[str, Any]:
    matches = [profile for profile in catalog["profiles"] if profile["id"] == profile_id]
    if not matches:
        raise CatalogError(f"unknown profile: {profile_id}")
    if version is not None:
        for profile in matches:
            if profile["version"] == version:
                return profile
        raise CatalogError(f"unknown profile version: {profile_id}@{version}")
    return max(matches, key=lambda profile: _version_key(profile["version"]))


def prepare_lab_plan(
    catalog: Mapping[str, Any],
    *,
    profile_id: str,
    environment: str = "dev",
    location: str | None = None,
    ttl_hours: int | None = None,
    version: str | None = None,
    parameters: Mapping[str, str] | None = None,
    request_id: str | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    profile = _select_profile(catalog, profile_id, version)
    if profile["release_state"] == "retired":
        raise CatalogError(f"profile is retired: {profile_id}@{profile['version']}")
    if environment not in profile["environments"]:
        raise CatalogError(f"environment is not allowed: {environment}")

    selected_location = location or profile["default_location"]
    if selected_location not in profile["allowed_locations"]:
        raise CatalogError(f"location is not allowed: {selected_location}")

    ttl = ttl_hours if ttl_hours is not None else profile["ttl"]["default_hours"]
    if not isinstance(ttl, int) or isinstance(ttl, bool):
        raise CatalogError("ttl_hours must be an integer")
    if not profile["ttl"]["minimum_hours"] <= ttl <= profile["ttl"]["maximum_hours"]:
        raise CatalogError("ttl_hours is outside the profile boundary")

    supplied = dict(parameters or {})
    allowed_parameter_names = (
        set(profile["parameters"]["required"])
        | set(profile["parameters"]["fixed"])
        | set(profile["parameters"]["defaults"])
    )
    unknown = sorted(set(supplied) - allowed_parameter_names)
    if unknown:
        raise CatalogError(f"unknown parameters: {', '.join(unknown)}")
    fixed_overrides = sorted(set(supplied) & set(profile["parameters"]["fixed"]))
    if fixed_overrides:
        raise CatalogError(f"fixed parameters cannot be overridden: {', '.join(fixed_overrides)}")
    for name, value in supplied.items():
        if not isinstance(value, str) or not value or len(value) > 4096 or "\x00" in value:
            raise CatalogError(f"parameter {name} must be a non-empty bounded string")

    missing = sorted(set(profile["parameters"]["required"]) - set(supplied))
    resolved_parameter_names = sorted(
        set(profile["parameters"]["fixed"])
        | set(profile["parameters"]["defaults"])
        | set(supplied)
    )
    request_seed = {
        "profile_id": profile["id"],
        "profile_version": profile["version"],
        "environment": environment,
        "location": selected_location,
        "ttl_hours": ttl,
        "supplied_parameter_names": sorted(supplied),
    }
    derived_request_id = request_id or f"lab-{_digest(request_seed).split(':', 1)[1][:12]}"
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", derived_request_id) is None:
        raise CatalogError("request_id must be 3-64 lowercase letters, numbers, or hyphens")

    root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[1]
    template_path = (root / profile["template"]["path"]).resolve()
    if not template_path.is_relative_to(root) or not template_path.is_file():
        raise CatalogError("profile template is not available in the repository")

    resource_group = profile["resource_group_pattern"].format(
        environment=environment,
        location=selected_location,
    )
    ready_for_preflight = not missing
    plan: dict[str, Any] = {
        "schema_version": "lab-factory.plan.v1",
        "request": {
            "request_id": derived_request_id,
            "profile_id": profile["id"],
            "profile_version": profile["version"],
            "environment": environment,
            "location": selected_location,
            "ttl_hours": ttl,
        },
        "resolved_profile": {
            "display_name": profile["display_name"],
            "release_state": profile["release_state"],
            "catalog_digest": _digest(catalog),
        },
        "deployment": {
            "operation": "prepare_only",
            "template_path": profile["template"]["path"],
            "template_scope": profile["template"]["scope"],
            "template_sha256": _file_digest(template_path),
            "resource_group": resource_group,
            "resolved_parameter_names": resolved_parameter_names,
            "user_supplied_parameter_names": sorted(supplied),
            "missing_required_parameters": missing,
        },
        "gates": {
            "ready_for_preflight": ready_for_preflight,
            "preflight_checks": list(profile["preflight_checks"]),
            "what_if_required": True,
            "explicit_deployment_authorization_required": True,
            "post_deployment_validation_checks": list(profile["validation_checks"]),
            "cleanup_verification_required": True,
        },
        "execution": {
            "azure_queries_performed": False,
            "azure_mutations_performed": False,
            "deployment_authorized": False,
            "cleanup_authorized": False,
        },
        "next_gate": "preflight_required" if ready_for_preflight else "parameters_required",
        "claim_boundaries": list(profile["claim_boundaries"]),
    }
    plan["plan_digest"] = _digest(plan)
    return plan
