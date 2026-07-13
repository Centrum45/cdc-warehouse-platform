#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  cat <<'EOF'
usage:
  scripts/table_ops.sh [--dry-run] backfill <db> <table> <start_dt> <end_dt>
  scripts/table_ops.sh [--dry-run] check-lineage <db> <table> <biz_dt> <ods_table>
  scripts/table_ops.sh [--dry-run] consistency <db> <table> <biz_dt> <ods_table> <partition_column>
  scripts/table_ops.sh [--dry-run] onboarding-verify <db> <table> <biz_dt> <ods_table>

env:
  LAKE_ROOT          default hdfs://localhost:8020/warehouse
  HIVE_JDBC_URL      default jdbc:hive2://localhost:10000
  MYSQL_CONTAINER   default cdc-warehouse-mysql
  HDFS_CONTAINER    default cdc-warehouse-hdfs-namenode
  HIVE_CONTAINER    default cdc-warehouse-hive-server
  KAFKA_CONTAINER   default cdc-warehouse-kafka
EOF
}

dry_run="false"
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run="true"
  shift
fi

cmd="${1:-}"
if [[ -z "${cmd}" || "${cmd}" == "-h" || "${cmd}" == "--help" ]]; then
  usage
  exit 0
fi
shift

lake_root="${LAKE_ROOT:-hdfs://localhost:8020/warehouse}"
hive_jdbc_url="${HIVE_JDBC_URL:-jdbc:hive2://localhost:10000}"
mysql_container="${MYSQL_CONTAINER:-cdc-warehouse-mysql}"
hdfs_container="${HDFS_CONTAINER:-cdc-warehouse-hdfs-namenode}"
hive_container="${HIVE_CONTAINER:-cdc-warehouse-hive-server}"
kafka_container="${KAFKA_CONTAINER:-cdc-warehouse-kafka}"

metadata_path() {
  local db="$1"
  local table="$2"
  echo "metadata/tables/${db}.${table}.json"
}

