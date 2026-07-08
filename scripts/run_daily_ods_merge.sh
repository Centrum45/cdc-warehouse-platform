#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/ops

biz_dt="${1:-${BIZ_DT:-}}"
lake_root="${LAKE_ROOT:-hdfs://localhost:8020/warehouse}"
if [[ -n "${biz_dt}" ]]; then
  python3 scripts/spark_sql_ods_merge_daily.py --lake-root "${lake_root}" --biz-dt "${biz_dt}" --engine pyspark 2>&1 | tee -a data/ops/spark_sql_merge.log
else
  python3 scripts/spark_sql_ods_merge_daily.py --lake-root "${lake_root}" --engine pyspark 2>&1 | tee -a data/ops/spark_sql_merge.log
fi
