#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage:
  deploy/run_job.sh [--env-file FILE] spark-streaming
  deploy/run_job.sh [--env-file FILE] realtime-streaming
  deploy/run_job.sh [--env-file FILE] daily-merge [biz_dt]
  deploy/run_job.sh [--env-file FILE] layers <biz_dt>
  deploy/run_job.sh [--env-file FILE] monitors [biz_dt]

Common env:
  PROJECT_ROOT, SPARK_MASTER, LAKE_ROOT, KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
  SPARK_STREAMING_CHECKPOINT, SPARK_STARTING_OFFSETS, SPARK_MAX_OFFSETS_PER_TRIGGER
  SPARK_BAD_RECORDS_PATH, SPARK_STREAMING_INTERVAL_SECONDS
  SPARK_SENSITIVE_RULES, SPARK_SENSITIVE_ALERT_PATH
  REALTIME_STREAMING_CHECKPOINT, REALTIME_MAX_OFFSETS_PER_TRIGGER
  PROGRESS_ROOT, DELAY_GATE_MAX_SECONDS, MERGE_AUDIT_ROOT, MERGE_BACKUP_ROOT, BIZ_DT
EOF
}

repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "${script_dir}/.." && pwd
}

load_env_file() {
  local env_file="$1"
  if [[ ! -f "${env_file}" && "${env_file}" != /* ]]; then
    env_file="$(repo_root)/${env_file}"
  fi
  if [[ ! -f "${env_file}" ]]; then
    echo "missing env file: ${env_file}" >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
}

find_pyspark_python() {
  local candidate
  for candidate in "${PYSPARK_PYTHON:-}" .venv/bin/python python3.11 python3.10 python3.9 python3.8 python3.7 python3 python; do
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

default_biz_dt() {
  python3 - <<'PY'
from datetime import date, timedelta
print((date.today() - timedelta(days=1)).isoformat())
PY
}

run_spark_streaming() {
  : "${KAFKA_BOOTSTRAP_SERVERS:?KAFKA_BOOTSTRAP_SERVERS is required}"
  : "${LAKE_ROOT:?LAKE_ROOT is required}"

  local checkpoint="${SPARK_STREAMING_CHECKPOINT:-${LAKE_ROOT%/}/checkpoints/offline_sink}"
  local command=(
    spark-submit
    --master "${SPARK_MASTER:-local[2]}"
    --packages "${SPARK_KAFKA_PACKAGE:-org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1}"
    streaming/offline_sink/pyspark_kafka_to_hdfs.py
    kafka
    "${KAFKA_BOOTSTRAP_SERVERS}"
    "${KAFKA_TOPIC:-cdc.incremental.binlog}"
    "${LAKE_ROOT}"
    "${checkpoint}"
    --starting-offsets "${SPARK_STARTING_OFFSETS:-latest}"
    --max-offsets-per-trigger "${SPARK_MAX_OFFSETS_PER_TRIGGER:-1000}"
    --trigger-seconds "${SPARK_STREAMING_INTERVAL_SECONDS:-5}"
  )

  if [[ -n "${SPARK_BAD_RECORDS_PATH:-}" ]]; then
    command+=(--bad-records-path "${SPARK_BAD_RECORDS_PATH}")
  fi
  if [[ -n "${SPARK_SENSITIVE_RULES:-}" ]]; then
    command+=(--sensitive-rules "${SPARK_SENSITIVE_RULES}")
  fi
  if [[ -n "${SPARK_SENSITIVE_ALERT_PATH:-}" ]]; then
    command+=(--sensitive-alert-path "${SPARK_SENSITIVE_ALERT_PATH}")
  fi
  if [[ -n "${PROGRESS_ROOT:-}" ]]; then
    command+=(--progress-root "${PROGRESS_ROOT}")
  fi

  "${command[@]}"
}

run_daily_merge() {
  local biz_dt="${1:-${BIZ_DT:-}}"
  if [[ -z "${biz_dt}" ]]; then
    biz_dt="$(default_biz_dt)"
  fi
  local lake_root="${LAKE_ROOT:-hdfs://localhost:8020/warehouse}"

  local pyspark_python
  pyspark_python="$(find_pyspark_python)" || {
    echo "pyspark python not found" >&2
    exit 1
  }

  PYSPARK_PYTHON="${pyspark_python}" PYSPARK_DRIVER_PYTHON="${pyspark_python}" \
    "${pyspark_python}" scripts/spark_sql_ods_merge_daily.py \
    --lake-root "${lake_root}" \
    --biz-dt "${biz_dt}" \
    --engine pyspark \
    --progress-root "${PROGRESS_ROOT:-data/progress}" \
    --max-delay-seconds "${DELAY_GATE_MAX_SECONDS:-1800}" \
    --audit-root "${MERGE_AUDIT_ROOT:-data/ops/merge_audit}" \
    --backup-root "${MERGE_BACKUP_ROOT:-${lake_root%/}/ods_backup}"
}

run_realtime_streaming() {
  : "${KAFKA_BOOTSTRAP_SERVERS:?KAFKA_BOOTSTRAP_SERVERS is required}"
  local command=(
    spark-submit
    --master "${SPARK_MASTER:-local[2]}"
    --packages "${SPARK_KAFKA_PACKAGE:-org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1}"
    streaming/realtime_sink/pyspark_kafka_to_kudu.py
    "${KAFKA_BOOTSTRAP_SERVERS}"
    "${KAFKA_TOPIC:-cdc.incremental.binlog}"
    "${REALTIME_STREAMING_CHECKPOINT:-${LAKE_ROOT:-hdfs://localhost:8020/warehouse}/checkpoints/realtime_kudu}"
    --master "${SPARK_MASTER:-local[2]}"
    --starting-offsets "${SPARK_STARTING_OFFSETS:-latest}"
    --max-offsets-per-trigger "${REALTIME_MAX_OFFSETS_PER_TRIGGER:-5000}"
    --trigger-seconds "${SPARK_STREAMING_INTERVAL_SECONDS:-5}"
  )
  "${command[@]}"
}

run_layers() {
  local biz_dt="${1:-${BIZ_DT:-}}"
  if [[ -z "${biz_dt}" ]]; then
    echo "layers requires biz_dt" >&2
    usage
    exit 2
  fi

  local pyspark_python
  pyspark_python="$(find_pyspark_python)" || {
    echo "pyspark python not found" >&2
    exit 1
  }

  PYSPARK_PYTHON="${pyspark_python}" PYSPARK_DRIVER_PYTHON="${pyspark_python}" \
    "${pyspark_python}" warehouse/jobs/pyspark_layer_sql.py \
    --lake-root "${LAKE_ROOT:-hdfs://localhost:8020/warehouse}" \
    --biz-dt "${biz_dt}"
}

run_monitors() {
  local biz_dt="${1:-${BIZ_DT:-}}"
  if [[ -z "${biz_dt}" ]]; then
    biz_dt="$(default_biz_dt)"
  fi
  spark-submit \
    --master "${SPARK_MASTER:-local[2]}" \
    monitors/run_monitor_suite.py \
    --biz-dt "${biz_dt}" \
    --lake-root "${LAKE_ROOT:-hdfs://localhost:8020/warehouse}" \
    --master "${SPARK_MASTER:-local[2]}"
}

env_file=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      env_file="${2:-}"
      if [[ -z "${env_file}" ]]; then
        usage
        exit 2
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

if [[ -n "${env_file}" ]]; then
  load_env_file "${env_file}"
fi

cd "${PROJECT_ROOT:-$(repo_root)}"
mkdir -p data/ops

job="$1"
shift

case "${job}" in
  spark-streaming)
    run_spark_streaming "$@"
    ;;
  realtime-streaming)
    run_realtime_streaming "$@"
    ;;
  daily-merge)
    run_daily_merge "$@"
    ;;
  layers)
    run_layers "$@"
    ;;
  monitors)
    run_monitors "$@"
    ;;
  *)
    echo "unknown job: ${job}" >&2
    usage
    exit 2
    ;;
esac
