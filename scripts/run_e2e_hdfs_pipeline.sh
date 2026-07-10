#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

biz_dt="${1:-${BIZ_DT:-$(python3 -c 'from datetime import date,timedelta; print((date.today()-timedelta(days=1)).isoformat())')}}"
lake_root="${LAKE_ROOT:-hdfs://localhost:8020/warehouse}"
compose_file="docker/docker-compose.yml"
hive_compose_file="docker/docker-compose.hive.yml"
test_id="${TEST_ID:-$(python3 -c 'import time; print(91000000 + int(time.time()) % 1000000)')}"
batch_no="E2E${biz_dt//-/}${test_id}"
ops_log="data/ops/e2e_hdfs_pipeline.log"

mkdir -p data/ops

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

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${ops_log}"
}

run_hive_file() {
  local file="$1"
  docker exec cdc-warehouse-hive-server beeline \
    -u jdbc:hive2://localhost:10000 \
    --hivevar "biz_dt=${biz_dt}" \
    -f "/workspace/${file}" >> "${ops_log}" 2>&1
}

run_hive_sql() {
  local sql="$1"
  docker exec cdc-warehouse-hive-server beeline \
    -u jdbc:hive2://localhost:10000 \
    -e "${sql}" >> "${ops_log}" 2>&1
}

wait_until() {
  local name="$1"
  local command="$2"
  local max_wait="${3:-90}"
  local waited=0
  until eval "${command}" >/dev/null 2>&1; do
    if [[ "${waited}" -ge "${max_wait}" ]]; then
      log "FAIL wait timeout: ${name}"
      return 1
    fi
    sleep 3
    waited=$((waited + 3))
  done
  log "OK ${name}"
}

log "E2E start biz_dt=${biz_dt} test_id=${test_id} lake_root=${lake_root}"

log "start docker stack"
docker compose -f "${compose_file}" -f "${hive_compose_file}" up -d \
  mysql zookeeper kafka maxwell hdfs-namenode hdfs-datanode hive-server spark-streaming admin ops-refresh >> "${ops_log}" 2>&1

wait_until "mysql healthy" "docker inspect -f '{{.State.Health.Status}}' cdc-warehouse-mysql | grep -q healthy" 120
wait_until "kafka healthy" "docker inspect -f '{{.State.Health.Status}}' cdc-warehouse-kafka | grep -q healthy" 120
wait_until "hdfs ready" "docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls /warehouse" 120
docker exec cdc-warehouse-hdfs-namenode hdfs dfsadmin -safemode leave >> "${ops_log}" 2>&1 || true
wait_until "hdfs safemode off" "docker exec cdc-warehouse-hdfs-namenode hdfs dfsadmin -safemode get | grep -q 'Safe mode is OFF'" 120
wait_until "hive ready" "docker exec cdc-warehouse-hive-server beeline -u jdbc:hive2://localhost:10000 -e 'show databases;'" 180

log "init hdfs/hive ddl"
./scripts/init_hdfs_hive.sh >> "${ops_log}" 2>&1
docker compose -f "${compose_file}" -f "${hive_compose_file}" restart spark-streaming >> "${ops_log}" 2>&1
wait_until "spark-streaming running" "docker inspect -f '{{.State.Running}}' cdc-warehouse-spark-streaming | grep -q true" 60

log "insert mysql test row"
docker exec cdc-warehouse-mysql mysql -uroot -proot -e "
insert into basiccomment.avatar_commentbatchsource
  (id,batchnumber,batchtype,ctime,utime,ver,source_channel)
values
  (${test_id},'${batch_no}','priority','${biz_dt} 11:00:00','${biz_dt} 11:00:00',1,'e2e')
on duplicate key update
  batchnumber=values(batchnumber),
  batchtype=values(batchtype),
  utime=values(utime),
  ver=ver+1,
  source_channel=values(source_channel);
" >> "${ops_log}" 2>&1

log "run one kafka to hdfs micro-batch"
docker exec cdc-warehouse-spark-streaming python3 scripts/spark_streaming_kafka_to_hdfs_once.py \
  --bootstrap-server kafka:9092 \
  --lake-root hdfs://hdfs-namenode:8020/warehouse >> "${ops_log}" 2>&1

binlog_path="/warehouse/ods_binlog/db=basiccomment/table=avatar_commentbatchsource/dt=${biz_dt}/part-00000.jsonl"
wait_until "spark-streaming hdfs binlog ${binlog_path}" \
  "docker exec cdc-warehouse-hdfs-namenode sh -c \"hdfs dfs -test -s '${binlog_path}' && hdfs dfs -cat '${binlog_path}' | grep -q '${test_id}'\"" \
  120

log "run pyspark ods merge"
pyspark_python="$(find_pyspark_python)" || {
  log "FAIL pyspark python not found"
  exit 1
}
PYSPARK_PYTHON="${pyspark_python}" PYSPARK_DRIVER_PYTHON="${pyspark_python}" "${pyspark_python}" scripts/spark_sql_ods_merge_daily.py \
  --lake-root "${lake_root}" \
  --biz-dt "${biz_dt}" \
  --engine pyspark >> "${ops_log}" 2>&1

ods_dir="/warehouse/ods/db=basiccomment/table=avatar_commentbatchsource/dt=${biz_dt}"
wait_until "ods hdfs snapshot ${ods_dir}" \
  "docker exec cdc-warehouse-hdfs-namenode sh -c \"hdfs dfs -ls '${ods_dir}' && hdfs dfs -cat '${ods_dir}'/part-*.csv | grep -q '${test_id}'\"" \
  60

log "repair hive partitions"
run_hive_sql "msck repair table ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di; msck repair table ods.ods_basiccomment_avatar_commentbatchsource_dic;"

log "run hive dim/dwd/dws/dwt/ads"
run_hive_file "warehouse/sql/dim/jobs/dim_comment_batch_type.sql"
run_hive_file "warehouse/sql/dwd/jobs/dwd_comment_batch_detail_di.sql"
run_hive_file "warehouse/sql/dws/jobs/dws_comment_batch_1d.sql"
run_hive_file "warehouse/sql/dwt/jobs/dwt_comment_batch_topic_td.sql"
run_hive_file "warehouse/sql/ads/jobs/ads_comment_dashboard_1d.sql"

log "query ods result"
docker exec cdc-warehouse-hive-server beeline \
  -u jdbc:hive2://localhost:10000 \
  -e "select id,batchnumber,batchtype,source_channel,dt from ods.ods_basiccomment_avatar_commentbatchsource_dic where dt='${biz_dt}' and id=${test_id};" \
  | tee data/ops/e2e_ods_result.txt

log "query ads result"
docker exec cdc-warehouse-hive-server beeline \
  -u jdbc:hive2://localhost:10000 \
  -e "select * from ads.ads_comment_dashboard_1d where dt='${biz_dt}' order by metric_name;" \
  | tee data/ops/e2e_ads_result.txt

log "E2E done"
echo "log: ${ops_log}"
echo "ods result: data/ops/e2e_ods_result.txt"
echo "ads result: data/ops/e2e_ads_result.txt"
