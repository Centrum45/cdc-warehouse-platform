#!/usr/bin/env bash
set -euo pipefail

env_root="${ENV_ROOT:-/etc/cdc-warehouse}"
project_root="${PROJECT_ROOT:-/opt/cdc-warehouse-platform}"
admin_env="${env_root}/admin.env"
jobs_env="${env_root}/jobs.env"
biz_dt="${BIZ_DT:-$(date -d yesterday +%F)}"
run_merge="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --merge)
      run_merge="true"
      shift
      ;;
    --biz-dt)
      biz_dt="$2"
      shift 2
      ;;
    *)
      echo "usage: $0 [--biz-dt yyyy-mm-dd] [--merge]" >&2
      exit 2
      ;;
  esac
done

ok=0
fail=0
warn=0

pass() {
  printf '[OK]   %s\n' "$1"
  ok=$((ok + 1))
}

bad() {
  printf '[FAIL] %s\n' "$1"
  fail=$((fail + 1))
}

note() {
  printf '[WARN] %s\n' "$1"
  warn=$((warn + 1))
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

hdfs_path_root() {
  local root="${WAREHOUSE_HDFS_ROOT:-${LAKE_ROOT:-/warehouse}}"
  if [[ "${root}" == hdfs://* ]]; then
    root="${root#hdfs://*/}"
    root="/${root#/}"
  fi
  echo "${root%/}"
}

check_hdfs_path() {
  local label="$1"
  local path="$2"
  if command -v hdfs >/dev/null 2>&1; then
    if hdfs dfs -test -e "${path}" >/dev/null 2>&1; then
      pass "${label}: ${path}"
    else
      note "${label} missing: ${path}"
    fi
  else
    note "skip ${label}, hdfs command not found"
  fi
}

check_hive_count() {
  local label="$1"
  local sql="$2"
  if command -v beeline >/dev/null 2>&1 && [[ -n "${HIVE_JDBC_URL:-}" ]]; then
    if beeline -u "${HIVE_JDBC_URL}" --silent=true --showHeader=false -e "${sql}" >/tmp/cdc_smoke_hive.out 2>/tmp/cdc_smoke_hive.err; then
      pass "${label}: $(tr -d '[:space:]' </tmp/cdc_smoke_hive.out | tail -c 80)"
    else
      note "${label} query failed: $(tail -n 1 /tmp/cdc_smoke_hive.err 2>/dev/null || true)"
    fi
  else
    note "skip ${label}, beeline/HIVE_JDBC_URL not ready"
  fi
}

load_env "${admin_env}"
load_env "${jobs_env}"

cd "${project_root}"

echo "biz_dt=${biz_dt}"
echo "project_root=${project_root}"

if deploy/server/control.sh health; then
  pass "control health"
else
  bad "control health"
fi

if [[ "${run_merge}" == "true" ]]; then
  echo "run daily merge for ${biz_dt}"
  systemctl set-environment "BIZ_DT=${biz_dt}"
  if systemctl start cdc-daily-merge.service; then
    pass "start cdc-daily-merge.service"
  else
    bad "start cdc-daily-merge.service"
  fi
  systemctl unset-environment BIZ_DT || true
  if systemctl is-failed --quiet cdc-daily-merge.service; then
    bad "cdc-daily-merge.service failed"
    journalctl -u cdc-daily-merge.service -n 120 --no-pager || true
  else
    pass "cdc-daily-merge.service not failed"
  fi
else
  note "skip merge; pass --merge to run daily merge"
fi

hdfs_root="$(hdfs_path_root)"
check_hdfs_path "ODS binlog partition" "${hdfs_root}/ods_binlog/db=basiccomment/table=avatar_commentbatchsource/dt=${biz_dt}"
check_hdfs_path "ODS snapshot partition" "${hdfs_root}/ods/db=basiccomment/table=avatar_commentbatchsource/dt=${biz_dt}"
check_hdfs_path "ADS comment dashboard partition" "${hdfs_root}/ads/ads_comment_dashboard_1d/dt=${biz_dt}"

check_hive_count "Hive ODS count" "select count(1) from ods.ods_basiccomment_avatar_commentbatchsource_dic where dt='${biz_dt}';"
check_hive_count "Hive ADS count" "select count(1) from ads.ads_comment_dashboard_1d where dt='${biz_dt}';"

printf '\nsummary: ok=%d warn=%d fail=%d\n' "${ok}" "${warn}" "${fail}"
[[ "${fail}" -eq 0 ]]
