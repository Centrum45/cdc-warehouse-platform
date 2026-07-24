#!/usr/bin/env bash
set -euo pipefail

dry_run="false"
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run="true"
  shift
fi

if [[ "${dry_run}" != "true" && "$(id -u)" -ne 0 ]]; then
  echo "run as root: sudo deploy/server/install.sh" >&2
  exit 1
fi

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
install_root="${INSTALL_ROOT:-/opt/cdc-warehouse-platform}"
env_root="${ENV_ROOT:-/etc/cdc-warehouse}"
service_user="${SERVICE_USER:-cdc}"

run() {
  if [[ "${dry_run}" == "true" ]]; then
    printf '+'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

need_file() {
  if [[ ! -f "$1" ]]; then
    echo "missing required file: $1" >&2
    exit 1
  fi
}

need_file "${repo_root}/deploy/server/admin.env.example"
need_file "${repo_root}/deploy/server/jobs.env.example"
need_file "${repo_root}/deploy/server/cdc-admin.service"
need_file "${repo_root}/deploy/server/cdc-spark-streaming.service"
need_file "${repo_root}/deploy/server/cdc-realtime-streaming.service"
need_file "${repo_root}/deploy/server/cdc-monitor.timer"
need_file "${repo_root}/deploy/server/cdc-daily-merge.timer"
need_file "${repo_root}/platform/springboot-admin/pom.xml"

if [[ "${dry_run}" == "true" ]]; then
  echo "dry run install"
  echo "repo_root=${repo_root}"
  echo "install_root=${install_root}"
  echo "env_root=${env_root}"
  echo "service_user=${service_user}"
fi

if ! id "${service_user}" >/dev/null 2>&1; then
  run useradd --system --create-home --shell /sbin/nologin "${service_user}"
fi

run mkdir -p "${install_root}" "${env_root}" /var/log/cdc-warehouse
if [[ "${dry_run}" == "true" ]]; then
  echo "+ rsync -a --delete --exclude .git --exclude data/hdfs --exclude data/hive --exclude docker/hadoop/dist --exclude docker/hive/dist ${repo_root}/ ${install_root}/"
else
  rsync -a --delete \
    --exclude .git \
    --exclude data/hdfs \
    --exclude data/hive \
    --exclude docker/hadoop/dist \
    --exclude docker/hive/dist \
    "${repo_root}/" "${install_root}/"
fi

if [[ ! -f "${env_root}/admin.env" ]]; then
  run cp "${install_root}/deploy/server/admin.env.example" "${env_root}/admin.env"
fi
if [[ ! -f "${env_root}/jobs.env" ]]; then
  run cp "${install_root}/deploy/server/jobs.env.example" "${env_root}/jobs.env"
fi

if [[ "${dry_run}" == "true" ]]; then
  echo "+ chmod +x ${install_root}/deploy/server/*.sh"
  echo "+ chown -R ${service_user}:${service_user} ${install_root} /var/log/cdc-warehouse"
  echo "+ chown root:${service_user} ${env_root}/*.env"
  echo "+ chmod 640 ${env_root}/*.env"
else
  chmod +x "${install_root}"/deploy/server/*.sh
  chown -R "${service_user}:${service_user}" "${install_root}" /var/log/cdc-warehouse
  chown root:"${service_user}" "${env_root}"/*.env
  chmod 640 "${env_root}"/*.env
fi

if [[ "${dry_run}" == "true" ]]; then
  echo "+ cd ${install_root}/platform/springboot-admin"
  echo "+ mvn -q -DskipTests package"
else
  cd "${install_root}/platform/springboot-admin"
  mvn -q -DskipTests package
fi

if [[ "${dry_run}" == "true" ]]; then
  echo "+ cp ${install_root}/deploy/server/*.service /etc/systemd/system/"
  echo "+ cp ${install_root}/deploy/server/*.timer /etc/systemd/system/"
  echo "+ systemctl daemon-reload"
else
  cp "${install_root}"/deploy/server/*.service /etc/systemd/system/
  cp "${install_root}"/deploy/server/*.timer /etc/systemd/system/
  systemctl daemon-reload
fi

echo "edit ${env_root}/admin.env and ${env_root}/jobs.env"
echo "then run:"
echo "  ${install_root}/deploy/server/control.sh preflight"
echo "  ${install_root}/deploy/server/control.sh start"
echo "  ${install_root}/deploy/server/control.sh health"
