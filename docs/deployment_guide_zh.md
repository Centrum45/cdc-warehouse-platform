# CDC Warehouse Platform 部署指南

本文说明项目两种部署方式：

- 本地调试：单台电脑，用 Docker Compose 启动完整本地环境。
- 服务器生产部署：Linux 服务器，用 `systemd` 管理服务，连接真实 MySQL、Kafka、HDFS、Hive、DolphinScheduler。

## 1. 架构

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

本地模式会用 Docker 启动 MySQL、Kafka、Maxwell、HDFS、Hive、DolphinScheduler、SparkStreaming、SpringBoot Admin。

服务器模式只安装本项目的 SpringBoot 和长跑任务。MySQL、Kafka、HDFS、Hive、DolphinScheduler 默认由生产环境提供。

## 2. 拉取代码

SSH 方式：

```bash
git clone git@github.com:Centrum45/cdc-warehouse-platform.git
cd cdc-warehouse-platform
git checkout dev
```

HTTPS 方式：

```bash
git clone https://github.com/Centrum45/cdc-warehouse-platform.git
cd cdc-warehouse-platform
git checkout dev
```

## 3. 本地部署

适合 Mac、Linux、开发电脑、测试电脑。建议先跑通本地模式，再考虑服务器部署。

### 3.1 本地依赖

必须安装：

- macOS 或 Linux。
- Docker Desktop 或 Docker Engine。
- Docker Compose v2。
- Git。
- Python 3.8-3.11。不要直接依赖系统 `python3`，项目提供 `.venv` 初始化脚本。
- Docker 可用内存至少 8 GB，推荐 12 GB。
- 磁盘剩余至少 15 GB。

检查命令：

```bash
docker version
docker compose version
python3 --version
git --version
```

初始化 Python 虚拟环境：

```bash
./scripts/setup_python.sh
./scripts/check_dependencies.sh --mode local
./scripts/test.sh
```

说明：

```text
setup_python.sh 创建 .venv 并安装 requirements.txt
test.sh 会优先使用 .venv/bin/python
check_dependencies.sh 检查 pyarrow、Docker、Maven、PySpark 等依赖
```

### 3.2 本地端口

确认这些端口未被占用：

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

检查端口：

```bash
lsof -i :8080
lsof -i :13306
lsof -i :19092
```

如果端口被占用，先停掉旧进程，或修改 `docker/docker-compose.yml` 端口映射。

### 3.3 准备本地环境变量

```bash
cp .env.example .env
```

本地调试默认值即可：

```text
ENVIRONMENT=dev
SPRING_PROFILES_ACTIVE=dev
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=cdc_warehouse_admin
LAKE_ROOT=hdfs://hdfs-namenode:8020/warehouse
```

不要把生产密码写进 `.env`。`.env` 只用于本地。

管理后台默认使用 `ADMIN_USER/ADMIN_PASS`。如果要本地测试多用户权限，可以设置：

```text
AUTH_USERS=admin:admin123:ADMIN,ops:ops123:OPERATOR,viewer:viewer123:VIEWER
COOKIE_SECURE=false
COOKIE_SAME_SITE=Lax
```

告警默认只写 outbox。本地测试可配置：

```text
ALERT_CHANNELS=file,stdout
ALERT_OUTBOX=data/alerts/outbox.jsonl
```

生产邮件/群机器人告警可配置：

```text
ALERT_CHANNELS=file,email,dingtalk
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=cdc-alert@example.com
SMTP_PASS=<change-me>
SMTP_FROM=cdc-alert@example.com
SMTP_TO=dba@example.com
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=...
```

部署后进入 `/monitors`，点击 `Send Test Alert` 验证告警链路。

### 3.4 下载 Hadoop 和 Hive

本地 HDFS/Hive 容器会挂载工作区里的 Hadoop、Hive 二进制包。如果没有下载过，执行：

```bash
./scripts/download_hadoop_hive.sh
```

验证：

```bash
test -x docker/hadoop/dist/hadoop/bin/hdfs && echo HADOOP_OK
test -x docker/hive/dist/hive/bin/hiveserver2 && echo HIVE_OK
```

### 3.5 一条命令本地部署并验收

执行：

```bash
./scripts/dev_up.sh
./scripts/dev_check.sh
```

这两个脚本会完成：

```text
启动 Docker Compose
初始化 HDFS/Hive
插入 MySQL 测试数据
Maxwell -> Kafka CDC
Kafka -> HDFS ods_binlog
PySpark ODS merge
Hive DIM/DWD/DWS/DWT/ADS 分层任务
本地健康检查
```

期望最终输出：

```text
summary ok=4 fail=0
```

看到这个结果，本地部署成功。

### 3.6 分步骤本地部署

如果不想一条命令跑，可以分步骤执行：

