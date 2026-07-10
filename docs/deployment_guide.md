# CDC Warehouse Platform Deployment Guide

This document describes how to deploy the project in two modes:

- Local debug: one machine, Docker Compose, full local stack.
- Server production: Linux server with `systemd`, connecting to real MySQL, Kafka, HDFS, Hive, and DolphinScheduler.

## 1. Architecture

```text
MySQL
  -> Maxwell
  -> Kafka topic cdc.incremental.binlog
  -> SparkStreaming-style consumer
  -> HDFS /warehouse/ods_binlog
  -> Daily ODS merge
  -> Hive ODS/DIM/DWD/DWS/DWT/ADS
  -> SpringBoot Admin dashboard
```

Local mode starts MySQL, Kafka, Maxwell, HDFS, Hive, DolphinScheduler, SparkStreaming, and SpringBoot Admin in Docker.

Server mode installs SpringBoot and long-running jobs as `systemd` services. MySQL, Kafka, HDFS, Hive, and DolphinScheduler are expected to already exist.

## 2. Repository

Clone the repository:

```bash
git clone git@github.com:Centrum45/cdc-warehouse-platform.git
cd cdc-warehouse-platform
git checkout dev
```

If SSH is not configured:

```bash
git clone https://github.com/Centrum45/cdc-warehouse-platform.git
cd cdc-warehouse-platform
git checkout dev
```

## 3. Local Deployment

Use this mode on a developer laptop or another local machine. It is the recommended first deployment path.

### 3.1 Local Requirements

Required:

- macOS or Linux.
- Docker Desktop or Docker Engine.
- Docker Compose v2.
- Git.
- Python 3.
- At least 8 GB memory available for Docker. 12 GB is better.
- At least 15 GB free disk.

Check:

```bash
docker version
docker compose version
python3 --version
git --version
```

### 3.2 Local Ports

Make sure these ports are free:

```text
8080   SpringBoot Admin
13306  MySQL
19092  Kafka external listener
2181   ZooKeeper
8020   HDFS RPC
9870   HDFS Web UI / WebHDFS
9864   HDFS DataNode HTTP
9866   HDFS DataNode transfer
10000  HiveServer2
12345  DolphinScheduler API
25333  DolphinScheduler worker/master port
```

On macOS/Linux:

```bash
lsof -i :8080
lsof -i :13306
lsof -i :19092
```

If a port is occupied, stop the old process or change the compose port mapping.

### 3.3 Prepare Local Env

```bash
cp .env.example .env
```

For local debug, these defaults are enough:

```text
ENVIRONMENT=dev
SPRING_PROFILES_ACTIVE=dev
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=cdc_warehouse_admin
LAKE_ROOT=hdfs://hdfs-namenode:8020/warehouse
```

Do not put production secrets into `.env`. `.env` is local only.

### 3.4 Download Hadoop And Hive

The local HDFS/Hive containers mount Hadoop and Hive binaries from the repo workspace. If not already present, run:

```bash
./scripts/download_hadoop_hive.sh
```

Verify:

```bash
test -x docker/hadoop/dist/hadoop/bin/hdfs && echo HADOOP_OK
test -x docker/hive/dist/hive/bin/hiveserver2 && echo HIVE_OK
```

### 3.5 One-Command Local Smoke

Run:

```bash
./scripts/local_smoke.sh
```

This command does:

```text
Docker Compose up
HDFS/Hive initialization
MySQL test insert
Maxwell -> Kafka CDC
Kafka -> HDFS ods_binlog
PySpark ODS merge
Hive DIM/DWD/DWS/DWT/ADS jobs
Local health check
```

Expected final output:

```text
summary: ok=19 warn=0 fail=0
local smoke done
```

### 3.6 Step-By-Step Local Deployment

If you do not want the one-command smoke:

```bash
./scripts/docker_up.sh
./scripts/init_hdfs_hive.sh
./scripts/run_e2e_hdfs_pipeline.sh
./scripts/check_local_stack.sh
```

Stop local stack:

```bash
./scripts/docker_down.sh
```

