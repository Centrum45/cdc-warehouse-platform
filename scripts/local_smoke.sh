#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ops_log="data/ops/local_smoke.log"
mkdir -p data/ops
: > "${ops_log}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${ops_log}"
}

run_step() {
  local name="$1"
  shift
  log "START ${name}"
  "$@" 2>&1 | tee -a "${ops_log}"
  log "OK ${name}"
}

log "local smoke start"
run_step "docker up" ./scripts/docker_up.sh
run_step "init hdfs hive" ./scripts/init_hdfs_hive.sh
run_step "e2e hdfs pipeline" ./scripts/run_e2e_hdfs_pipeline.sh
run_step "local stack health" ./scripts/check_local_stack.sh
log "local smoke done"
echo "log: ${ops_log}"
