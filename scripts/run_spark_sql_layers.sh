#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

biz_dt="${1:-${BIZ_DT:-}}"
if [[ -z "${biz_dt}" ]]; then
  echo "usage: scripts/run_spark_sql_layers.sh <biz_dt>" >&2
  exit 2
fi

mkdir -p data/ops
bash deploy/run_job.sh layers "${biz_dt}" 2>&1 | tee -a data/ops/spark_sql_layers.log
