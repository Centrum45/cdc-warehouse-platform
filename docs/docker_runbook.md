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

Current SparkStreaming and daily PySpark merge still write local HDFS simulation
for easy local rerun:

```text
data/lake
```

Docker HDFS is installed for real HDFS/Hive practice. Sync local lake into HDFS
when needed:

```bash
./scripts/sync_lake_to_hdfs.sh
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls -R /warehouse/local_lake
```

Hive DDL is loaded by `scripts/init_hdfs_hive.sh`. The local CSV/JSONL lake is
kept as default job output because host PySpark can run without Hadoop client
network/config friction.
