#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_backend_source(cloud_init_path: Path) -> str:
    lines = cloud_init_path.read_text(encoding="utf-8").splitlines()
    path_index = lines.index("  - path: /opt/servicetracer-demo/backend.py")
    content_index = lines.index("    content: |", path_index)
    source_lines: list[str] = []

    for line in lines[content_index + 1 :]:
        if line.startswith("  - path: ") or line == "runcmd:":
            break
        if line and not line.startswith("      "):
            raise SystemExit(f"unexpected backend indentation: {line!r}")
        source_lines.append(line[6:] if line else "")

    source = "\n".join(source_lines) + "\n"
    compile(source, str(cloud_init_path), "exec")
    return source


def render_unit(backend_id: str, mode: str, listener_port: int) -> str:
    return f"""[Unit]
Description=ServiceTracer simulated remote-access backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=SERVICETRACER_BACKEND_ID={backend_id}
Environment=SERVICETRACER_BACKEND_MODE={mode}
Environment=SERVICETRACER_LISTENER_PORT={listener_port}
Environment=SERVICETRACER_TLS_HANDSHAKE_TIMEOUT_SECONDS=1.0
ExecStart=/usr/bin/python3 /opt/servicetracer-demo/backend.py
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadOnlyPaths=/etc/servicetracer-demo

[Install]
WantedBy=multi-user.target
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render the exact VPN backend source embedded in cloud-init and a concrete systemd unit."
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--backend-id", default="VPN-LOCAL")
    parser.add_argument("--mode", choices=("healthy", "radius-timeout"), default="healthy")
    parser.add_argument("--listener-port", type=int, default=443)
    args = parser.parse_args()

    if not 1 <= args.listener_port <= 65535:
        parser.error("--listener-port must be between 1 and 65535")

    repo_root = args.repo_root.resolve()
    cloud_init_path = repo_root / "infra" / "bootstrap" / "vpn-backend-cloud-init.yaml"
    if not cloud_init_path.is_file():
        raise SystemExit(f"cloud-init source not found: {cloud_init_path}")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    backend_path = output_dir / "backend.py"
    unit_path = output_dir / "servicetracer-demo-backend.service"
    metadata_path = output_dir / "rendered-artifacts.json"

    backend_path.write_text(extract_backend_source(cloud_init_path), encoding="utf-8")
    unit_path.write_text(
        render_unit(args.backend_id, args.mode, args.listener_port), encoding="utf-8"
    )
    backend_path.chmod(0o755)
    unit_path.chmod(0o644)

    metadata = {
        "schema_version": "servicetracer.local-vm-render.v1",
        "source": str(cloud_init_path.relative_to(repo_root)),
        "backend_id": args.backend_id,
        "mode": args.mode,
        "listener_port": args.listener_port,
        "files": {
            "backend.py": {"sha256": sha256(backend_path), "mode": "0755"},
            "servicetracer-demo-backend.service": {
                "sha256": sha256(unit_path),
                "mode": "0644",
            },
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