```bash
./scripts/setup_python.sh
./scripts/check_dependencies.sh --mode local
./scripts/docker_up.sh
./scripts/init_hdfs_hive.sh
./scripts/verify_end_to_end.sh
```

停止本地环境：

```bash
./scripts/docker_down.sh
```

如果想完全清理重来：

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hive.yml down -v
rm -rf data/hdfs data/hive data/checkpoints data/progress data/ops
```

然后重新跑：

```bash
./scripts/dev_up.sh
./scripts/dev_check.sh
```

### 3.7 本地访问地址

SpringBoot Admin：

```text
http://localhost:8080/
```

HDFS UI：

```text
http://localhost:9870/
```

DolphinScheduler：

```text
http://localhost:12345/dolphinscheduler
```

MySQL：

```bash
docker exec -it cdc-warehouse-mysql mysql -uroot -proot
```

Kafka topic：

```bash
docker exec cdc-warehouse-kafka kafka-topics --bootstrap-server kafka:9092 --list
```

HDFS warehouse：

```bash
docker exec cdc-warehouse-hdfs-namenode hdfs dfs -ls -R /warehouse
```

Hive：

```bash
docker exec -it cdc-warehouse-hive-server beeline -u jdbc:hive2://localhost:10000
```

### 3.8 本地数据查看

ODS binlog：

```bash
docker exec cdc-warehouse-hdfs-namenode \
  hdfs dfs -ls /warehouse/ods_binlog/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-07
```

ODS snapshot：

```bash
docker exec cdc-warehouse-hdfs-namenode \
  hdfs dfs -ls /warehouse/ods/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-07
```

ADS：

```bash
docker exec cdc-warehouse-hive-server beeline \
  -u jdbc:hive2://localhost:10000 \
  -e "select * from ads.ads_comment_dashboard_1d where dt='2026-07-07';"
```

日期 `2026-07-07` 按实际运行日期替换。正常取 T-1。

### 3.9 本地日志

容器状态：

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hive.yml ps
```

关键日志：

```bash
docker logs -f cdc-warehouse-admin
docker logs -f cdc-warehouse-maxwell
docker logs -f cdc-warehouse-kafka
docker logs -f cdc-warehouse-spark-streaming
docker logs -f cdc-warehouse-hdfs-namenode
docker logs -f cdc-warehouse-hive-server
```

页面用的运维快照日志：

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

### 3.10 本地常见问题

Docker 内存太小：

```text
Hive 或 DolphinScheduler 启动慢、退出、卡住。
```

解决：Docker Desktop 分配至少 8 GB 内存。

端口被占用：

```text
Bind for 0.0.0.0:8080 failed: port is already allocated.
```

解决：

```bash
lsof -i :8080
```

停掉占用进程，或修改 `docker/docker-compose.yml`。

Hadoop/Hive 缺失：

```text
missing Hadoop. run ./scripts/download_hadoop_hive.sh
missing Hive. run ./scripts/download_hadoop_hive.sh
```

解决：

```bash
./scripts/download_hadoop_hive.sh
```

HDFS safe mode：

```text
Name node is in safe mode.
```

解决：

```bash
docker exec cdc-warehouse-hdfs-namenode hdfs dfsadmin -safemode leave
./scripts/init_hdfs_hive.sh
```

MySQL 插入后没有同步到数仓：

```bash
docker logs --tail 200 cdc-warehouse-maxwell
docker logs --tail 200 cdc-warehouse-spark-streaming
docker exec cdc-warehouse-kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic cdc.incremental.binlog \
  --from-beginning \
  --max-messages 5
```

然后重新跑：

```bash
./scripts/run_e2e_hdfs_pipeline.sh
```

## 4. 服务器生产部署

适合直接部署到 Linux 服务器，不需要 Kubernetes。

生产部署推荐主路径是 `deploy/server/*`：它会安装 systemd service/timer，并统一管理 SpringBoot、SparkStreaming、每日 merge 和运维快照。`deploy/prod/*` 只作为手动启动 Admin 或手动提交任务的辅助入口，不作为主部署方式。

### 4.1 生产环境前提

本项目不负责安装生产 MySQL、Kafka、HDFS、Hive、DolphinScheduler。生产环境里这些服务应该已经存在。

本项目在服务器上安装和管理：

```text
cdc-admin.service
cdc-spark-streaming.service
cdc-ops-refresh.service
cdc-daily-merge.service
cdc-daily-merge.timer
```

### 4.2 服务器依赖

推荐系统：

- CentOS 7+/Rocky Linux/Ubuntu 20.04+。
- 支持 `systemd`。

必须有这些命令：

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

Python 依赖使用项目内 `.venv` 管理。服务器安装完成后，在 `/opt/cdc-warehouse-platform` 下执行：

