#!/usr/bin/env bash
set -euo pipefail

cd "${PROJECT_ROOT:-/opt/cdc-warehouse-platform}"
mkdir -p data/kafka data/checkpoints data/progress data/ops

python3 scripts/spark_streaming_kafka_to_hdfs_loop.py \
  --topic "${KAFKA_TOPIC:-cdc.incremental.binlog}" \
  --bootstrap-server "${KAFKA_BOOTSTRAP_SERVERS}" \
  --lake-root "${LAKE_ROOT}" \
  --checkpoint "${SPARK_STREAMING_CHECKPOINT:-data/checkpoints/offline_sink.json}" \
  --rules "${SENSITIVE_RULES:-metadata/rules/sensitive_columns.json}" \
  --progress-root "${PROGRESS_ROOT:-data/progress}" \
  --work-root "${SPARK_STREAMING_WORK_ROOT:-data/kafka}" \
  --interval-seconds "${SPARK_STREAMING_INTERVAL_SECONDS:-5}" \
  --max-messages "${SPARK_STREAMING_MAX_MESSAGES:-500}" \
  --timeout-ms "${SPARK_STREAMING_TIMEOUT_MS:-10000}"
