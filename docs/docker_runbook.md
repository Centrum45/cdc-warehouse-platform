# Docker Runbook

Local demo cluster:

```text
MySQL 8.0
Kafka + Zookeeper
Maxwell
SpringBoot Admin
```

Optional warehouse infra:

```text
HDFS NameNode + DataNode
Hive Metastore + HiveServer2
```

## Start

```bash
cd cdc-warehouse-platform
./scripts/docker_up.sh
```

Start and initialize HDFS/Hive:

```bash
./scripts/download_hadoop_hive.sh
./scripts/init_hdfs_hive.sh
```

Run full CDC warehouse E2E:

```bash
./scripts/run_e2e_hdfs_pipeline.sh
```

Expected checks:

```text
spark-streaming hdfs binlog ... OK
ods hdfs snapshot ... OK
Hive ODS query returns inserted e2e row
Hive ADS query returns comment_batch_total metrics
```

Open:

```text
http://localhost:8080
```

Kafka host from local machine:

```text
localhost:19092
```

MySQL:

```text
127.0.0.1:13306
root/root
```

HDFS:

```text
NameNode UI: http://localhost:9870
fs.defaultFS: hdfs://localhost:8020
```

Hive:

```text
HiveServer2 JDBC: jdbc:hive2://localhost:10000
Metastore thrift: thrift://localhost:9083
```

## Generate A Binlog Event

```bash
./scripts/docker_seed_change.sh
```

This updates `basiccomment.avatar_commentbatchsource`, Maxwell reads MySQL
binlog, and Kafka receives the CDC JSON.

Export Kafka topic to local JSONL:

```bash
./scripts/kafka_to_jsonl.sh cdc.incremental.binlog data/kafka/cdc.incremental.binlog.jsonl 100
```

Then run local warehouse pipeline:

```bash
./scripts/run_local_pipeline.sh
```

## Maxwell Bootstrap

Inside Maxwell container:

```bash
docker exec cdc-warehouse-maxwell bin/maxwell-bootstrap \
  --database basiccomment \
  --table avatar_commentbatchsource \
  --host mysql \
  --user maxwell \
  --password maxwell
```

## Stop

```bash
./scripts/docker_down.sh
```

## Notes

Local mode still writes file-lake output for fast reruns:

```text
data/lake
```

Docker E2E writes real HDFS paths:

```text
/warehouse/ods_binlog
/warehouse/ods
/warehouse/dim
/warehouse/dwd
/warehouse/dws
/warehouse/dwt
/warehouse/ads
```

Hive DDL is loaded by `scripts/init_hdfs_hive.sh`. Runtime state under
`data/hdfs`, `data/hive`, and `data/ops` is ignored by Git.

Browse HDFS-backed layers through the platform API:

```bash
LAKE_ROOT=hdfs://localhost:8020/warehouse BIZ_DT=2026-07-07 python3 platform_api/main.py
curl 'http://127.0.0.1:8000/api/layers?dt=2026-07-07'
```
