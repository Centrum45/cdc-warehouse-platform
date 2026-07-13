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
export SPARK_STREAMING_CHECKPOINT="${SPARK_STREAMING_CHECKPOINT:-hdfs://hdfs-namenode:8020/warehouse/checkpoints/offline_sink}"
export SPARK_BAD_RECORDS_PATH="${SPARK_BAD_RECORDS_PATH:-}"
mysql_container="${MYSQL_CONTAINER:-cdc-warehouse-mysql}"
kafka_container="${KAFKA_CONTAINER:-cdc-warehouse-kafka}"
hdfs_container="${HDFS_CONTAINER:-cdc-warehouse-hdfs-namenode}"
hive_container="${HIVE_CONTAINER:-cdc-warehouse-hive-server}"
spark_container="${SPARK_STREAMING_CONTAINER:-cdc-warehouse-spark-streaming}"
admin_container="${ADMIN_CONTAINER:-cdc-warehouse-admin}"
hive_jdbc_url="${HIVE_JDBC_URL:-jdbc:hive2://localhost:10000}"

mkdir -p data/ops

find_pyspark_python() {
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

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${ops_log}"
}

run_hive_sql() {
  local sql="$1"
  docker exec "${hive_container}" beeline \
    -u "${hive_jdbc_url}" \
    -e "${sql}" >> "${ops_log}" 2>&1
}

wait_until() {
  local name="$1"
  local command="$2"
  local max_wait="${3:-90}"
  local waited=0
  until run_with_timeout 20 "${command}" >/dev/null 2>&1; do
    if [[ "${waited}" -ge "${max_wait}" ]]; then
      log "FAIL wait timeout: ${name}"
      return 1
    fi
    sleep 3
    waited=$((waited + 3))
  done
  log "OK ${name}"
}

run_with_timeout() {
  local seconds="$1"
  local command="$2"
  bash -c "${command}" &
  local pid="$!"
  local elapsed=0
  while kill -0 "${pid}" >/dev/null 2>&1; do
    if [[ "${elapsed}" -ge "${seconds}" ]]; then
      kill "${pid}" >/dev/null 2>&1 || true
      wait "${pid}" >/dev/null 2>&1 || true
      return 124
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  wait "${pid}"
}

log "E2E start biz_dt=${biz_dt} test_id=${test_id} lake_root=${lake_root}"

log "start docker stack"
docker compose -f "${compose_file}" -f "${hive_compose_file}" up -d \
  mysql zookeeper kafka maxwell hdfs-namenode hdfs-datanode hive-server spark-streaming admin ops-refresh >> "${ops_log}" 2>&1

wait_until "mysql healthy" "docker inspect -f '{{.State.Health.Status}}' '${mysql_container}' | grep -q healthy" 120
wait_until "kafka healthy" "docker inspect -f '{{.State.Health.Status}}' '${kafka_container}' | grep -q healthy" 120
wait_until "hdfs ready" "docker exec '${hdfs_container}' hdfs dfs -ls /warehouse" 120
docker exec "${hdfs_container}" hdfs dfsadmin -safemode leave >> "${ops_log}" 2>&1 || true
wait_until "hdfs safemode off" "docker exec '${hdfs_container}' hdfs dfsadmin -safemode get | grep -q 'Safe mode is OFF'" 120
wait_until "hive ready" "docker exec '${hive_container}' beeline -u '${hive_jdbc_url}' -e 'show databases;'" 180

log "init hdfs/hive ddl"
./scripts/init_hdfs_hive.sh >> "${ops_log}" 2>&1
docker exec "${hdfs_container}" hdfs dfs -rm -r -f "${SPARK_STREAMING_CHECKPOINT}" /warehouse/ods_binlog/_spark_metadata >> "${ops_log}" 2>&1 || true
docker compose -f "${compose_file}" -f "${hive_compose_file}" up -d --force-recreate spark-streaming >> "${ops_log}" 2>&1
wait_until "spark-streaming running" "docker inspect -f '{{.State.Running}}' '${spark_container}' | grep -q true" 60
wait_until "spark-streaming checkpoint initialized" "docker exec '${hdfs_container}' hdfs dfs -test -e '${SPARK_STREAMING_CHECKPOINT}/offsets/0'" 120

