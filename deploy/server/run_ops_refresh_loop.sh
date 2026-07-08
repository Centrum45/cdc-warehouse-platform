#!/usr/bin/env bash
set -euo pipefail

cd "${PROJECT_ROOT:-/opt/cdc-warehouse-platform}"
mkdir -p data/ops

interval="${OPS_REFRESH_INTERVAL_SECONDS:-5}"
while true; do
  deploy/server/refresh_ops_snapshot_server.sh >> data/ops/refresher.log 2>&1 || true
  sleep "${interval}"
done
