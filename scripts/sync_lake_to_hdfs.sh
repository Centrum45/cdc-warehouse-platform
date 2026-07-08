#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

lake_root="${1:-data/lake}"
hdfs_root="${2:-/warehouse/local_lake}"

if [ ! -d "${lake_root}" ]; then
  echo "local lake not found: ${lake_root}" >&2
  exit 1
fi

docker exec cdc-warehouse-hdfs-namenode hdfs dfs -mkdir -p "${hdfs_root}"
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -rm -r -f "${hdfs_root}" >/dev/null 2>&1 || true
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -mkdir -p "${hdfs_root}"

docker cp "${lake_root}" cdc-warehouse-hdfs-namenode:/tmp/cdc-warehouse-lake
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -put -f /tmp/cdc-warehouse-lake/* "${hdfs_root}/"
docker exec cdc-warehouse-hdfs-namenode rm -rf /tmp/cdc-warehouse-lake
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls -R "${hdfs_root}" | head -80
