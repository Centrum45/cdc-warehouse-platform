#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/ops

biz_dt="${1:-${BIZ_DT:-}}"
if [[ -n "${biz_dt}" ]]; then
  bash deploy/run_job.sh daily-merge "${biz_dt}" 2>&1 | tee -a data/ops/spark_sql_merge.log
else
  bash deploy/run_job.sh daily-merge 2>&1 | tee -a data/ops/spark_sql_merge.log
fi
