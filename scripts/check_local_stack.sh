#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

compose_file="${COMPOSE_FILE:-docker/docker-compose.yml}"
hive_compose_file="${HIVE_COMPOSE_FILE:-docker/docker-compose.hive.yml}"
biz_dt="${BIZ_DT:-$(python3 -c 'from datetime import date,timedelta; print((date.today()-timedelta(days=1)).isoformat())')}"
admin_url="${ADMIN_URL:-http://localhost:8080/api/dashboard}"

ok=0
fail=0
warn=0

pass() {
  printf '[OK]   %s\n' "$1"
  ok=$((ok + 1))
}

bad() {
  printf '[FAIL] %s\n' "$1"
  fail=$((fail + 1))
}

note() {
  printf '[WARN] %s\n' "$1"
  warn=$((warn + 1))
}

compose() {
  docker compose -f "${compose_file}" -f "${hive_compose_file}" "$@"
}

container_running() {
  local name="$1"
  if docker inspect -f '{{.State.Running}}' "${name}" 2>/dev/null | grep -q true; then
    pass "container ${name} running"
  else
    bad "container ${name} not running"
  fi
}

container_health() {
  local name="$1"
  local status
  status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${name}" 2>/dev/null || true)"
  case "${status}" in
    healthy) pass "container ${name} healthy" ;;
    none) note "container ${name} has no healthcheck" ;;
    *) bad "container ${name} health=${status}" ;;
  esac
}

try_exec() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    pass "${label}"
  else
    bad "${label}"
  fi
}

container_running cdc-warehouse-mysql
container_running cdc-warehouse-kafka
container_running cdc-warehouse-maxwell
container_running cdc-warehouse-hdfs-namenode
container_running cdc-warehouse-hdfs-datanode
container_running cdc-warehouse-hive-server
container_running cdc-warehouse-spark-streaming
container_running cdc-warehouse-admin

container_health cdc-warehouse-mysql
container_health cdc-warehouse-kafka

try_exec "MySQL basiccomment table query" \
  docker exec cdc-warehouse-mysql mysql -uroot -proot -e "select count(*) from basiccomment.avatar_commentbatchsource;"

try_exec "Kafka topic list" \
  docker exec cdc-warehouse-kafka kafka-topics --bootstrap-server kafka:9092 --list

if docker exec cdc-warehouse-kafka kafka-topics --bootstrap-server kafka:9092 --list 2>/dev/null | grep -q '^cdc.incremental.binlog$'; then
  pass "Kafka topic cdc.incremental.binlog exists"
else
  note "Kafka topic cdc.incremental.binlog not found yet"
fi

try_exec "HDFS /warehouse ls" \
  docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls /warehouse

try_exec "Hive show databases" \
  docker exec cdc-warehouse-hive-server beeline -u jdbc:hive2://localhost:10000 -e 'show databases;'

if curl -fsS "${admin_url}" >/dev/null 2>&1; then
  pass "SpringBoot dashboard ${admin_url}"
else
  bad "SpringBoot dashboard ${admin_url}"
fi

if docker exec cdc-warehouse-hdfs-namenode hdfs dfs -test -d "/warehouse/ods_binlog/db=basiccomment/table=avatar_commentbatchsource/dt=${biz_dt}" >/dev/null 2>&1; then
  pass "ODS binlog partition ${biz_dt}"
else
  note "ODS binlog partition ${biz_dt} missing"
fi

if docker exec cdc-warehouse-hdfs-namenode hdfs dfs -test -d "/warehouse/ods/db=basiccomment/table=avatar_commentbatchsource/dt=${biz_dt}" >/dev/null 2>&1; then
  pass "ODS snapshot partition ${biz_dt}"
else
  note "ODS snapshot partition ${biz_dt} missing"
fi

if docker exec cdc-warehouse-hdfs-namenode hdfs dfs -test -d "/warehouse/ads/ads_comment_dashboard_1d/dt=${biz_dt}" >/dev/null 2>&1; then
  pass "ADS partition ${biz_dt}"
else
  note "ADS partition ${biz_dt} missing"
fi

mkdir -p data/ops
compose ps > data/ops/local_stack_ps.txt 2>&1 || true
docker logs --tail 120 cdc-warehouse-spark-streaming > data/ops/spark_streaming.log 2>&1 || true
docker logs --tail 120 cdc-warehouse-admin > data/ops/admin.log 2>&1 || true
docker logs --tail 120 cdc-warehouse-maxwell > data/ops/maxwell.log 2>&1 || true

printf '\nsummary: ok=%d warn=%d fail=%d\n' "${ok}" "${warn}" "${fail}"
printf 'logs: data/ops/local_stack_ps.txt data/ops/spark_streaming.log data/ops/admin.log data/ops/maxwell.log\n'

[[ "${fail}" -eq 0 ]]
