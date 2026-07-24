#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <repository> <40-char-ref> <fqdn> <backend-transaction-url> <allowed-origin>" >&2
  exit 2
}

[[ $# -eq 5 ]] || usage
SOURCE_REPOSITORY="$1"
SOURCE_REF="$2"
PUBLIC_FQDN="$3"
BACKEND_TRANSACTION_URL="$4"
ALLOWED_ORIGIN="$5"

[[ "$SOURCE_REPOSITORY" =~ ^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$ ]] || usage
[[ "$SOURCE_REF" =~ ^[0-9a-f]{40}$ ]] || usage
[[ "$PUBLIC_FQDN" =~ ^[a-z0-9][a-z0-9.-]+[a-z0-9]$ ]] || usage
[[ "$BACKEND_TRANSACTION_URL" =~ ^https://[A-Za-z0-9.:-]+/transaction$ ]] || usage
[[ "$ALLOWED_ORIGIN" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?$ ]] || usage

SOURCE_ROOT='/opt/servicetracer-demo-api-src'
APP_ROOT='/opt/servicetracer-demo-api'
CONFIG_ROOT='/etc/servicetracer-demo-api'
ENV_FILE="${CONFIG_ROOT}/service.env"
SERVICE_NAME='servicetracer-demo-api.service'
LOCAL_PORT='8090'

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  certbot \
  curl \
  git \
  nginx \
  python3 \
  python3-certbot-nginx

if ! getent group servicetracer-api >/dev/null; then
  groupadd --system servicetracer-api
fi
if ! id servicetracer-api >/dev/null 2>&1; then
  useradd --system --gid servicetracer-api --home-dir /var/lib/servicetracer-api --shell /usr/sbin/nologin servicetracer-api
fi

rm -rf "${SOURCE_ROOT}.new"
git init "${SOURCE_ROOT}.new"
git -C "${SOURCE_ROOT}.new" remote add origin "$SOURCE_REPOSITORY"
git -C "${SOURCE_ROOT}.new" fetch --depth 1 origin "$SOURCE_REF"
git -C "${SOURCE_ROOT}.new" checkout --detach FETCH_HEAD
[[ "$(git -C "${SOURCE_ROOT}.new" rev-parse HEAD)" == "$SOURCE_REF" ]]
rm -rf "$SOURCE_ROOT"
mv "${SOURCE_ROOT}.new" "$SOURCE_ROOT"

install -d -o root -g servicetracer-api -m 0750 "$APP_ROOT" "$CONFIG_ROOT"
install -o root -g servicetracer-api -m 0640 "$SOURCE_ROOT/demo_api/core.py" "$APP_ROOT/core.py"
install -o root -g servicetracer-api -m 0640 "$SOURCE_ROOT/demo_api/runtime.py" "$APP_ROOT/runtime.py"
install -o root -g servicetracer-api -m 0640 "$SOURCE_ROOT/demo_api/standalone_server.py" "$APP_ROOT/standalone_server.py"

umask 0027
cat > "$ENV_FILE" <<EOF_ENV
SERVICETRACER_BACKEND_TRANSACTION_URL=${BACKEND_TRANSACTION_URL}
SERVICETRACER_ALLOWED_ORIGIN=${ALLOWED_ORIGIN}
SERVICETRACER_SOURCE_ID=${PUBLIC_FQDN}
SERVICETRACER_DEMO_API_LISTEN=127.0.0.1
SERVICETRACER_DEMO_API_PORT=${LOCAL_PORT}
SERVICETRACER_HOSTING_MODEL=dedicated_vm_subproject
EOF_ENV
chown root:servicetracer-api "$ENV_FILE"
chmod 0640 "$ENV_FILE"

cat > "/etc/systemd/system/${SERVICE_NAME}" <<EOF_SERVICE
[Unit]
Description=ServiceTracer demo API independent workload
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=servicetracer-api
Group=servicetracer-api
EnvironmentFile=${ENV_FILE}
WorkingDirectory=${APP_ROOT}
ExecStart=/usr/bin/python3 ${APP_ROOT}/standalone_server.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_INET AF_INET6
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
EOF_SERVICE

cat > /etc/nginx/conf.d/servicetracer-demo-api-rate-limit.conf <<'EOF_RATE'
limit_req_zone $binary_remote_addr zone=servicetracer_demo_api:10m rate=6r/m;
EOF_RATE

rm -f /etc/nginx/sites-enabled/default
cat > /etc/nginx/sites-available/servicetracer-demo-api <<EOF_NGINX
server {
    listen 80;
    listen [::]:80;
    server_name ${PUBLIC_FQDN};

    location /api/ {
        limit_req zone=servicetracer_demo_api burst=2 nodelay;
        proxy_pass http://127.0.0.1:${LOCAL_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 45s;
        client_max_body_size 4k;
    }

    location / {
        return 404;
    }
}
EOF_NGINX
ln -sfn /etc/nginx/sites-available/servicetracer-demo-api /etc/nginx/sites-enabled/servicetracer-demo-api

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
nginx -t
systemctl enable --now nginx
systemctl reload nginx

for _ in $(seq 1 60); do
  if getent ahostsv4 "$PUBLIC_FQDN" >/dev/null 2>&1; then
    break
  fi
  sleep 5
done
getent ahostsv4 "$PUBLIC_FQDN" >/dev/null

certbot --nginx \
  --non-interactive \
  --agree-tos \
  --register-unsafely-without-email \
  --redirect \
  --keep-until-expiring \
  --domain "$PUBLIC_FQDN"

nginx -t
systemctl reload nginx

for _ in $(seq 1 60); do
  if curl --fail --silent --show-error "https://${PUBLIC_FQDN}/api/health" > /tmp/servicetracer-demo-api-health.json; then
    python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('/tmp/servicetracer-demo-api-health.json').read_text(encoding='utf-8'))
if payload.get('status') != 'healthy' or payload.get('hosting_model') != 'dedicated_vm_subproject':
    raise SystemExit(f'Unexpected health response: {payload!r}')
PY
    exit 0
  fi
  sleep 5
done

systemctl status "$SERVICE_NAME" --no-pager >&2 || true
journalctl -u "$SERVICE_NAME" --no-pager -n 100 >&2 || true
journalctl -u nginx --no-pager -n 100 >&2 || true
exit 1
