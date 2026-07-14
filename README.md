# CDC Warehouse Platform

Binlog-driven warehouse platform based on:

```text
MySQL -> Maxwell -> Kafka -> ods_binlog -> ODS snapshot -> DIM/DWD/DWS/DWT/ADS
                         -> Kudu/Impala realtime path
```

This repo supports two deployment modes:

- Local debug: Docker Compose starts MySQL, Maxwell, Kafka, HDFS, Hive, DolphinScheduler, SparkStreaming, and SpringBoot Admin.
- Server production: deploy SpringBoot and long-running jobs directly to Linux servers with systemd, while connecting to real MySQL/Kafka/HDFS/Hive/DolphinScheduler.

Runtime interfaces:

- HDFS: Docker or production HDFS, default local endpoint `hdfs://localhost:8020/warehouse`
- Kafka: Docker or production Kafka
- Hive/Spark SQL: generated SQL, Docker Hive/PySpark E2E, server Spark submit scripts
- Kudu/Impala: Docker single-node realtime cluster, Impala views, Kudu upsert smoke
- Platform: SpringBoot + Freemarker admin console
- Scheduler: DolphinScheduler workflow definitions
- Debug fallbacks: local JSONL input plus Parquet lake data under `data/lake`; realtime local Kudu fallback still uses CSV

## Local Quick Start

Python helper scripts expect Python 3.8-3.11. Use `scripts/setup_python.sh` to create `.venv` instead of relying on the system `python3`.

```bash
cd cdc-warehouse-platform
cp .env.example .env
./scripts/setup_python.sh
./scripts/check_dependencies.sh --mode local
./scripts/dev_up.sh
./scripts/dev_check.sh
```

Outputs:

```text
hdfs://localhost:8020/warehouse/ods_binlog/db=basiccomment/table=avatar_commentbatchsource/dt=<biz_dt>/
hdfs://localhost:8020/warehouse/ods/db=basiccomment/table=avatar_commentbatchsource/dt=<biz_dt>/
warehouse/sql/ods/merge/merge_ods_basiccomment_avatar_commentbatchsource_dic.sql
```

Run tests:

```bash
./scripts/test.sh
```

Production preflight:

```bash
cp deploy/prod/jobs.env.example deploy/prod/jobs.env
cp deploy/prod/admin.env.example deploy/prod/admin.env
./scripts/prod_preflight.sh deploy/prod/jobs.env
```

One-command end-to-end verification after deployment:

```bash
# local Docker full chain
./scripts/verify_end_to_end.sh

# server deployment, using deploy/server/control.sh
./scripts/verify_end_to_end.sh --mode server --biz-dt 2026-07-07
```

The local verification checks:

```text
MySQL insert -> Maxwell -> Kafka -> SparkStreaming -> HDFS ods_binlog
-> PySpark ODS merge -> Hive ODS -> DIM/DWD/DWS/DWT/ADS -> SpringBoot API
```

The same verification can be triggered from the Admin dashboard with the `本地 E2E 验收` or `服务器 E2E 验收` buttons. Logs are shown on the Logs page under `E2E 验收` and `E2E 诊断`.

CI checks on GitHub Actions:

```text
Python unit tests
Python syntax/import checks
SpringBoot Maven compile
Shell syntax checks
Docker Compose config checks
Deployment guide Markdown fence checks
```

PySpark jobs:

```bash
# local/production use the same job entrypoints; only env values differ
bash deploy/run_job.sh spark-streaming
bash deploy/run_job.sh daily-merge 2026-07-06
bash deploy/run_job.sh layers 2026-07-06

# production env file
bash deploy/run_job.sh --env-file deploy/prod/jobs.env daily-merge 2026-07-06
```

Realtime Kudu/Impala:

```bash
# print realtime DDL only
python3 scripts/run_realtime_kudu_smoke.py --dry-run

# local real Kudu/Impala
bash scripts/run_local_kudu_impala_smoke.sh

# consume real Docker Kafka once, then upsert Kudu through Impala
python3 scripts/spark_streaming_kafka_to_kudu_once.py --bootstrap-objects

# continuously consume Docker Kafka in SparkStreaming-style micro-batches
python3 scripts/spark_streaming_kafka_to_kudu_loop.py --bootstrap-objects

# real production Impala/Kudu, after setting IMPALA_* and KUDU_MASTERS
python3 -m realtime.impala.bootstrap
python3 scripts/run_realtime_kudu_smoke.py
```

See `docs/realtime_kudu_impala.md`.

Code walkthrough for interviews:

```text
docs/code_walkthrough_zh.md
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

Alert channel smoke:

```bash
ALERT_CHANNELS=file,stdout python3 scripts/send_test_alert.py
```

Admin auth and alert config:

```text
AUTH_USERS=admin:<pass>:ADMIN,ops:<pass>:OPERATOR,viewer:<pass>:VIEWER
COOKIE_SECURE=true
ALERT_CHANNELS=file,email,dingtalk
```

Control-plane skeleton:

```text
platform/springboot-admin
  /                 dashboard
  /realtime         Kudu/Impala status, realtime tables, realtime views
  /logs             runtime logs and Kafka/container status
  /tasks            Spark task config
  /table-ops        table backfill, lineage check, consistency check, onboarding verification
  /onboarding       MySQL-to-Hive onboarding
  /replay           Maxwell bootstrap/replay
  /monitors         delay/field/special/table/plaintext monitors, Send Test Alert
```

Table-level operations are also available from CLI:

```bash
scripts/table_ops.sh --dry-run backfill basiccomment avatar_commentbatchsource 2026-07-06 2026-07-07
scripts/table_ops.sh check-lineage basiccomment avatar_commentbatchsource 2026-07-07 ods_basiccomment_avatar_commentbatchsource_dic
scripts/table_ops.sh consistency basiccomment avatar_commentbatchsource 2026-07-07 ods_basiccomment_avatar_commentbatchsource_dic ctime
scripts/table_ops.sh backfill basiccomment avatar_commentbatchsource 2026-07-06 2026-07-07
scripts/table_ops.sh onboarding-verify basiccomment avatar_commentbatchsource 2026-07-07 ods_basiccomment_avatar_commentbatchsource_dic
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

Docker local stack:

```bash
./scripts/local_smoke.sh

# or step by step
./scripts/docker_up.sh
./scripts/init_hdfs_hive.sh
./scripts/check_local_stack.sh
./scripts/docker_seed_change.sh
./scripts/kafka_to_jsonl.sh
./scripts/docker_down.sh
```

Full Docker HDFS/Hive E2E:

```bash
./scripts/download_hadoop_hive.sh
./scripts/dev_up.sh
./scripts/dev_check.sh
./scripts/verify_end_to_end.sh
./scripts/run_e2e_hdfs_pipeline.sh
```

This verifies:

```text
MySQL insert -> Maxwell -> Kafka -> SparkStreaming -> HDFS ods_binlog
-> PySpark ODS merge -> Hive ODS -> DIM/DWD/DWS/DWT/ADS
```

Deployment docs:

```text
docs/deployment_guide.md
docs/deployment_guide_zh.md
docs/docker_runbook.md
docs/deployment_profiles.md
docs/realtime_kudu_impala.md
deploy/server/README.md
```

## Server Deployment

Install to a Linux server without Kubernetes:

```bash
sudo deploy/server/install.sh
sudo vim /etc/cdc-warehouse/admin.env
sudo vim /etc/cdc-warehouse/jobs.env
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh preflight
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh start
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
```

Service operations:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh status
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-spark-streaming.service
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh merge
systemctl list-timers | grep cdc-daily-merge
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
