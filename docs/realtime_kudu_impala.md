# Realtime Kudu / Impala

The production realtime path uses PySpark Structured Streaming to consume
Maxwell events and writes latest-row state to Kudu through Impala SQL.

```text
Kafka / JSONL binlog
  -> streaming/realtime_sink/pyspark_kafka_to_kudu.py
  -> Impala UPSERT/DELETE
  -> Kudu tables
  -> Impala realtime views
```

## Requirements

Install Python client dependencies:

```bash
scripts/setup_python.sh
```

Set production environment variables as needed:

```bash
export IMPALA_HOST=impala.example.com
export IMPALA_PORT=21050
export IMPALA_USER=cdc_user
export IMPALA_PASSWORD='your_password'
export IMPALA_AUTH_MECHANISM=PLAIN
export KUDU_MASTERS=kudu-master-1.example.com:7051,kudu-master-2.example.com:7051
```

Auth variables are optional. Use what your Impala cluster requires.

## Local Kudu / Impala

This repo includes a single-node local Kudu/Impala stack:

```bash
docker compose -f docker/docker-compose.kudu.yml up -d
```

The local Kudu stack uses `--time_source=system_unsync` so Docker Desktop can run it without host NTP privileges. Do not use that flag in production.
The sample Kudu tables set `kudu.num_tablet_replicas=1` for this single-tablet-server stack. Use `3` or your production replica policy in a real cluster.

Ports:

```text
Kudu master RPC:  localhost:7051
Kudu master UI:   http://localhost:8051
Kudu tserver RPC: localhost:7050
Kudu tserver UI:  http://localhost:8050
Impala JDBC/ODBC: localhost:21050
Impala UI:        http://localhost:25000
```

Local env:

```bash
export IMPALA_HOST=localhost
export IMPALA_PORT=21050
export KUDU_MASTERS=kudu-master:7051
```

Run full local smoke:

```bash
bash scripts/run_local_kudu_impala_smoke.sh
```

Run one Kafka-to-Kudu micro-batch:

```bash
python3 scripts/spark_streaming_kafka_to_kudu_once.py --bootstrap-objects
```

Run continuously:

```bash
bash deploy/run_job.sh realtime-streaming
```

The job uses Spark's Kafka source and checkpoint directory for offset
management. `spark_streaming_kafka_to_kudu_once.py` remains a smoke/debug
entrypoint only.

Server deployment can enable the optional systemd unit:

```text
REALTIME_STREAMING_ENABLED=true
```

Then restart through `deploy/server/control.sh`.

Stop:

```bash
docker compose -f docker/docker-compose.kudu.yml down
```

## Query Through Impala

Impala shell:

```bash
docker exec -it cdc-impala impala-shell --protocol=hs2 -i 127.0.0.1:21050
```

Example SQL:

```sql
show databases;
use realtime;
show tables;
select * from v_realtime_comment_analysis limit 20;
```