log "insert mysql test row"
docker exec "${mysql_container}" mysql -uroot -proot -e "
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

wait_until "ods_binlog hive row id=${test_id}" \
  "docker exec '${hive_container}' beeline -u '${hive_jdbc_url}' --silent=true --showHeader=false --outputformat=tsv2 -e \"msck repair table ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di; select count(1) from ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di where dt='${biz_dt}' and get_json_object(data_json,'$.id')='${test_id}';\" | awk '\$1+0>0{found=1} END{exit !found}'" \
  180

log "run pyspark ods merge"
pyspark_python="$(find_pyspark_python)" || {
  log "FAIL pyspark python not found"
  exit 1
}
LAKE_ROOT="${lake_root}" SPARK_DFS_CLIENT_USE_DATANODE_HOSTNAME=true PYSPARK_PYTHON="${pyspark_python}" PYSPARK_DRIVER_PYTHON="${pyspark_python}" \
  bash deploy/run_job.sh daily-merge "${biz_dt}" >> "${ops_log}" 2>&1

ods_dir="/warehouse/ods/db=basiccomment/table=avatar_commentbatchsource/dt=${biz_dt}"
wait_until "ods hdfs snapshot ${ods_dir}" \
  "docker exec '${hdfs_container}' sh -c \"hdfs dfs -ls '${ods_dir}'/part-*.parquet\"" \
  60

log "repair hive partitions"
run_hive_sql "msck repair table ods_binlog.ods_binlog_basiccomment_avatar_commentbatchsource_di; msck repair table ods.ods_basiccomment_avatar_commentbatchsource_dic;"

wait_until "ods hive row id=${test_id}" \
  "docker exec '${hive_container}' beeline -u '${hive_jdbc_url}' --silent=true --showHeader=false --outputformat=tsv2 -e \"select count(1) from ods.ods_basiccomment_avatar_commentbatchsource_dic where dt='${biz_dt}' and id=${test_id};\" | awk '\$1+0>0{found=1} END{exit !found}'" \
  90

log "run spark sql dim/dwd/dws/dwt/ads"
LAKE_ROOT="${lake_root}" SPARK_DFS_CLIENT_USE_DATANODE_HOSTNAME=true PYSPARK_PYTHON="${pyspark_python}" PYSPARK_DRIVER_PYTHON="${pyspark_python}" \
  bash deploy/run_job.sh layers "${biz_dt}" >> "${ops_log}" 2>&1

log "repair hive layer partitions"
run_hive_sql "
msck repair table dim.dim_comment_batch_type;
msck repair table dim.dim_user_info;
msck repair table dwd.dwd_comment_batch_detail_di;
msck repair table dwd.dwd_trade_order_detail_di;
msck repair table dws.dws_comment_batch_1d;
msck repair table dws.dws_trade_user_1d;
msck repair table dwt.dwt_comment_batch_topic_td;
msck repair table dwt.dwt_trade_user_td;
msck repair table ads.ads_comment_dashboard_1d;
msck repair table ads.ads_trade_dashboard_1d;
"

log "query ods result"
docker exec "${hive_container}" beeline \
  -u "${hive_jdbc_url}" \
  -e "select id,batchnumber,batchtype,source_channel,dt from ods.ods_basiccomment_avatar_commentbatchsource_dic where dt='${biz_dt}' and id=${test_id};" \
  | tee data/ops/e2e_ods_result.txt

log "query ads result"
docker exec "${hive_container}" beeline \
  -u "${hive_jdbc_url}" \
  -e "select * from ads.ads_comment_dashboard_1d where dt='${biz_dt}' order by metric_name;" \
  | tee data/ops/e2e_ads_result.txt

log "E2E done"
echo "log: ${ops_log}"
echo "ods result: data/ops/e2e_ods_result.txt"
echo "ads result: data/ops/e2e_ads_result.txt"
