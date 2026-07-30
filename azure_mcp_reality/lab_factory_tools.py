from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from lab_factory.catalog import (
    CatalogError,
    list_profiles,
    load_catalog,
    prepare_lab_plan,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


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
    return {
        "schema_version": "lab-factory.profile-list.v1",
        "profiles": list_profiles(catalog),
        "execution": {
            "azure_queries_performed": False,
            "azure_mutations_performed": False,
            "deployment_authorized": False,
            "cleanup_authorized": False,
        },
        "claim_boundaries": [
            "catalog_entry != released_lab",
            "allowed_location != live_capacity_available",
            "profile_listed != deployment_authorized",
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
    """Prepare a deterministic plan without Azure access or deployment authority."""

    root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else REPOSITORY_ROOT
    )
    catalog = load_catalog(catalog_path, repository_root=root)
    return prepare_lab_plan(
        catalog,
        profile_id=profile_id,
        environment=environment,
        location=location,
        ttl_hours=ttl_hours,
        version=version,
        request_id=request_id,
        parameters=dict(parameters or {}),
        repository_root=root,
    )


__all__ = [
    "CatalogError",
    "list_lab_profiles_payload",
    "prepare_lab_request_payload",
]