```bash
sudo -u cdc /opt/cdc-warehouse-platform/scripts/setup_python.sh
sudo -u cdc /opt/cdc-warehouse-platform/scripts/check_dependencies.sh --mode prod
```

Ubuntu 示例：

```bash
sudo apt-get update
sudo apt-get install -y git rsync openjdk-8-jdk maven python3 curl mysql-client
```

CentOS/Rocky 示例：

```bash
sudo yum install -y git rsync java-1.8.0-openjdk-devel maven python3 curl mysql
```

Kafka/Hadoop/Hive 客户端通常来自公司大数据客户端包。安装后验证：

```bash
java -version
mvn -version
python3 --version
kafka-topics --version
hdfs version
beeline --version
mysql --version
```

### 4.3 服务器网络检查

在部署服务器上先验证能连通外部系统：

```bash
mysql -h MYSQL_HOST -P 3306 -u USER -p -e 'select 1'
kafka-topics --bootstrap-server KAFKA_HOST:9092 --list
hdfs dfs -ls /warehouse
beeline -u jdbc:hive2://HIVE_HOST:10000 -e 'show databases;'
curl -I http://DOLPHINSCHEDULER_HOST:12345/dolphinscheduler
```

如果任一命令失败，先解决网络、防火墙、DNS、Kerberos、客户端配置，再部署本项目。

### 4.4 服务器目录

安装后目录：

```text
/opt/cdc-warehouse-platform        项目代码
/etc/cdc-warehouse/admin.env       SpringBoot Admin 环境变量
/etc/cdc-warehouse/jobs.env        任务环境变量
/var/log/cdc-warehouse             预留日志目录
```

systemd 日志通过 `journalctl` 查看。

页面运维快照文件在：

```text
/opt/cdc-warehouse-platform/data/ops
```

### 4.5 服务器安装

拉代码：

```bash
git clone git@github.com:Centrum45/cdc-warehouse-platform.git
cd cdc-warehouse-platform
git checkout dev
```

执行安装：

```bash
sudo deploy/server/install.sh
```

如果想先做不写入系统目录的演练：

```bash
deploy/server/install.sh --dry-run
```

安装脚本会做：

```text
创建 cdc 系统用户
复制代码到 /opt/cdc-warehouse-platform
如果 env 文件不存在，则创建 /etc/cdc-warehouse/*.env
构建 SpringBoot jar
安装 systemd unit
reload systemd
```

### 4.6 配置服务器环境变量

编辑 Admin 配置：

```bash
sudo vim /etc/cdc-warehouse/admin.env
```

示例：

```env
SPRING_PROFILES_ACTIVE=prod
WAREHOUSE_PROJECT_ROOT=/opt/cdc-warehouse-platform
SERVER_PORT=8080
WAREHOUSE_ACTIONS_PUBLIC_ENABLED=false

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
LAKE_ROOT=hdfs://nameservice1/warehouse
WAREHOUSE_HDFS_ROOT=hdfs://nameservice1/warehouse
WEBHDFS_ENDPOINT=http://namenode.prod.example.com:9870
WEBHDFS_USER=hdfs
KAFKA_BOOTSTRAP_SERVERS=kafka01.prod.example.com:9092,kafka02.prod.example.com:9092
KAFKA_TOPIC=cdc.incremental.binlog
```

编辑任务配置：

```bash
sudo vim /etc/cdc-warehouse/jobs.env
```

示例：

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
MERGE_AUDIT_ROOT=data/ops/merge_audit
MERGE_BACKUP_ROOT=hdfs://nameservice1/warehouse/ods_backup

SPARK_MASTER=local[2]
SPARK_KAFKA_PACKAGE=org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1
SPARK_STREAMING_CHECKPOINT=hdfs://nameservice1/warehouse/checkpoints/offline_sink
SPARK_STARTING_OFFSETS=latest
SPARK_MAX_OFFSETS_PER_TRIGGER=1000
SPARK_BAD_RECORDS_PATH=hdfs://nameservice1/warehouse/dead_letter/offline_sink
SPARK_STREAMING_INTERVAL_SECONDS=5

