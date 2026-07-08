#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "run as root: sudo deploy/server/uninstall.sh" >&2
  exit 1
fi

install_root="${INSTALL_ROOT:-/opt/cdc-warehouse-platform}"
env_root="${ENV_ROOT:-/etc/cdc-warehouse}"

systemctl stop cdc-admin.service cdc-spark-streaming.service cdc-ops-refresh.service cdc-daily-merge.timer cdc-daily-merge.service 2>/dev/null || true
systemctl disable cdc-admin.service cdc-spark-streaming.service cdc-ops-refresh.service cdc-daily-merge.timer 2>/dev/null || true

rm -f /etc/systemd/system/cdc-admin.service
rm -f /etc/systemd/system/cdc-spark-streaming.service
rm -f /etc/systemd/system/cdc-ops-refresh.service
rm -f /etc/systemd/system/cdc-daily-merge.service
rm -f /etc/systemd/system/cdc-daily-merge.timer
systemctl daemon-reload

if [[ "${REMOVE_DATA:-false}" == "true" ]]; then
  rm -rf "${install_root}" "${env_root}" /var/log/cdc-warehouse
  echo "removed code, env, logs"
else
  echo "services removed"
  echo "kept ${install_root}, ${env_root}, /var/log/cdc-warehouse"
  echo "set REMOVE_DATA=true to remove data too"
fi