find_python_with_module() {
  local module="$1"
  for candidate in "${PYTHON_BIN:-}" "${PYSPARK_PYTHON:-}" .venv/bin/python python3.11 python3.10 python3.9 python3.8 python3.7 python3 python; do
    if [[ -z "${candidate}" ]]; then
      continue
    fi
    if command -v "${candidate}" >/dev/null 2>&1 && "${candidate}" -c "import ${module}" >/dev/null 2>&1; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

run_or_print() {
  if [[ "${dry_run}" == "true" ]]; then
    printf '[DRY RUN]'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

date_range() {
  local start_dt="$1"
  local end_dt="$2"
  python3 - "$start_dt" "$end_dt" <<'PY'
from datetime import date, timedelta
import sys

start = date.fromisoformat(sys.argv[1])
end = date.fromisoformat(sys.argv[2])
while start <= end:
    print(start.isoformat())
    start += timedelta(days=1)
PY
}

bootstrap_table() {
  local db="$1"
  local table="$2"
  local python_bin
  python_bin="$(find_python_with_module pyarrow)" || {
    echo "python with pyarrow not found" >&2
    return 1
  }
  run_or_print "${python_bin}" scripts/bootstrap_mysql_table.py "$(metadata_path "$db" "$table")" \
    --lake-root "${lake_root}" \
    --replace-binlog
}

run_merge_dt() {
  local dt="$1"
  if [[ "${dry_run}" == "true" ]]; then
    echo "[DRY RUN] BIZ_DT=${dt} bash deploy/run_job.sh daily-merge ${dt}"
    return 0
  fi
  BIZ_DT="${dt}" bash deploy/run_job.sh daily-merge "${dt}"
}

hive_scalar() {
  local sql="$1"
  docker exec "${hive_container}" beeline \
    -u "${hive_jdbc_url}" \
    --silent=true \
    --showHeader=false \
    -e "${sql}" 2>/dev/null \
    | awk -F'|' '
      NF >= 3 {
        value = $2
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
        if (value ~ /^[0-9]+$/) {
          print value
          exit
        }
      }
    '
}

check_lineage() {
  local db="$1"
  local table="$2"
  local dt="$3"
  local ods_table="$4"

  echo "== MySQL row count =="
  run_or_print docker exec "${mysql_container}" mysql -uroot -proot -N -e "select count(*) from ${db}.${table};" || true

  echo "== Kafka recent table events =="
  if [[ "${dry_run}" == "true" ]]; then
    echo "[DRY RUN] docker exec ${kafka_container} kafka-console-consumer --bootstrap-server kafka:9092 --topic cdc.incremental.binlog ..."
  else
    docker exec "${kafka_container}" kafka-console-consumer \
    --bootstrap-server kafka:9092 \
    --topic cdc.incremental.binlog \
    --from-beginning \
    --max-messages 200 \
    --timeout-ms 8000 2>/dev/null \
    | grep -c "\"database\":\"${db}\".*\"table\":\"${table}\"" || true
  fi

  echo "== HDFS ods_binlog partition =="
  run_or_print docker exec "${hdfs_container}" hdfs dfs -ls "/warehouse/ods_binlog/db=${db}/table=${table}/dt=${dt}" || true

  echo "== HDFS ods partition =="
  run_or_print docker exec "${hdfs_container}" hdfs dfs -ls "/warehouse/ods/db=${db}/table=${table}/dt=${dt}" || true

  echo "== Hive ODS count =="
  run_or_print docker exec "${hive_container}" beeline \
    -u "${hive_jdbc_url}" \
    --silent=true \
    --showHeader=false \
    -e "select count(*) from ods.${ods_table} where dt='${dt}';" || true
}

consistency() {
  local db="$1"
  local table="$2"
  local dt="$3"
  local ods_table="$4"
  local partition_column="$5"
  local next_dt
  next_dt="$(python3 - "$dt" <<'PY'
from datetime import date, timedelta
import sys
print((date.fromisoformat(sys.argv[1]) + timedelta(days=1)).isoformat())
PY
)"

  local mysql_count
  local ods_count
  if [[ "${dry_run}" == "true" ]]; then
    echo "[DRY RUN] compare MySQL ${db}.${table} and Hive ods.${ods_table} for dt=${dt}"
    return 0
  fi
  mysql_count="$(docker exec "${mysql_container}" mysql -uroot -proot -N -e "select count(*) from ${db}.${table} where ${partition_column} >= '${dt} 00:00:00' and ${partition_column} < '${next_dt} 00:00:00';" | tail -n 1 || echo 0)"
  ods_count="$(hive_scalar "select count(*) from ods.${ods_table} where dt='${dt}';")"
  ods_count="${ods_count:-0}"

  echo "mysql_count=${mysql_count}"
  echo "ods_count=${ods_count}"
  if [[ "${mysql_count}" == "${ods_count}" ]]; then
    echo "CONSISTENT"
    return 0
  fi
  echo "INCONSISTENT"
  return 1
}

case "${cmd}" in
  backfill)
    db="${1:?db required}"
    table="${2:?table required}"
    start_dt="${3:?start_dt required}"
    end_dt="${4:?end_dt required}"
    bootstrap_table "${db}" "${table}"
    while IFS= read -r dt; do
      run_merge_dt "${dt}"
    done < <(date_range "${start_dt}" "${end_dt}")
    ;;
  check-lineage)
    check_lineage "${1:?db required}" "${2:?table required}" "${3:?biz_dt required}" "${4:?ods_table required}"
    ;;
  consistency)
    consistency "${1:?db required}" "${2:?table required}" "${3:?biz_dt required}" "${4:?ods_table required}" "${5:?partition_column required}"
    ;;
  onboarding-verify)
    db="${1:?db required}"
    table="${2:?table required}"
    dt="${3:?biz_dt required}"
    ods_table="${4:?ods_table required}"
    bootstrap_table "${db}" "${table}"
    run_merge_dt "${dt}"
    run_or_print docker exec "${hdfs_container}" hdfs dfs -ls "/warehouse/ods_binlog/db=${db}/table=${table}/dt=${dt}"
    run_or_print docker exec "${hdfs_container}" hdfs dfs -ls "/warehouse/ods/db=${db}/table=${table}/dt=${dt}"
    run_or_print docker exec "${hive_container}" beeline -u "${hive_jdbc_url}" --silent=true --showHeader=false -e "select count(*) from ods.${ods_table} where dt='${dt}';"
    ;;
  *)
    echo "unknown command: ${cmd}" >&2
    usage >&2
    exit 2
    ;;
esac
