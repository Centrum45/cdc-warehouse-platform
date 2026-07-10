# Realtime Kudu / Impala

The realtime path consumes Maxwell binlog events and writes latest-row state to Kudu through Impala SQL.

```text
Kafka / JSONL binlog
  -> streaming/realtime_sink/kafka_to_kudu.py
  -> Impala UPSERT/DELETE
  -> Kudu tables
  -> Impala realtime views
```

## Local Simulation

No Kudu/Impala needed:

```bash
python3 streaming/realtime_sink/kafka_to_kudu.py \
  data/kafka/cdc.incremental.binlog.jsonl \
  data/kudu \
  data/checkpoints/realtime_sink.json
```

Equivalent explicit engine:

```bash
REALTIME_ENGINE=local_csv python3 streaming/realtime_sink/kafka_to_kudu.py
```

Output:

```text
data/kudu/realtime.avatar_commentbatchsource.csv
```

## Real Cluster Requirements

Install Python client dependencies:

```bash
pip install impyla thrift-sasl
```

Set environment:

```bash
export IMPALA_HOST=impala.example.com
export IMPALA_PORT=21050
export IMPALA_USER=cdc_user
export IMPALA_PASSWORD='your_password'
export IMPALA_AUTH_MECHANISM=PLAIN
export KUDU_MASTERS=kudu-master-1.example.com:7051,kudu-master-2.example.com:7051
export USE_REAL_KUDU=true
export REALTIME_ENGINE=kudu_impala
```

Auth variables are optional. Use what your Impala cluster requires.

## Initialize Kudu Tables And Views

Preview SQL:

```bash
python3 scripts/run_realtime_kudu_smoke.py --dry-run
```

Execute against real Impala:

```bash
python3 -m realtime.impala.bootstrap
```

This creates:

```text
realtime.avatar_commentbatchsource
realtime.order_info
realtime.user_info
realtime.v_realtime_comment_analysis
realtime.v_realtime_trade_analysis
realtime.v_realtime_user_analysis
```

## Run Realtime Sink

```bash
python3 scripts/run_realtime_kudu_smoke.py --real \
  --engine kudu_impala \
  --topic-file data/kafka/cdc.incremental.binlog.jsonl \
  --checkpoint data/checkpoints/realtime_sink_real.json
```

The script:

- initializes realtime Kudu tables/views
- upserts/deletes rows from binlog events
- queries `realtime.v_realtime_comment_analysis`

## Impala Query

```python
from realtime.impala.query import ImpalaQuery

query = ImpalaQuery()
print(query.run_view("realtime", "v_realtime_comment_analysis"))
query.close()
```

## Notes

- Kudu writes use Impala `UPSERT INTO` and `DELETE`.
- Delete binlog events delete by primary key.
- Local CSV mode remains default for developer machines.
- Real mode fails fast if Impala/Kudu write fails.
