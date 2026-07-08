#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/ops

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

date '+%Y-%m-%d %H:%M:%S' > data/ops/refreshed_at.txt
