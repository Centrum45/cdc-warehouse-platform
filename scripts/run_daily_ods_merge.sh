#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/ops

biz_dt="${1:-${BIZ_DT:-}}"
lake_root="${LAKE_ROOT:-hdfs://localhost:8020/warehouse}"

find_pyspark_python() {
  for candidate in "${PYSPARK_PYTHON:-}" python3 /Library/Frameworks/Python.framework/Versions/3.7/bin/python3; do
    if [[ -z "${candidate}" ]]; then
      continue
    fi
    if command -v "${candidate}" >/dev/null 2>&1 && "${candidate}" -c 'import pyspark' >/dev/null 2>&1; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

pyspark_python="$(find_pyspark_python)" || {
  echo "pyspark python not found" | tee -a data/ops/spark_sql_merge.log
  exit 1
}

if [[ -n "${biz_dt}" ]]; then
  PYSPARK_PYTHON="${pyspark_python}" PYSPARK_DRIVER_PYTHON="${pyspark_python}" "${pyspark_python}" scripts/spark_sql_ods_merge_daily.py --lake-root "${lake_root}" --biz-dt "${biz_dt}" --engine pyspark 2>&1 | tee -a data/ops/spark_sql_merge.log
else
  PYSPARK_PYTHON="${pyspark_python}" PYSPARK_DRIVER_PYTHON="${pyspark_python}" "${pyspark_python}" scripts/spark_sql_ods_merge_daily.py --lake-root "${lake_root}" --engine pyspark 2>&1 | tee -a data/ops/spark_sql_merge.log
fi
