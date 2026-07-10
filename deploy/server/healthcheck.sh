#!/usr/bin/env bash
set -euo pipefail

env_root="${ENV_ROOT:-/etc/cdc-warehouse}"
project_root="${PROJECT_ROOT:-/opt/cdc-warehouse-platform}"
admin_env="${env_root}/admin.env"
jobs_env="${env_root}/jobs.env"

ok=0
fail=0

pass() {
  printf '[OK]   %s\n' "$1"
  ok=$((ok + 1))
}

warn() {
  printf '[WARN] %s\n' "$1"
}

bad() {
  printf '[FAIL] %s\n' "$1"
  fail=$((fail + 1))
}

load_env() {
  local file="$1"
  local key
  local value
  if [[ -f "${file}" ]]; then
    while IFS= read -r line || [[ -n "${line}" ]]; do
      [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue
      [[ "${line}" != *=* ]] && continue
      key="${line%%=*}"
      value="${line#*=}"
      [[ "${key}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
      export "${key}=${value}"
    done < "${file}"
    pass "loaded ${file}"
  else
    bad "missing ${file}"
  fi
}

check_cmd() {
  local cmd="$1"
  if command -v "${cmd}" >/dev/null 2>&1; then
    pass "command ${cmd}"
  else
    bad "command ${cmd} not found"
  fi
}

check_optional_cmd() {
  local cmd="$1"
  if command -v "${cmd}" >/dev/null 2>&1; then
    pass "command ${cmd}"
  else
    warn "command ${cmd} not found"
  fi
}

check_service() {
  local service="$1"
  if systemctl is-active --quiet "${service}"; then
    pass "service ${service} active"
  else
    warn "service ${service} inactive"
  fi
}

load_env "${admin_env}"
load_env "${jobs_env}"

[[ -d "${project_root}" ]] && pass "project root ${project_root}" || bad "project root ${project_root} missing"
[[ -f "${project_root}/platform/springboot-admin/target/cdc-warehouse-admin-0.1.0.jar" ]] && pass "admin jar exists" || bad "admin jar missing, run deploy/server/install.sh"

check_cmd java
check_cmd python3
check_optional_cmd mvn
check_optional_cmd kafka-topics
check_optional_cmd kafka-console-consumer
check_optional_cmd hdfs
check_optional_cmd beeline
check_optional_cmd curl
check_optional_cmd mysql

check_service cdc-admin.service
check_service cdc-spark-streaming.service
check_service cdc-ops-refresh.service
systemctl list-timers --all cdc-daily-merge.timer --no-pager >/dev/null 2>&1 && pass "timer cdc-daily-merge visible" || warn "timer cdc-daily-merge not visible"

if command -v curl >/dev/null 2>&1; then
  port="${SERVER_PORT:-8080}"
  if curl -fsS "http://127.0.0.1:${port}/api/dashboard" >/dev/null 2>&1; then
    pass "admin HTTP http://127.0.0.1:${port}/api/dashboard"
  else
    warn "admin HTTP not reachable on port ${port}"
  fi
fi

if command -v mysql >/dev/null 2>&1 && [[ -n "${DB_HOST:-}" ]]; then
  if MYSQL_PWD="${DB_PASSWORD:-}" mysql -h"${DB_HOST}" -P"${DB_PORT:-3306}" -u"${DB_USER}" -e 'select 1' "${DB_NAME}" >/dev/null 2>&1; then
    pass "MySQL select 1"
  else
    bad "MySQL select 1 failed"
  fi
fi

if command -v kafka-topics >/dev/null 2>&1 && [[ -n "${KAFKA_BOOTSTRAP_SERVERS:-}" ]]; then
  if kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP_SERVERS}" --list >/dev/null 2>&1; then
    pass "Kafka topic list"
  else
    bad "Kafka topic list failed"
  fi
fi

if command -v hdfs >/dev/null 2>&1 && [[ -n "${WAREHOUSE_HDFS_ROOT:-}" ]]; then
  if hdfs dfs -ls "${WAREHOUSE_HDFS_ROOT}" >/dev/null 2>&1; then
    pass "HDFS ls ${WAREHOUSE_HDFS_ROOT}"
  else
    bad "HDFS ls ${WAREHOUSE_HDFS_ROOT} failed"
  fi
fi

if command -v beeline >/dev/null 2>&1 && [[ -n "${HIVE_JDBC_URL:-}" ]]; then
  if beeline -u "${HIVE_JDBC_URL}" -e 'show databases' >/dev/null 2>&1; then
    pass "Hive show databases"
  else
    bad "Hive show databases failed"
  fi
fi

printf '\nsummary: ok=%d fail=%d\n' "${ok}" "${fail}"
[[ "${fail}" -eq 0 ]]
