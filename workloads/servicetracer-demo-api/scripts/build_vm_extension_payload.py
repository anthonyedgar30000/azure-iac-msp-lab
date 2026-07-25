from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shlex
from urllib.parse import urlparse

SHA40 = re.compile(r"^[0-9a-f]{40}$")


def require_https(value: str, field: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field} must be an absolute HTTPS URL")
    return value


def build_payload(
    *,
    location: str,
    installer_uri: str,
    source_repository: str,
    source_ref: str,
    public_fqdn: str,
    backend_transaction_url: str,
    allowed_origin: str,
    force_update_tag: str,
) -> dict[str, object]:
    if not location.strip():
        raise ValueError("location is required")
    if not SHA40.fullmatch(source_ref):
        raise ValueError("source_ref must be a lowercase 40-character commit SHA")
    if not public_fqdn.strip() or any(char.isspace() for char in public_fqdn):
        raise ValueError("public_fqdn must be a non-empty hostname without whitespace")
    if not force_update_tag.strip():
        raise ValueError("force_update_tag is required")

    installer_uri = require_https(installer_uri, "installer_uri")
    source_repository = require_https(source_repository, "source_repository")
    backend_transaction_url = require_https(
        backend_transaction_url, "backend_transaction_url"
    )
    allowed_origin = require_https(allowed_origin, "allowed_origin")

    command = shlex.join(
        [
            "bash",
            "install.sh",
            source_repository,
            source_ref,
            public_fqdn,
            backend_transaction_url,
            allowed_origin,
        ]
    )

    return {
        "location": location,
        "properties": {
            "publisher": "Microsoft.Azure.Extensions",
            "type": "CustomScript",
            "typeHandlerVersion": "2.1",
            "autoUpgradeMinorVersion": True,
            "forceUpdateTag": force_update_tag,
            "protectedSettings": {
                "fileUris": [installer_uri],
                "commandToExecute": command,
            },
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the exact VM extension create-or-update payload."
    )
    parser.add_argument("--location", required=True)
    parser.add_argument("--installer-uri", required=True)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--public-fqdn", required=True)
    parser.add_argument("--backend-transaction-url", required=True)
    parser.add_argument("--allowed-origin", required=True)
    parser.add_argument("--force-update-tag", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(
        location=args.location,
        installer_uri=args.installer_uri,
        source_repository=args.source_repository,
        source_ref=args.source_ref,
        public_fqdn=args.public_fqdn,
        backend_transaction_url=args.backend_transaction_url,
        allowed_origin=args.allowed_origin,
        force_update_tag=args.force_update_tag,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
