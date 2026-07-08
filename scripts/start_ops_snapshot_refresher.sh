#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/ops

pid_file="data/ops/refresher.pid"
log_file="data/ops/refresher.log"

if [[ -f "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" 2>/dev/null; then
  echo "ops refresher already running: $(cat "${pid_file}")"
  exit 0
fi

nohup bash scripts/ops_snapshot_loop.sh >/dev/null 2>&1 &

echo "$!" > "${pid_file}"
echo "ops refresher started: $(cat "${pid_file}")"
