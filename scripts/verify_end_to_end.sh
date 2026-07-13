#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mode="local"
biz_dt="${BIZ_DT:-}"
run_realtime="false"
ops_log="data/ops/verify_end_to_end.log"

usage() {
  cat <<'EOF'
usage: scripts/verify_end_to_end.sh [--mode local|server] [--biz-dt yyyy-mm-dd] [--with-realtime]

local mode:
  Verifies Docker local chain:
  MySQL -> Maxwell -> Kafka -> SparkStreaming -> HDFS -> ODS merge -> Hive ODS -> ADS -> SpringBoot.

server mode:
  Runs deploy/server/control.sh health and smoke against a server deployment.

env:
  BIZ_DT            business date, default yesterday
  TEST_ID           optional local E2E test id
  LAKE_ROOT         default hdfs://localhost:8020/warehouse for local merge
  ADMIN_URL         default http://localhost:8080/api/dashboard
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    --biz-dt)
      biz_dt="${2:-}"
      shift 2
      ;;
    --with-realtime)
      run_realtime="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${biz_dt}" ]]; then
  biz_dt="$(python3 -c 'from datetime import date,timedelta; print((date.today()-timedelta(days=1)).isoformat())')"
fi

mkdir -p data/ops
: > "${ops_log}"

ok=0
fail=0

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${ops_log}"
}

pass() {
  ok=$((ok + 1))
  log "OK   $*"
}

bad() {
  fail=$((fail + 1))
  log "FAIL $*"
}

run_step() {
  local name="$1"
  shift
  log "STEP ${name}"
  if "$@" >> "${ops_log}" 2>&1; then
    pass "${name}"
  else
    bad "${name}"
    log "last log lines:"
    tail -n 80 "${ops_log}" || true
    return 1
  fi
}

capture_diagnostics() {
  log "capture diagnostics"
  {
    echo "== docker ps =="
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || true
    echo
    echo "== springboot dashboard =="
    curl -fsS "${ADMIN_URL:-http://localhost:8080/api/dashboard}" 2>/dev/null || true
    echo
  } > data/ops/verify_diagnostics.txt

  for name in cdc-warehouse-mysql cdc-warehouse-maxwell cdc-warehouse-kafka cdc-warehouse-spark-streaming cdc-warehouse-hive-server cdc-warehouse-admin; do
    docker logs --tail 160 "${name}" > "data/ops/${name}.verify.log" 2>&1 || true
  done
}

verify_local() {
  log "verify local E2E biz_dt=${biz_dt}"
  run_step "local full CDC warehouse E2E" env BIZ_DT="${biz_dt}" ./scripts/run_e2e_hdfs_pipeline.sh || return 1
  run_step "local stack health summary" env BIZ_DT="${biz_dt}" ./scripts/check_local_stack.sh || return 1
  run_step "SpringBoot dashboard API" curl -fsS "${ADMIN_URL:-http://localhost:8080/api/dashboard}" || return 1
  if [[ "${run_realtime}" == "true" ]]; then
    run_step "realtime Kudu/Impala smoke" ./scripts/run_local_kudu_impala_smoke.sh || return 1
  fi
}

verify_server() {
  log "verify server deployment biz_dt=${biz_dt}"
  local control="${CONTROL_SH:-deploy/server/control.sh}"
  if [[ ! -x "${control}" ]]; then
    chmod +x "${control}" 2>/dev/null || true
  fi
  run_step "server health" "${control}" health || return 1
  run_step "server smoke" "${control}" smoke --biz-dt "${biz_dt}" --merge || return 1
  if [[ "${run_realtime}" == "true" ]]; then
    run_step "realtime Kudu/Impala smoke" python3 scripts/run_realtime_kudu_smoke.py || return 1
  fi
}

case "${mode}" in
  local)
    if verify_local; then
      pass "end-to-end verification complete"
    else
      capture_diagnostics
      exit 1
    fi
    ;;
  server)
    if verify_server; then
      pass "server verification complete"
    else
      capture_diagnostics
      exit 1
    fi
    ;;
  *)
    echo "invalid mode: ${mode}" >&2
    usage >&2
    exit 2
    ;;
esac

capture_diagnostics
log "summary ok=${ok} fail=${fail}"
log "main log: ${ops_log}"
log "diagnostics: data/ops/verify_diagnostics.txt"

[[ "${fail}" -eq 0 ]]
