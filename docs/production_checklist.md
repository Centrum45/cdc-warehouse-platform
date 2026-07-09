# Production Checklist

Use this before exposing the platform outside local debugging.

## Security

- `SPRING_PROFILES_ACTIVE=prod`
- `WAREHOUSE_ACTIONS_PUBLIC_ENABLED=false`
- `ADMIN_PASS` changed from the default
- `JWT_SECRET` is at least 32 characters and not shared with dev
- Admin UI is behind company network, VPN, or reverse proxy access control
- MySQL/Kafka/Hive/HDFS credentials are passed by env files, not committed

## Preflight

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh preflight
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh health
```

## Runtime

- `cdc-admin.service` is running
- `cdc-spark-streaming.service` is running
- `cdc-ops-refresh.service` is running
- `cdc-daily-merge.timer` is enabled
- `/logs` shows recent Maxwell, Kafka, SparkStreaming, and Admin logs

## Data

- HDFS warehouse root exists
- `ods_binlog` receives new partitions
- daily ODS merge writes ODS snapshots
- Hive partitions can be repaired with `msck repair table`
- ADS tables return rows for the latest business date

## Smoke

```bash
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt YYYY-MM-DD
sudo /opt/cdc-warehouse-platform/deploy/server/control.sh smoke --biz-dt YYYY-MM-DD --merge
```

## Rollback

- Keep the previous release directory or Git commit hash.
- Stop services before switching code.
- Start with `control.sh start`.
- Run `control.sh health` and `control.sh smoke`.