Remove Docker volumes if you want a clean rebuild:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hive.yml down -v
rm -rf data/hdfs data/hive data/checkpoints data/progress data/ops
```

Then rerun:

```bash
./scripts/local_smoke.sh
```

### 3.7 Local Access

SpringBoot Admin:

```text
http://localhost:8080/
```

HDFS UI:

```text
http://localhost:9870/
```

DolphinScheduler:

```text
http://localhost:12345/dolphinscheduler
```

MySQL:

```bash
docker exec -it cdc-warehouse-mysql mysql -uroot -proot
```

Kafka topics:

```bash
docker exec cdc-warehouse-kafka kafka-topics --bootstrap-server kafka:9092 --list
```

HDFS warehouse:

```bash
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls -R /warehouse
```

Hive:

```bash
docker exec -it cdc-warehouse-hive-server beeline -u jdbc:hive2://localhost:10000
```

### 3.8 Local Data Checks

ODS binlog:

```bash
docker exec cdc-warehouse-hdfs-namenode \
  hdfs dfs -cat /warehouse/ods_binlog/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-07/part-00000.jsonl
```

ODS snapshot:

```bash
docker exec cdc-warehouse-hdfs-namenode \
  hdfs dfs -cat /warehouse/ods/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-07/part-*.csv
```

ADS:

```bash
docker exec cdc-warehouse-hive-server beeline \
  -u jdbc:hive2://localhost:10000 \
  -e "select * from ads.ads_comment_dashboard_1d where dt='2026-07-07';"
```

Use current T-1 date if your run date is different.

### 3.9 Local Logs

Container status:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hive.yml ps
```

Important logs:

```bash
docker logs -f cdc-warehouse-admin
docker logs -f cdc-warehouse-maxwell
docker logs -f cdc-warehouse-kafka
docker logs -f cdc-warehouse-spark-streaming
docker logs -f cdc-warehouse-hdfs-namenode
docker logs -f cdc-warehouse-hive-server
```

Dashboard snapshot logs:

```text
data/ops/container_status.txt
data/ops/admin.log
data/ops/maxwell.log
data/ops/kafka.log
data/ops/spark_streaming.log
data/ops/hdfs_warehouse_ls.txt
data/ops/hive_databases.txt
data/ops/e2e_hdfs_pipeline.log
data/ops/local_smoke.log
```

### 3.10 Local Common Failures

Docker memory too small:

```text
Hive or DolphinScheduler exits or hangs.
```

Fix: give Docker at least 8 GB memory.

Port occupied:

```text
Bind for 0.0.0.0:8080 failed: port is already allocated.
```

Fix:

```bash
lsof -i :8080
```

Stop the occupying process or edit `docker/docker-compose.yml`.

Hadoop/Hive missing:

```text
missing Hadoop. run ./scripts/download_hadoop_hive.sh
missing Hive. run ./scripts/download_hadoop_hive.sh
```

Fix:

```bash
./scripts/download_hadoop_hive.sh
```

HDFS safe mode:

```text
Name node is in safe mode.
```

Fix:

```bash
docker exec cdc-warehouse-hdfs-namenode hdfs dfsadmin -safemode leave
./scripts/init_hdfs_hive.sh
```

MySQL data seems not synced:

```bash
docker logs --tail 200 cdc-warehouse-maxwell
docker logs --tail 200 cdc-warehouse-spark-streaming
docker exec cdc-warehouse-kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic cdc.incremental.binlog \
  --from-beginning \
  --max-messages 5
```

Then run:

```bash
./scripts/run_e2e_hdfs_pipeline.sh
```

## 4. Server Production Deployment

Use this mode when deploying to a Linux server without Kubernetes.

### 4.1 Production Assumptions

The project does not install production MySQL/Kafka/HDFS/Hive/DolphinScheduler. Those systems should already exist.

The server deployment installs and manages:

```text
cdc-admin.service
cdc-spark-streaming.service
cdc-ops-refresh.service
cdc-daily-merge.service
cdc-daily-merge.timer
```

### 4.2 Server Requirements

Recommended OS:

- CentOS 7+/Rocky Linux/Ubuntu 20.04+.
- `systemd`.

Required commands:

```text
git
rsync
java
mvn
python3
kafka-topics
kafka-console-consumer
hdfs
beeline
mysql
curl
```

