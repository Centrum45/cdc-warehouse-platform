#!/usr/bin/env bash
set -euo pipefail

cd "${PROJECT_ROOT:-/opt/cdc-warehouse-platform}"
mkdir -p data/ops

{
  echo "NAMES     STATUS    PORTS"
  systemctl --no-pager --plain is-active cdc-admin.service cdc-spark-streaming.service cdc-ops-refresh.service 2>/dev/null \
    | paste <(printf "cdc-admin\ncdc-spark-streaming\ncdc-ops-refresh\n") - \
    | awk '{print $1 "     " $2 "    -"}'
} > data/ops/container_status.txt

journalctl -u cdc-admin -n 120 --no-pager > data/ops/admin.log 2>&1 || true
journalctl -u cdc-spark-streaming -n 120 --no-pager > data/ops/spark_streaming.log 2>&1 || true
journalctl -u cdc-daily-merge -n 120 --no-pager > data/ops/spark_sql_merge.log 2>&1 || true

if command -v kafka-topics >/dev/null 2>&1; then
  kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP_SERVERS}" --list > data/ops/kafka_topics.txt 2>&1 || true
else
  echo "kafka-topics not found" > data/ops/kafka_topics.txt
fi

if command -v hdfs >/dev/null 2>&1; then
  hdfs dfs -ls -R "${HDFS_WAREHOUSE_PATH:-/warehouse}" > data/ops/hdfs_warehouse_ls.txt 2>&1 || true
else
  echo "hdfs command not found" > data/ops/hdfs_warehouse_ls.txt
fi

if command -v beeline >/dev/null 2>&1; then
  beeline -u "${HIVE_JDBC_URL}" -e 'show databases;' > data/ops/hive_databases.txt 2>&1 || true
else
  echo "beeline not found" > data/ops/hive_databases.txt
fi

date '+%Y-%m-%d %H:%M:%S' > data/ops/refreshed_at.txt
