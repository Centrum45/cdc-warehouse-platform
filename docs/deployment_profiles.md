# Deployment Profiles

## Local Debug

Use Docker Compose. It starts MySQL, Maxwell, Kafka, SparkStreaming, HDFS, Hive, DolphinScheduler, and SpringBoot admin.

```bash
cp .env.example .env
./scripts/setup_python.sh
./scripts/check_dependencies.sh --mode local
./scripts/dev_up.sh
./scripts/dev_check.sh
```

Defaults:

- `ENVIRONMENT=dev`
- `SPRING_PROFILES_ACTIVE=dev`
- SpringBoot can read local fallback JSON when MySQL metadata is empty
- `/api/actions/**` is public for local button-driven debugging

## Production Manual Helpers

Production uses external MySQL, Kafka, HDFS, Hive, and DolphinScheduler. Docker Compose is not required.

The recommended production path is **Direct Server Deployment** below. `deploy/prod/*` is kept as a manual helper for starting Admin or submitting individual jobs without systemd.

```bash
cp deploy/prod/admin.env.example deploy/prod/admin.env
cp deploy/prod/jobs.env.example deploy/prod/jobs.env
```

Fill real endpoints and secrets, then run:

```bash
./scripts/prod_preflight.sh deploy/prod/jobs.env deploy/prod/admin.env
deploy/prod/run_admin.sh deploy/prod/admin.env
deploy/prod/submit_daily_merge.sh deploy/prod/jobs.env 2026-07-07
bash deploy/run_job.sh --env-file deploy/prod/jobs.env spark-streaming
bash deploy/run_job.sh --env-file deploy/prod/jobs.env layers 2026-07-07
```

Production defaults:

- `SPRING_PROFILES_ACTIVE=prod`
- fallback demo data disabled
- startup validation enabled
- SpringBoot fails fast when MySQL or project root is wrong
- `/api/actions/**` requires JWT auth

## Direct Server Deployment

Use this when one or more Linux servers already have access to production MySQL, Kafka, HDFS, Hive, and DolphinScheduler.

```bash
sudo deploy/server/install.sh
sudo vim /etc/cdc-warehouse/admin.env
sudo vim /etc/cdc-warehouse/jobs.env
cd /opt/cdc-warehouse-platform
sudo -u cdc ./scripts/setup_python.sh
sudo -u cdc ./scripts/check_dependencies.sh --mode prod
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh preflight
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh start
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
```

Services:

- `cdc-admin.service`: SpringBoot data management platform.
- `cdc-spark-streaming.service`: Kafka binlog consumer, writes ODS binlog to HDFS.
- `cdc-ops-refresh.service`: refreshes dashboard logs/status every few seconds.
- `cdc-daily-merge.timer`: triggers daily ODS snapshot merge.

Common commands:

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh status
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh logs cdc-admin.service
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt 2026-07-07
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh merge
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh restart
```

## Config Boundary

Code must not hardcode environment endpoints. Use env vars or `configs/app-prod.yaml`.

Python-side config is intentionally split into only two files:

- `configs/app-dev.yaml` for local Docker/debug defaults.
- `configs/app-prod.yaml` for production, with real endpoints injected through env vars.

Local data paths are acceptable only in `dev`. Production paths should point to HDFS or external services.
Spark/Python tasks use `deploy/run_job.sh` in both local and production; deployment mode changes only env values.
