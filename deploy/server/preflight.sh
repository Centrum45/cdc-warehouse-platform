#!/usr/bin/env bash
set -euo pipefail

admin_env="${1:-/etc/cdc-warehouse/admin.env}"
jobs_env="${2:-/etc/cdc-warehouse/jobs.env}"

failures=0

fail() {
  echo "FAIL $*"
  failures=$((failures + 1))
}

pass() {
  echo "OK   $*"
}

load_env() {
  local file="$1"
  if [[ ! -f "${file}" ]]; then
    fail "missing env file: ${file}"
    return 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "${file}"
  set +a
}

require_value() {
  local name="$1"
  local value="${!name:-}"
  if [[ -z "${value}" || "${value}" == *"<"*">"* ]]; then
    fail "${name} is empty or placeholder"
  else
    pass "${name}"
  fi
}

load_env "${admin_env}" || true
load_env "${jobs_env}" || true

for name in SPRING_PROFILES_ACTIVE WAREHOUSE_PROJECT_ROOT DB_HOST DB_NAME DB_USER DB_PASSWORD ADMIN_USER ADMIN_PASS JWT_SECRET HIVE_JDBC_URL; do
  require_value "${name}"
done

if [[ "${SPRING_PROFILES_ACTIVE:-}" != "prod" ]]; then
  fail "SPRING_PROFILES_ACTIVE must be prod"
fi

if [[ "${WAREHOUSE_ACTIONS_PUBLIC_ENABLED:-false}" != "false" ]]; then
  fail "WAREHOUSE_ACTIONS_PUBLIC_ENABLED must be false in production"
fi

if [[ "${ADMIN_PASS:-}" == "admin123" ]]; then
  fail "ADMIN_PASS must not use default admin123"
fi

jwt_secret="${JWT_SECRET:-}"
if [[ "${#jwt_secret}" -lt 32 ]]; then
  fail "JWT_SECRET must be at least 32 characters"
fi

for cmd in java python3 bash; do
  if command -v "${cmd}" >/dev/null 2>&1; then
    pass "command ${cmd}"
  else
    fail "missing command ${cmd}"
  fi
done

if [[ -d "${WAREHOUSE_PROJECT_ROOT:-}" ]]; then
  pass "project root exists"
else
  fail "project root missing: ${WAREHOUSE_PROJECT_ROOT:-}"
fi

if [[ "${failures}" -gt 0 ]]; then
  echo "preflight failed: ${failures}"
  exit 1
fi

echo "preflight passed"