DS_ENDPOINT=http://dolphinscheduler.prod.example.com:12345/dolphinscheduler
DS_TOKEN=your_ds_token
```

可选实时 Kudu/Impala 配置：

```env
IMPALA_HOST=impala.prod.example.com
IMPALA_PORT=21050
IMPALA_USER=cdc_user
IMPALA_PASSWORD=your_password
IMPALA_AUTH_MECHANISM=PLAIN
KUDU_MASTERS=kudu-master-1.prod.example.com:7051,kudu-master-2.prod.example.com:7051
```

保护 env 文件权限：

```bash
sudo chown root:cdc /etc/cdc-warehouse/*.env
sudo chmod 640 /etc/cdc-warehouse/*.env
```

### 4.7 初始化生产元数据库

SpringBoot 需要管理平台元数据库表。SQL 文件：

```text
platform/springboot-admin/src/main/resources/schema.sql
platform/springboot-admin/src/main/resources/data.sql
```

导入 MySQL：

```bash
mysql -h MYSQL_HOST -P 3306 -u cdc_admin -p cdc_warehouse_admin \
  < platform/springboot-admin/src/main/resources/schema.sql

mysql -h MYSQL_HOST -P 3306 -u cdc_admin -p cdc_warehouse_admin \
  < platform/springboot-admin/src/main/resources/data.sql
```

如果生产库已经有数据，执行前先审查 SQL。

### 4.8 启动服务器服务

启动：

```bash
cd /opt/cdc-warehouse-platform
sudo -u cdc ./scripts/setup_python.sh
sudo -u cdc ./scripts/check_dependencies.sh --mode prod
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh preflight
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh start
```

健康检查：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
```

期望输出：

```text
summary: ok=N fail=0
```

访问 Admin：

```text
http://SERVER_IP:8080/
```

### 4.9 生产 smoke 验收

只读 smoke：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07
```

检查内容：

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

如果生产已经有 Kudu/Impala 集群，也可以跑实时链路 smoke：

```bash
cd /opt/cdc-warehouse-platform
python3 scripts/run_realtime_kudu_smoke.py
```

触发 ODS merge 并验收：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07 --merge
```

日期换成真实业务日期。通常用 T-1。

### 4.10 服务器运维命令

状态：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh status
```

重启：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh restart
```

停止：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh stop
```

日志：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-admin.service
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-spark-streaming.service
journalctl -u cdc-daily-merge.service -n 200 --no-pager
```

手动跑每日 merge：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh merge
```

查看定时器：

```bash
systemctl list-timers | grep cdc-daily-merge
systemctl cat cdc-daily-merge.timer
```

默认每天执行时间：

```text
02:30
```

修改定时器：

```text
deploy/server/cdc-daily-merge.timer
```

修改后复制并重载：

```bash
sudo cp deploy/server/cdc-daily-merge.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart cdc-daily-merge.timer
```

### 4.11 服务器升级

拉最新代码：

```bash
cd cdc-warehouse-platform
git pull origin dev
sudo deploy/server/install.sh
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh restart
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
```

安装脚本不会覆盖已有的 `/etc/cdc-warehouse/*.env`。

### 4.12 服务器卸载

只删除 systemd 服务，保留代码、env、日志：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/uninstall.sh
```

全部删除：

```bash
sudo REMOVE_DATA=true /opt/cdc-warehouse-platform/deploy/server/uninstall.sh
```

### 4.13 生产常见问题

Admin 启动失败：

```bash
journalctl -u cdc-admin.service -n 200 --no-pager
```

常见原因：

```text
MySQL URL/user/password 错误
元数据库 schema 未初始化
SPRING_PROFILES_ACTIVE 配置错误
WAREHOUSE_PROJECT_ROOT 错误
8080 端口被占用
```

SparkStreaming 服务失败：

```bash
journalctl -u cdc-spark-streaming.service -n 200 --no-pager
```

常见原因：

```text
kafka-console-consumer 不在 PATH
KAFKA_BOOTSTRAP_SERVERS 错误
HDFS client 配置缺失
LAKE_ROOT 错误
/warehouse 权限不足
```

Daily merge 失败：

```bash
journalctl -u cdc-daily-merge.service -n 200 --no-pager
```

常见原因：

```text
delay gate 未通过
ODS binlog 分区不存在
使用 pyspark engine 但 PySpark 缺失
HDFS 权限不足
Hive 表或分区缺失
```

HDFS 权限问题：

```bash
hdfs dfs -ls /warehouse
hdfs dfs -mkdir -p /warehouse/ods_binlog /warehouse/ods /warehouse/ads
hdfs dfs -chmod -R 775 /warehouse
```

Kafka 没有 CDC 数据：

```bash
kafka-topics --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" --list
kafka-console-consumer \
  --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
  --topic cdc.incremental.binlog \
  --from-beginning \
  --max-messages 5
```

需要确认 Maxwell 正在运行，并指向正确 MySQL binlog 源。

## 5. 成功标准

本地成功：

```bash
./scripts/local_smoke.sh
```

最终输出：

```text
summary: ok=19 warn=0 fail=0
local smoke done
```

服务器成功：

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt YYYY-MM-DD
```

最终输出：

```text
fail=0
```

然后打开：

```text
http://SERVER_IP:8080/
```

## 6. 常用命令速查

本地：

```bash
./scripts/local_smoke.sh
./scripts/check_local_stack.sh
./scripts/docker_down.sh
```

服务器：

```bash
sudo deploy/server/install.sh
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh start
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt YYYY-MM-DD
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-admin.service
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh restart
```
