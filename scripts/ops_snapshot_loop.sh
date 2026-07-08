#!/usr/bin/env bash
set -u

cd "$(dirname "$0")/.."
mkdir -p data/ops

while true; do
  bash scripts/refresh_ops_snapshot.sh >> data/ops/refresher.log 2>&1 || true
  sleep 5
done
