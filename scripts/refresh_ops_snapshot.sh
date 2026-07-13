#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
mkdir -p data/ops data/ops/hdfs_samples

docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' > data/ops/container_status.txt
docker logs --tail 120 cdc-warehouse-maxwell > data/ops/maxwell.log 2>&1 || true
docker logs --tail 80 cdc-warehouse-kafka > data/ops/kafka.log 2>&1 || true
docker logs --tail 80 cdc-warehouse-spark-streaming > data/ops/spark_streaming.log 2>&1 || true
docker logs --tail 80 cdc-warehouse-admin > data/ops/admin.log 2>&1 || true
docker logs --tail 80 cdc-warehouse-hdfs-namenode > data/ops/hdfs_namenode.log 2>&1 || true
docker logs --tail 80 cdc-warehouse-hive-server > data/ops/hive_server.log 2>&1 || true
docker exec cdc-warehouse-kafka kafka-topics --bootstrap-server kafka:9092 --list > data/ops/kafka_topics.txt 2>&1 || true
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls -R /warehouse > data/ops/hdfs_warehouse_ls.txt 2>&1 || true
docker exec cdc-warehouse-hive-server beeline -u jdbc:hive2://localhost:10000 -e 'show databases;' > data/ops/hive_databases.txt 2>&1 || true

if [ -s data/ops/hdfs_warehouse_ls.txt ]; then
  awk '$1 ~ /^d/ {print $NF}' data/ops/hdfs_warehouse_ls.txt \
    | grep '/dt=' \
    | sort -u \
    | while IFS= read -r directory; do
      safe_name=$(printf '%s' "$directory" | sed 's#[^A-Za-z0-9._=-]#_#g')
      if docker exec cdc-warehouse-hdfs-namenode sh -lc "hdfs dfs -ls '$directory'/*.parquet >/dev/null 2>&1"; then
        printf 'parquet partition: %s\nquery it through Hive/Spark/Impala\n' "$directory" \
          > "data/ops/hdfs_samples/${safe_name}.head"
        docker exec cdc-warehouse-hdfs-namenode sh -lc "hdfs dfs -ls '$directory'/*.parquet 2>/dev/null | wc -l" \
          > "data/ops/hdfs_samples/${safe_name}.count" 2>&1 || true
      else
        docker exec cdc-warehouse-hdfs-namenode sh -lc "hdfs dfs -cat '$directory'/* 2>/dev/null | grep -v 'NativeCodeLoader' | head -20" \
          > "data/ops/hdfs_samples/${safe_name}.head" 2>&1 || true
        docker exec cdc-warehouse-hdfs-namenode sh -lc "hdfs dfs -cat '$directory'/* 2>/dev/null | grep -v 'NativeCodeLoader' | wc -l" \
          > "data/ops/hdfs_samples/${safe_name}.count" 2>&1 || true
      fi
    done
fi

date '+%Y-%m-%d %H:%M:%S' > data/ops/refreshed_at.txt