Install examples:

Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y git rsync openjdk-8-jdk maven python3 curl mysql-client
```

CentOS/Rocky:

```bash
sudo yum install -y git rsync java-1.8.0-openjdk-devel maven python3 curl mysql
```

Kafka/Hadoop/Hive clients usually come from your company big-data client package. After installation, verify:

```bash
java -version
mvn -version
python3 --version
kafka-topics --version
hdfs version
beeline --version
mysql --version
```

### 4.3 Server Network Checklist

From the deployment server, verify access to external systems:

```bash
mysql -h MYSQL_HOST -P 3306 -u USER -p -e 'select 1'
kafka-topics --bootstrap-server KAFKA_HOST:9092 --list
hdfs dfs -ls /warehouse
beeline -u jdbc:hive2://HIVE_HOST:10000 -e 'show databases;'
curl -I http://DOLPHINSCHEDULER_HOST:12345/dolphinscheduler
```

If any command fails, fix network, firewall, DNS, Kerberos, or client config before installing this project.

### 4.4 Server Directory Layout

The installer uses:

```text
/opt/cdc-warehouse-platform        project code
/etc/cdc-warehouse/admin.env       SpringBoot Admin env
/etc/cdc-warehouse/jobs.env        job env
/var/log/cdc-warehouse             reserved log dir
```

System logs go to `journalctl`.

Dashboard snapshot files go to:

```text
/opt/cdc-warehouse-platform/data/ops
```

### 4.5 Install On Server

Clone code:

```bash
git clone git@github.com:Centrum45/cdc-warehouse-platform.git
cd cdc-warehouse-platform
git checkout dev
```

Run installer:

```bash
sudo deploy/server/install.sh
```

Preview install actions first if you want a no-write check:

```bash
deploy/server/install.sh --dry-run
```

Installer does:

```text
create cdc system user
copy code to /opt/cdc-warehouse-platform
create env files under /etc/cdc-warehouse if absent
build SpringBoot jar
install systemd unit files
reload systemd
```

### 4.6 Configure Server Env

Edit admin env:

```bash
sudo vim /etc/cdc-warehouse/admin.env
```

Example:

```env
SPRING_PROFILES_ACTIVE=prod
WAREHOUSE_PROJECT_ROOT=/opt/cdc-warehouse-platform
SERVER_PORT=8080

DB_HOST=mysql.prod.example.com
DB_PORT=3306
DB_NAME=cdc_warehouse_admin
DB_USER=cdc_admin
DB_PASSWORD=your_password

ADMIN_USER=admin
ADMIN_PASS=your_admin_password
JWT_SECRET=replace_with_long_random_secret

DS_ENDPOINT=http://dolphinscheduler.prod.example.com:12345/dolphinscheduler
DS_TOKEN=your_ds_token
HIVE_JDBC_URL=jdbc:hive2://hive.prod.example.com:10000
WAREHOUSE_HDFS_ROOT=hdfs://nameservice1/warehouse
WEBHDFS_ENDPOINT=http://namenode.prod.example.com:9870
WEBHDFS_USER=hdfs
```

Edit job env:

```bash
sudo vim /etc/cdc-warehouse/jobs.env
```

Example:

```env
ENVIRONMENT=prod
PROJECT_ROOT=/opt/cdc-warehouse-platform

KAFKA_BOOTSTRAP_SERVERS=kafka01.prod.example.com:9092,kafka02.prod.example.com:9092
KAFKA_TOPIC=cdc.incremental.binlog

LAKE_ROOT=hdfs://nameservice1/warehouse
WAREHOUSE_HDFS_ROOT=hdfs://nameservice1/warehouse
WEBHDFS_ENDPOINT=http://namenode.prod.example.com:9870
WEBHDFS_USER=hdfs

PROGRESS_ROOT=/warehouse/progress
DELAY_GATE_MAX_SECONDS=1800

SPARK_STREAMING_INTERVAL_SECONDS=5
SPARK_STREAMING_MAX_MESSAGES=500
SPARK_STREAMING_TIMEOUT_MS=10000

