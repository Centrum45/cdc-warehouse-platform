#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
env_file="${1:-deploy/prod/jobs.env}"

if [[ ! -f "${env_file}" ]]; then
  echo "missing env file: ${env_file}" >&2
  echo "copy deploy/prod/jobs.env.example first" >&2
  exit 1
fi

set -a
source "${env_file}"
set +a

biz_dt="${BIZ_DT:-${2:-}}"
if [[ -z "${biz_dt}" ]]; then
  echo "usage: $0 [env-file] <biz_dt>" >&2
  exit 1
fi

python3 scripts/spark_sql_ods_merge_daily.py \
  --lake-root "${LAKE_ROOT}" \
  --biz-dt "${biz_dt}" \
  --engine pyspark \
  --progress-root "${PROGRESS_ROOT}" \
  --max-delay-seconds "${DELAY_GATE_MAX_SECONDS}"
