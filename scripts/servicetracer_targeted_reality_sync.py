#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import ssl
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

RESOURCE_GROUP = "rg-st-demo-api-dev-westus2"
VM_NAME = "vm-st-demo-api-mst-dev"
LOCATION = "westus2"
FQDN = "st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com"
UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
SUBSCRIPTION_PATH = re.compile(r"/subscriptions/[^/]+", re.IGNORECASE)


def observed_at() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest(value: str | None) -> str | None:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else None


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: redact(item)
            for key, item in value.items()
            if key not in {"subscriptionId", "tenantId", "principalId", "objectId"}
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        value = SUBSCRIPTION_PATH.sub("/subscriptions/<redacted>", value)
        return UUID.sub("<redacted-uuid>", value)
    return value


def run(command: list[str], *, allow_failure: bool = False) -> tuple[bool, str, str]:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    stdout = result.stdout
    stderr = redact(" ".join(result.stderr.split())[:1000])
    if result.returncode != 0 and not allow_failure:
        raise RuntimeError(f"command failed: {' '.join(command[:3])}: {stderr}")
    return result.returncode == 0, stdout, str(stderr)


def az(args: list[str], *, allow_failure: bool = False) -> tuple[bool, Any, str]:
    ok, stdout, stderr = run(
        ["az", *args, "--only-show-errors", "--output", "json"],
        allow_failure=allow_failure,
    )
    if not ok:
        return False, None, stderr
    return True, json.loads(stdout or "null"), ""


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def public_health() -> dict[str, Any]:
    request = urllib.request.Request(
        f"https://{FQDN}/api/health",
        headers={"Origin": "https://anthonyedgar30000.github.io", "User-Agent": "servicetracer-reality-sync/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30, context=ssl.create_default_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return {
                "status": "observed",
                "http_status": response.status,
                "payload": redact(payload),
                "access_control_allow_origin": response.headers.get("Access-Control-Allow-Origin"),
            }
    except Exception as exc:  # evidence must fail closed
        return {
            "status": "observation_failed",
            "error_type": type(exc).__name__,
            "claim_boundary": "Public health observation failure does not establish service absence.",
        }


def quota_record(items: list[dict[str, Any]], names: tuple[str, ...]) -> dict[str, Any] | None:
    normalized = {str(item.get("name", {}).get("value", "")).lower(): item for item in items}
    for name in names:
        item = normalized.get(name.lower())
        if item:
            return {"name": item.get("name", {}).get("localizedValue"), "current": item.get("currentValue"), "limit": item.get("limit")}
    return None


def guest_script() -> str:
    return r'''set -eu
python3 - <<'PY'
import hashlib
import json
import re
import subprocess
import urllib.request
from pathlib import Path


def command(args):
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr_present": bool(result.stderr.strip())}

result = {
    "source_ref": None,
    "service": {},
    "nginx": {},
    "environment": {},
    "local_health": {},
    "file_sha256": {},
}
source_root = Path('/opt/servicetracer-demo-api-src')
if source_root.exists():
    git = command(['git', '-C', str(source_root), 'rev-parse', 'HEAD'])
    if git['returncode'] == 0:
        result['source_ref'] = git['stdout']
for unit in ('servicetracer-demo-api.service', 'nginx.service'):
    active = command(['systemctl', 'is-active', unit])
    enabled = command(['systemctl', 'is-enabled', unit])
    show = command(['systemctl', 'show', unit, '--property=ActiveState,SubState,MainPID,FragmentPath', '--no-pager'])
    result['service'][unit] = {"active": active['stdout'], "enabled": enabled['stdout'], "properties": show['stdout'].splitlines()}
nginx = command(['nginx', '-T'])
combined = nginx['stdout']
if not combined:
    combined = subprocess.run(['nginx', '-T'], text=True, capture_output=True, check=False).stderr
match = re.search(r'proxy_read_timeout\s+([0-9]+)s;', combined)
result['nginx'] = {"config_valid": nginx['returncode'] == 0, "proxy_read_timeout_seconds": int(match.group(1)) if match else None}
for env_path in (Path('/etc/servicetracer-demo-api/service.env'), Path('/etc/servicetracer/demo-api.env')):
    if env_path.exists():
        result['environment']['path'] = str(env_path)
        for line in env_path.read_text(encoding='utf-8').splitlines():
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            if key in {
                'SERVICETRACER_ALLOWED_ORIGIN',
                'SERVICETRACER_SOURCE_ID',
                'SERVICETRACER_DEMO_API_LISTEN',
                'SERVICETRACER_DEMO_API_PORT',
                'SERVICETRACER_HOSTING_MODEL',
                'SERVICETRACER_BACKEND_TIMEOUT_SECONDS',
                'SERVICETRACER_MAX_PARALLEL_TRANSACTIONS',
            }:
                result['environment'][key] = value
        break
try:
    with urllib.request.urlopen('http://127.0.0.1:8090/api/health', timeout=10) as response:
        result['local_health'] = {"http_status": response.status, "payload": json.loads(response.read().decode('utf-8'))}
except Exception as exc:
    result['local_health'] = {"status": "observation_failed", "error_type": type(exc).__name__}
for path in (
    Path('/opt/servicetracer-demo-api/core.py'),
    Path('/opt/servicetracer-demo-api/runtime.py'),
    Path('/opt/servicetracer-demo-api/standalone_server.py'),
):
    if path.exists():
        result['file_sha256'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
print('SERVICETRACER_SYNC_JSON_BEGIN')
print(json.dumps(result, separators=(',', ':')))
print('SERVICETRACER_SYNC_JSON_END')
PY'''


def guest_observation() -> dict[str, Any]:
    ok, response, error = az(
        [
            "vm", "run-command", "invoke",
            "--resource-group", RESOURCE_GROUP,
            "--name", VM_NAME,
            "--command-id", "RunShellScript",
            "--scripts", guest_script(),
        ],
        allow_failure=True,
    )
    if not ok:
        return {
            "status": "observation_failed",
            "error": error,
            "claim_boundary": "Guest state remains not_observed; command failure does not establish service failure.",
        }
    message = "\n".join(str(item.get("message", "")) for item in (response or {}).get("value", []))
    match = re.search(r"SERVICETRACER_SYNC_JSON_BEGIN\s*(\{.*\})\s*SERVICETRACER_SYNC_JSON_END", message, re.DOTALL)
    if not match:
        return {"status": "observation_failed", "error": "bounded JSON markers not found"}
    return {"status": "observed", "result": redact(json.loads(match.group(1)))}


def main() -> int:
    evidence_dir = Path(os.environ.get("SERVICETRACER_SYNC_EVIDENCE_DIR", "servicetracer-targeted-reality-sync-evidence"))
    evidence_dir.mkdir(parents=True, exist_ok=False)
    started = observed_at()
    expected_subscription = os.environ["EXPECTED_TARGET_SUBSCRIPTION_ID"]
    expected_tenant = os.environ["EXPECTED_AZURE_TENANT_ID"]

    _, account, _ = az(["account", "show"])
    if account.get("id") != expected_subscription or account.get("tenantId") != expected_tenant or account.get("state") != "Enabled":
        raise RuntimeError("Azure account context does not match the protected target identity")
    account_record = {
        "subscription_name": account.get("name"),
        "subscription_sha256": digest(account.get("id")),
        "tenant_sha256": digest(account.get("tenantId")),
        "state": account.get("state"),
    }
    write(evidence_dir / "account.json", account_record)

    _, group, _ = az(["group", "show", "--name", RESOURCE_GROUP])
    _, resources, _ = az(["resource", "list", "--resource-group", RESOURCE_GROUP])
    inventory = {
        "resource_group": {"name": group.get("name"), "location": group.get("location"), "provisioning_state": group.get("properties", {}).get("provisioningState")},
        "resource_count": len(resources or []),
        "resources": [
            {"name": item.get("name"), "type": item.get("type"), "location": item.get("location"), "provisioning_state": item.get("properties", {}).get("provisioningState")}
            for item in (resources or [])
        ],
    }
    write(evidence_dir / "inventory.json", redact(inventory))

    _, vm, _ = az(["vm", "show", "--resource-group", RESOURCE_GROUP, "--name", VM_NAME, "--show-details"])
    _, instance_view, _ = az(["vm", "get-instance-view", "--resource-group", RESOURCE_GROUP, "--name", VM_NAME])
    vm_record = {
        "name": vm.get("name"),
        "location": vm.get("location"),
        "hardware_profile": vm.get("hardwareProfile"),
        "provisioning_state": vm.get("provisioningState"),
        "power_state": vm.get("powerState"),
        "public_ips": vm.get("publicIps"),
        "fqdn": vm.get("fqdns"),
        "identity_type": (vm.get("identity") or {}).get("type"),
        "statuses": (instance_view or {}).get("statuses"),
    }
    write(evidence_dir / "vm.json", redact(vm_record))

    _, deployments, _ = az(["deployment", "group", "list", "--resource-group", RESOURCE_GROUP])
    deployment_records = [
        {
            "name": item.get("name"),
            "provisioning_state": item.get("properties", {}).get("provisioningState"),
            "timestamp": item.get("properties", {}).get("timestamp"),
            "duration": item.get("properties", {}).get("duration"),
        }
        for item in (deployments or [])
    ]
    write(evidence_dir / "deployments.json", deployment_records)

    _, compute_usage, _ = az(["vm", "list-usage", "--location", LOCATION])
    _, network_usage, _ = az(["network", "list-usages", "--location", LOCATION])
    quota = {
        "location": LOCATION,
        "total_regional_vcpus": quota_record(compute_usage or [], ("cores", "total regional vcpus")),
        "standard_falsv7_family_vcpus": quota_record(compute_usage or [], ("standardfalsv7family", "standard falsv7 family vcpus")),
        "standard_ipv4_public_ips": quota_record(network_usage or [], ("PublicIPAddresses", "public ip addresses")),
    }
    write(evidence_dir / "quota.json", quota)

    health = public_health()
    write(evidence_dir / "public-health.json", health)
    guest = guest_observation()
    write(evidence_dir / "guest.json", guest)

    summary = {
        "schema_version": "servicetracer.targeted-reality-sync.v1",
        "started_at": started,
        "completed_at": observed_at(),
        "repository_sha": os.environ.get("GITHUB_SHA"),
        "target": {"resource_group": RESOURCE_GROUP, "vm": VM_NAME, "location": LOCATION, "fqdn": FQDN},
        "account": account_record,
        "inventory_resource_count": inventory["resource_count"],
        "vm_power_state": vm_record["power_state"],
        "public_health_status": health.get("status"),
        "public_health_http_status": health.get("http_status"),
        "guest_observation_status": guest.get("status"),
        "guest_source_ref": (guest.get("result") or {}).get("source_ref"),
        "guest_proxy_read_timeout_seconds": ((guest.get("result") or {}).get("nginx") or {}).get("proxy_read_timeout_seconds"),
        "azure_authentication_performed": True,
        "azure_control_plane_queries_performed": True,
        "guest_read_only_command_performed": guest.get("status") == "observed",
        "azure_resource_configuration_mutations_performed": False,
        "transaction_replay_performed": False,
        "deployment_performed": False,
        "cleanup_performed": False,
        "claim_boundary": "Read-only observation refreshes evidence; it does not deploy PR #84, prove least privilege, prove recovery, or authorize a transaction replay.",
    }
    write(evidence_dir / "summary.json", summary)
    manifest = [
        {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(evidence_dir.glob("*.json"))
    ]
    write(evidence_dir / "manifest.json", {"files": manifest})
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
