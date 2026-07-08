#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "run as root: sudo deploy/server/install.sh" >&2
  exit 1
fi

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
install_root="${INSTALL_ROOT:-/opt/cdc-warehouse-platform}"
env_root="${ENV_ROOT:-/etc/cdc-warehouse}"
service_user="${SERVICE_USER:-cdc}"

id "${service_user}" >/dev/null 2>&1 || useradd --system --create-home --shell /sbin/nologin "${service_user}"

mkdir -p "${install_root}" "${env_root}" /var/log/cdc-warehouse
rsync -a --delete \
  --exclude .git \
  --exclude data/hdfs \
  --exclude data/hive \
  --exclude docker/hadoop/dist \
  --exclude docker/hive/dist \
  "${repo_root}/" "${install_root}/"

if [[ ! -f "${env_root}/admin.env" ]]; then
  cp "${install_root}/deploy/server/admin.env.example" "${env_root}/admin.env"
fi
if [[ ! -f "${env_root}/jobs.env" ]]; then
  cp "${install_root}/deploy/server/jobs.env.example" "${env_root}/jobs.env"
fi

chmod +x "${install_root}"/deploy/server/*.sh
chown -R "${service_user}:${service_user}" "${install_root}" /var/log/cdc-warehouse
chown root:"${service_user}" "${env_root}"/*.env
chmod 640 "${env_root}"/*.env

cd "${install_root}/platform/springboot-admin"
mvn -q -DskipTests package

cp "${install_root}"/deploy/server/*.service /etc/systemd/system/
cp "${install_root}"/deploy/server/*.timer /etc/systemd/system/
systemctl daemon-reload

echo "edit ${env_root}/admin.env and ${env_root}/jobs.env"
echo "then run:"
echo "  ${install_root}/deploy/server/control.sh start"
echo "  ${install_root}/deploy/server/control.sh health"
