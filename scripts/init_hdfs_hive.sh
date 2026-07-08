#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

compose_file="docker/docker-compose.yml"
hive_compose_file="docker/docker-compose.hive.yml"
ops_dir="data/ops"
init_sql="${ops_dir}/hive_init.sql"

mkdir -p "${ops_dir}"

docker compose -f "${compose_file}" -f "${hive_compose_file}" up -d hdfs-namenode hdfs-datanode hive-server

echo "wait hdfs..."
for _ in $(seq 1 60); do
  if docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls / >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "wait hdfs safemode off..."
for _ in $(seq 1 60); do
  docker exec cdc-warehouse-hdfs-namenode hdfs dfsadmin -safemode leave >/dev/null 2>&1 || true
  if docker exec cdc-warehouse-hdfs-namenode hdfs dfsadmin -safemode get 2>/dev/null | grep -q 'Safe mode is OFF'; then
    break
  fi
  sleep 2
done

docker exec cdc-warehouse-hdfs-namenode hdfs dfs -mkdir -p \
  /warehouse/ods_binlog \
  /warehouse/ods \
  /warehouse/dim \
  /warehouse/dwd \
  /warehouse/dws \
  /warehouse/dwt \
  /warehouse/ads \
  /warehouse/hive

docker exec cdc-warehouse-hdfs-namenode hdfs dfs -chmod -R 777 /warehouse

{
  echo "create database if not exists ods_binlog;"
  echo "create database if not exists ods;"
  echo "create database if not exists dim;"
  echo "create database if not exists dwd;"
  echo "create database if not exists dws;"
  echo "create database if not exists dwt;"
  echo "create database if not exists ads;"
  echo ""
  find warehouse/sql -path '*/ddl/*.sql' -type f | sort | while read -r file; do
    echo "-- ${file}"
    sed 's/[[:space:]]*$//' "${file}"
    echo ""
  done
} > "${init_sql}"

echo "wait hive..."
for _ in $(seq 1 90); do
  if docker exec cdc-warehouse-hive-server beeline -u jdbc:hive2://localhost:10000 -e 'show databases;' >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

docker exec cdc-warehouse-hive-server beeline -u jdbc:hive2://localhost:10000 -f /workspace/"${init_sql}"
docker exec cdc-warehouse-hive-server beeline -u jdbc:hive2://localhost:10000 -e 'show databases;' > "${ops_dir}/hive_databases.txt" 2>&1 || true
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls -R /warehouse > "${ops_dir}/hdfs_warehouse_ls.txt" 2>&1 || true

echo "hdfs ui: http://localhost:9870"
echo "hive jdbc: jdbc:hive2://localhost:10000"
echo "init sql: ${init_sql}"
