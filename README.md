# CDC Warehouse Platform

Binlog-driven warehouse demo based on:

```text
MySQL -> Maxwell -> Kafka -> ods_binlog -> ODS snapshot -> DIM/DWD/DWS/DWT/ADS
                         -> Kudu/Impala realtime path
```

This repo is a runnable local reconstruction of the architecture. Heavy systems
are represented with compatible local interfaces:

- HDFS: local file lake `data/lake` or Docker HDFS `hdfs://localhost:8020/warehouse`
- Kafka: JSONL event files or Docker Kafka
- Hive/Spark SQL: generated SQL, local merge job, and Docker Hive/PySpark E2E
- Kudu/Impala: DDL/query placeholders
- Platform: SpringBoot + Freemarker skeleton
- Scheduler: DolphinScheduler workflow definitions

## Quick Start

```bash
cd cdc-warehouse-platform
./scripts/run_local_pipeline.sh
```

Outputs:

```text
data/lake/ods_binlog/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-06/part-00000.jsonl
data/lake/ods/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-06/part-00000.csv
warehouse/sql/ods/merge/merge_ods_basiccomment_avatar_commentbatchsource_dic.sql
```

Run tests:

```bash
python3 -m unittest discover -s tests
```

Python SparkStreaming-style jobs:

```bash
python3 streaming/offline_sink/spark_streaming_to_hdfs.py
python3 streaming/realtime_sink/kafka_to_kudu.py
```

True PySpark dual-mode jobs:

```bash
python3 scripts/run_spark_jobs.py all

# if PySpark is installed, run local Spark jobs
spark-submit --master local[2] streaming/offline_sink/pyspark_kafka_to_hdfs.py local data/kafka/cdc.incremental.binlog.jsonl data/lake
spark-submit --master local[2] warehouse/jobs/pyspark_ods_merge.py metadata/tables/basiccomment.avatar_commentbatchsource.json data/lake 2026-07-06
spark-submit --master local[2] streaming/realtime_sink/pyspark_kafka_to_kudu.py data/kafka/cdc.incremental.binlog.jsonl data/kudu_pyspark

# production Kafka stream shape
spark-submit --master yarn streaming/offline_sink/pyspark_kafka_to_hdfs.py kafka kafka:9092 cdc.incremental.binlog hdfs:///warehouse /checkpoint/cdc/offline
```

Onboard MySQL table to Hive:

```bash
python3 scripts/onboard_table.py metadata/dba/basiccomment.avatar_commentbatchsource.json id ver ctime
```

Publish DolphinScheduler workflow in local audit mode:

```bash
python3 scripts/publish_dolphinscheduler.py
```

Run monitor suite:

```bash
python3 monitors/run_monitor_suite.py
```

Control-plane skeleton:

```text
platform/springboot-admin
  /                 metadata query
  /tasks            Spark task config
  /replay           Maxwell bootstrap/replay
  /monitors         delay/field/special/table/plaintext monitors
```

SpringBoot platform with MySQL:

```text
platform/springboot-admin/src/main/resources/schema.sql
platform/springboot-admin/src/main/resources/data.sql
platform/springboot-admin/src/main/resources/application.yml
docs/springboot_mysql.md
```

SpringBoot form actions:

```text
POST /onboarding   execute MySQL-to-Hive onboarding and persist table/task metadata
POST /tasks        save Spark task config
POST /replay       create replay command and persist replay record
```

Docker demo:

```bash
./scripts/docker_up.sh
./scripts/docker_seed_change.sh
./scripts/kafka_to_jsonl.sh
./scripts/docker_down.sh
```

Full Docker HDFS/Hive E2E:

```bash
./scripts/download_hadoop_hive.sh
./scripts/run_e2e_hdfs_pipeline.sh
```

This verifies:

```text
MySQL insert -> Maxwell -> Kafka -> SparkStreaming -> HDFS ods_binlog
-> PySpark ODS merge -> Hive ODS -> DIM/DWD/DWS/DWT/ADS
```

Platform API can browse HDFS by setting:

```bash
LAKE_ROOT=hdfs://localhost:8020/warehouse BIZ_DT=2026-07-07 python3 platform_api/main.py
```

See:

```text
docs/docker_runbook.md
```

Trade/user demo pipeline:

```bash
./scripts/run_trade_user_pipeline.sh
```

## Core Merge Rule

```text
new binlog
union all old ODS partitions touched by binlog
row_number over(partition by primary key order by ver desc, binlog_type desc)
keep rn = 1
drop binlog_type = delete
```

`binlog_type` order:

```text
insert/bootstrap-insert = 1
update                  = 2
delete                  = 3
```

Delete wins when same primary key and same version exist.

## Project Capabilities

- Incremental ingest: Maxwell reads MySQL binlog, writes Kafka, SparkStreaming sinks daily partitions to HDFS.
- History ingest: Maxwell bootstrap creates full events for first MySQL-Hive mirror or replay.
- ODS merge: SparkSQL parses T-1 binlog, merges touched ODS partitions, filters delete, writes snapshot.
- Warehouse modeling: ODS -> DIM/DWD/DWS/DWT/ADS. DWD handles modeling, cleaning, degenerate dimensions.
- Scheduling: DolphinScheduler runs layer jobs and merge dependencies.
- Delay gate: SparkStreaming writes table sync progress. Merge starts only when delay threshold passes.
- Field monitor: compares platform metadata with DBA metadata and emits ODS alter SQL.
- Special value monitor: checks increasing fields and not-null fields by SQL.
- Table update monitor: checks max update time to catch business table switch or migration.
- Plaintext guard: detects sensitive values during binlog ingestion, hashes or defaults them, then notifies DBA.
- Management platform: SpringBoot + Freemarker pages for metadata, MySQL-to-Hive onboarding, Spark job config.
- Realtime warehouse: SparkStreaming parses Kafka binlog by schema, upserts Kudu, queries with Impala.
