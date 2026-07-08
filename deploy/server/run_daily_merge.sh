#!/usr/bin/env bash
set -euo pipefail

cd "${PROJECT_ROOT:-/opt/cdc-warehouse-platform}"
mkdir -p data/ops

biz_dt="${BIZ_DT:-$(date -d yesterday +%F)}"

python3 scripts/spark_sql_ods_merge_daily.py \
  --lake-root "${LAKE_ROOT}" \
  --biz-dt "${biz_dt}" \
  --engine pyspark \
  --progress-root "${PROGRESS_ROOT:-data/progress}" \
  --max-delay-seconds "${DELAY_GATE_MAX_SECONDS:-1800}" \
  2>&1 | tee -a data/ops/spark_sql_merge.log