DS_ENDPOINT=http://dolphinscheduler.prod.example.com:12345/dolphinscheduler
DS_TOKEN=your_ds_token
```

Protect env files:

```bash
sudo chown root:cdc /etc/cdc-warehouse/*.env
sudo chmod 640 /etc/cdc-warehouse/*.env
```

### 4.7 Initialize Production Metadata DB

SpringBoot expects the admin metadata DB schema. Use:

```text
platform/springboot-admin/src/main/resources/schema.sql
platform/springboot-admin/src/main/resources/data.sql
```

Load into MySQL:

```bash
mysql -h MYSQL_HOST -P 3306 -u cdc_admin -p cdc_warehouse_admin \
  < platform/springboot-admin/src/main/resources/schema.sql

mysql -h MYSQL_HOST -P 3306 -u cdc_admin -p cdc_warehouse_admin \
  < platform/springboot-admin/src/main/resources/data.sql
```

If your production metadata already exists, review SQL before running.

### 4.8 Start Server Services

Start:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh preflight
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh start
```

Health check:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
```

Expected:

```text
summary: ok=N fail=0
```

Access Admin:

```text
http://SERVER_IP:8080/
```

### 4.9 Production Smoke

Read-only smoke:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07
```

This checks:

```text
systemd services
Admin HTTP
MySQL select 1
Kafka topic list
HDFS /warehouse
Hive show databases
ODS binlog partition
ODS snapshot partition
ADS partition
Hive ODS count
Hive ADS count
```

Run smoke and trigger ODS merge:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07 --merge
```

Use a real business date. Normally this is T-1.

### 4.10 Server Operations

Status:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh status
```

Restart:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh restart
```

Stop:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh stop
```

Logs:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-admin.service
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-spark-streaming.service
journalctl -u cdc-daily-merge.service -n 200 --no-pager
```

Manual daily merge:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh merge
```

Timer:

```bash
systemctl list-timers | grep cdc-daily-merge
systemctl cat cdc-daily-merge.timer
```

The default timer runs at:

```text
02:30 daily
```

Change it in:

```text
deploy/server/cdc-daily-merge.timer
```

Then reinstall or copy the unit file and reload:

```bash
sudo cp deploy/server/cdc-daily-merge.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart cdc-daily-merge.timer
```

### 4.11 Server Upgrade

Pull new code:

```bash
cd cdc-warehouse-platform
git pull origin dev
sudo deploy/server/install.sh
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh restart
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
```

The installer does not overwrite existing `/etc/cdc-warehouse/*.env`.

### 4.12 Server Uninstall

Remove services but keep code/env/logs:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/uninstall.sh
```

Remove everything:

```bash
sudo REMOVE_DATA=true /opt/cdc-warehouse-platform/deploy/server/uninstall.sh
```

### 4.13 Production Common Failures

Admin fails to start:

```bash
journalctl -u cdc-admin.service -n 200 --no-pager
```

Common causes:

```text
MySQL URL/user/password wrong
metadata schema missing
SPRING_PROFILES_ACTIVE not prod/dev as expected
WAREHOUSE_PROJECT_ROOT wrong
port 8080 occupied
```

SparkStreaming service fails:

```bash
journalctl -u cdc-spark-streaming.service -n 200 --no-pager
```

Common causes:

```text
kafka-console-consumer not on PATH
KAFKA_BOOTSTRAP_SERVERS wrong
HDFS client config missing
LAKE_ROOT wrong
permission denied on /warehouse
```

Daily merge fails:

```bash
journalctl -u cdc-daily-merge.service -n 200 --no-pager
```

Common causes:

```text
delay gate not passed
ODS binlog partition missing
PySpark missing if engine=pyspark
HDFS permission denied
Hive table not repaired or missing
```

HDFS permission issue:

```bash
hdfs dfs -ls /warehouse
hdfs dfs -mkdir -p /warehouse/ods_binlog /warehouse/ods /warehouse/ads
hdfs dfs -chmod -R 775 /warehouse
```

Kafka has no CDC data:

```bash
kafka-topics --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" --list
kafka-console-consumer \
  --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
  --topic cdc.incremental.binlog \
  --from-beginning \
  --max-messages 5
```

Maxwell must be running and pointed to the correct MySQL binlog source.

## 5. What Success Looks Like

Local success:

```bash
./scripts/local_smoke.sh
```

Final output:

```text
summary: ok=19 warn=0 fail=0
local smoke done
```

Server success:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt YYYY-MM-DD
```

Final output:

```text
fail=0
```

Then open:

```text
http://SERVER_IP:8080/
```

## 6. Quick Command Reference

Local:

```bash
./scripts/local_smoke.sh
./scripts/check_local_stack.sh
./scripts/docker_down.sh
```

Server:

```bash
sudo deploy/server/install.sh
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh start
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt YYYY-MM-DD
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-admin.service
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh restart
```
