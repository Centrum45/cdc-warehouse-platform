# Server Deployment

This deploys directly to a Linux server with `systemd`. No Kubernetes required.

## Layout

- code: `/opt/cdc-warehouse-platform`
- env: `/etc/cdc-warehouse/admin.env`, `/etc/cdc-warehouse/jobs.env`
- logs: `journalctl`, plus dashboard snapshots under `data/ops`
- user: `cdc`

## Install

On the server:

```bash
sudo deploy/server/install.sh
sudo vim /etc/cdc-warehouse/admin.env
sudo vim /etc/cdc-warehouse/jobs.env
```

Start services:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh preflight
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh start
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
```

## Operations

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh status
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh preflight
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh restart
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh stop
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07 --merge
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh merge

sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-admin.service
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-spark-streaming.service
journalctl -u cdc-daily-merge.service -n 200 --no-pager
```

Admin UI:

```text
http://SERVER_IP:8080/
```

Daily merge timer:

```bash
systemctl list-timers | grep cdc-daily-merge
systemctl cat cdc-daily-merge.timer
```

Production smoke:

```bash
# Read-only checks: services, endpoints, HDFS partitions, Hive counts.
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07

# Also trigger daily ODS merge for that partition.
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07 --merge
```

Uninstall systemd units but keep code/env/logs:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/uninstall.sh
```

Remove code/env/logs too:

```bash
sudo REMOVE_DATA=true /opt/cdc-warehouse-platform/deploy/server/uninstall.sh
```

## Production Notes

- `SPRING_PROFILES_ACTIVE=prod` disables local fallback data.
- Admin startup fails if MySQL or project root is invalid.
- `WAREHOUSE_ACTIONS_PUBLIC_ENABLED=false` keeps pages and action APIs behind login/JWT.
- Change `ADMIN_PASS` and use a strong `JWT_SECRET` before startup.
- `/login` provides browser login. `/api/auth/login` provides API JWT login.
- SparkStreaming expects `kafka-console-consumer` on PATH.
- Ops refresh uses `kafka-topics`, `hdfs`, and `beeline` if installed.

## Required Server Dependencies

- Java 8+.
- Maven, only needed during install build.
- Python 3 with project Python dependencies.
- Kafka client commands: `kafka-console-consumer`, `kafka-topics`.
- Hadoop client command: `hdfs`.
- Hive client command: `beeline`.
- Network access to MySQL, Kafka, HDFS, Hive, DolphinScheduler.

## Env Files

`/etc/cdc-warehouse/admin.env` controls SpringBoot admin:

- MySQL metadata DB.
- admin login and JWT secret.
- DolphinScheduler, Hive, HDFS, WebHDFS endpoints.

`/etc/cdc-warehouse/jobs.env` controls background jobs:

- Kafka bootstrap and topic.
- HDFS warehouse root.
- delay gate and SparkStreaming batch size.
- DolphinScheduler endpoint.
